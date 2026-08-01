"""
Переводит статью на EN и ZH через DeepSeek и СРАЗУ публикует — без черновиков.

Использование:
    python3 tools/publish_all.py docs/posts/<файл-статьи-на-русском>.md

Делает всё за один запуск:
  1. Переводит статью на английский и китайский через DeepSeek API.
  2. Сохраняет оба перевода как обычные статьи (сразу в сборку, без draft-).
  3. Запускает blog_build.py — пересобирает весь сайт.
  4. Коммитит и пушит на GitHub.

Нужен:  pip install requests python-dotenv
Ключ:   .env файл в корне репо, строка DEEPSEEK_API_KEY=...
"""
import os
import re
import subprocess
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

LANG_NAMES = {"en": "English", "zh": "Simplified Chinese", "ru": "Russian"}

# Раздельные промпты — китайский и английский тексты живут по разным правилам.
# Один общий промпт «переведи в target_lang» даёт правильный, но сухой,
# дословно-калькированный результат: годится для фактов, плохо для живого текста.
# Синхронизировано с tools/translate_draft.py — держать оба файла одинаковыми.

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
    return resp.json()["choices"][0]["message"]["content"].strip()


def slugify(name):
    return re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))


def clean(text):
    return text.lstrip("#").strip().strip('"').strip()


def translate_and_save(src_path, meta, body, target_lang, group):
    target_lang_name = LANG_NAMES[target_lang]
    print(f"[{target_lang}] перевожу заголовок...")
    new_title = clean(call_deepseek(meta.get("title", ""), target_lang))
    print(f"[{target_lang}] перевожу описание...")
    new_desc = clean(call_deepseek(meta.get("description", ""), target_lang))
    print(f"[{target_lang}] перевожу текст статьи...")
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
    out_path = os.path.join(out_dir, f"{group}-{target_lang}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(front_matter + new_body + "\n")
    print(f"[{target_lang}] сохранено: {out_path}")
    return out_path


def main():
    if len(sys.argv) != 2:
        print("Использование: python3 tools/publish_all.py <путь-к-статье.md>")
        sys.exit(1)

    src_path = sys.argv[1]
    with open(src_path, encoding="utf-8") as f:
        raw = f.read()
    meta, body = read_front_matter(raw)

    src_lang = meta.get("lang", "ru")
    group = meta.get("group") or slugify(os.path.splitext(os.path.basename(src_path))[0])

    if not meta.get("group"):
        print(f"ВНИМАНИЕ: в исходной статье нет поля 'group', использую '{group}'.")
        print("Добавь 'group:' в front matter исходника вручную, если нужно точное имя.")

    targets = [lang for lang in LANG_NAMES if lang != src_lang]
    for lang in targets:
        translate_and_save(src_path, meta, body, lang, group)

    print("\nПересобираю сайт...")
    subprocess.run(["python3", "tools/blog_build.py"], cwd=ROOT, check=True)

    print("Коммичу и пушу...")
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", f"feat: auto-translate and publish '{group}' (en/zh)"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)

    print("\nГотово. Статья переведена, собрана и опубликована на всех языках.")


if __name__ == "__main__":
    main()
