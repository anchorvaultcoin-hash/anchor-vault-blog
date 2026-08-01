"""
Переводит статью блога на другие языки через DeepSeek API.
Результат сохраняется как ЧЕРНОВИК (с префиксом draft-), не публикуется автоматически.

Использование:
    python3 tools/translate_draft.py docs/posts/2026-07-30-ukrali-seed-frazu.md en
    python3 tools/translate_draft.py docs/posts/2026-07-30-ukrali-seed-frazu.md zh

Что делает:
  1. Читает исходную статью (front matter + текст).
  2. Переводит title, description и текст через DeepSeek API.
  3. Сохраняет как docs/posts/draft-<slug>-<lang>.md
  4. НЕ добавляет group/slug в основную сборку, пока ты вручную не проверишь
     черновик и не переименуешь файл (убрав "draft-" из имени).

Нужен:  pip install requests python-dotenv
Ключ:   .env файл в корне репо, строка DEEPSEEK_API_KEY=...
"""
import os
import re
import sys

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"), override=True)

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

# Сессия с trust_env=False: игнорирует системный SOCKS-прокси (тот же приём,
# что в tools/admin.py) — иначе запрос падает с "Missing dependencies for
# SOCKS support", если в системе включён ALL_PROXY=socks://...
SESSION = requests.Session()
SESSION.trust_env = False

LANG_NAMES = {"en": "English", "ru": "Russian", "zh": "Simplified Chinese"}

# Раздельные промпты — китайский и английский тексты живут по разным правилам.
# Один общий промпт «переведи в target_lang» даёт правильный, но сухой,
# дословно-калькированный результат: годится для фактов, плохо для живого текста.

_SHARED_RULES = """Preserve Markdown formatting exactly (## headings, **bold**, paragraph breaks,
list markers). Keep every fact, number, date, and proper name unchanged — do not add,
drop, or soften anything from the source. Do not translate: token tickers (USDC, USDT, ANCR),
company and project names (Humanity Protocol, Pantera Capital), and URLs.
Output ONLY the translated text — no notes, no original text, no labels like "Translation:"."""

SYSTEM_PROMPTS = {
    "zh": f"""You are a professional translator working from Russian/English into Simplified
Chinese (简体中文, mainland China audience — never Traditional Chinese), specializing in
crypto security and blockchain writing.

Translate for meaning, not word-for-word. Avoid "翻译腔" (translation-ese, calques from the
source language) — restructure sentences the way a native Chinese blog writer would, using
natural connectors and rhythm. Style: 公众号-style tech/security writing — direct, confident,
slightly punchy, short paragraphs. Headlines should be sharp, not descriptive.

Standard terminology (use consistently): multisig → 多签, vault → 金库, exploit/hack → 攻击/漏洞利用,
cold wallet → 冷钱包, seed phrase → 助记词, non-custodial → 非托管.

A native Chinese reader should not be able to tell this is a translation.

{_SHARED_RULES}""",

    "en": f"""You are a professional translator working from Russian into English, specializing
in crypto security and technical/blog writing for an international audience.

Translate for meaning, not word-for-word. Russian sentences are often longer and more
formal than natural English — break them up, cut filler, and use the plain, direct register
a native English blog writer would use. Avoid stiff constructions that read as translated
("it should be noted that", "the given"). Contractions are fine where they read naturally.
Keep the calm, matter-of-fact tone of the source — this is security writing, not marketing copy.

A native English reader should not be able to tell this is a translation.

{_SHARED_RULES}""",

    "ru": f"""You are a professional translator working into Russian, specializing in crypto
security and technical/blog writing.

Translate for meaning, not word-for-word. Use natural Russian sentence structure and
register — avoid calques from the source language. Keep the calm, direct, non-marketing tone.

{_SHARED_RULES}""",
}

# Дословный перевод (temperature низкая) звучит сухо и калькированно.
# Слишком высокая (>1.0) для текста про безопасность рискованна: модель может
# начать вольно интерпретировать формулировки там, где важна точная фраза.
# 0.8 — компромисс: достаточно свободы для живого текста, факты не плывут.
TRANSLATE_TEMPERATURE = 0.8


def read_front_matter(raw):
    meta, body = {}, raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            for line in raw[3:end].strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
            body = raw[end + 4:].lstrip("\n")
    return meta, body


def call_deepseek(text, target_lang):
    if not API_KEY:
        print("ОШИБКА: DEEPSEEK_API_KEY не найден в .env")
        sys.exit(1)

    resp = SESSION.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPTS[target_lang]},
                {"role": "user", "content": text},
            ],
            "temperature": TRANSLATE_TEMPERATURE,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def slugify(name):
    return re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))


def main():
    if len(sys.argv) != 3:
        print("Использование: python3 tools/translate_draft.py <путь-к-статье.md> <en|zh|ru>")
        sys.exit(1)

    src_path, target_lang = sys.argv[1], sys.argv[2]
    if target_lang not in LANG_NAMES:
        print(f"Неизвестный язык: {target_lang}. Доступны: {list(LANG_NAMES)}")
        sys.exit(1)

    with open(src_path, encoding="utf-8") as f:
        raw = f.read()
    meta, body = read_front_matter(raw)

    src_lang = meta.get("lang", "ru")
    if src_lang == target_lang:
        print("Язык исходника совпадает с целевым, перевод не нужен.")
        sys.exit(0)

    group = meta.get("group") or slugify(os.path.splitext(os.path.basename(src_path))[0])
    target_lang_name = LANG_NAMES[target_lang]

    def clean(text):
        # убираем случайную markdown-разметку, которую модель иногда добавляет к заголовкам
        return text.lstrip("#").strip().strip('"').strip()

    print(f"Перевожу заголовок на {target_lang_name}...")
    new_title = clean(call_deepseek(meta.get("title", ""), target_lang))

    print(f"Перевожу описание на {target_lang_name}...")
    new_desc = clean(call_deepseek(meta.get("description", ""), target_lang))

    print(f"Перевожу текст статьи на {target_lang_name} (это может занять минуту)...")
    new_body = call_deepseek(body, target_lang)

    latin_slug = slugify(new_title)[:60]
    new_slug = latin_slug if len(latin_slug) >= 3 else f"{group}-{target_lang}"

    front_matter = f"""---
title: {new_title}
description: {new_desc}
date: {meta.get('date', '')}
lang: {target_lang}
slug: {new_slug}
group: {group}
---

"""

    out_dir = os.path.dirname(src_path)
    out_path = os.path.join(out_dir, f"draft-{group}-{target_lang}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(front_matter + new_body + "\n")

    print(f"\nЧерновик сохранён: {out_path}")
    print("Проверь текст, при необходимости поправь.")
    print(f"Когда готов публиковать — переименуй файл, убрав 'draft-' из начала имени,")
    print("и запусти обычную сборку: python3 tools/blog_build.py")


if __name__ == "__main__":
    main()
