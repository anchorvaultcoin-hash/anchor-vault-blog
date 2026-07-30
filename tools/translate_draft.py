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

LANG_NAMES = {"en": "English", "ru": "Russian", "zh": "Simplified Chinese"}

SYSTEM_PROMPT = """Translate the following text into {target_lang}.
Preserve Markdown formatting (## headings, **bold**, paragraph breaks).
Keep a calm, direct, non-marketing tone. Adapt idioms naturally.
Output ONLY the translated text, nothing else — no notes, no original text, no labels like "Translation:"."""


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


def call_deepseek(text, target_lang_name):
    if not API_KEY:
        print("ОШИБКА: DEEPSEEK_API_KEY не найден в .env")
        sys.exit(1)

    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.format(target_lang=target_lang_name)},
                {"role": "user", "content": text},
            ],
            "temperature": 0.3,
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
    new_title = clean(call_deepseek(meta.get("title", ""), target_lang_name))

    print(f"Перевожу описание на {target_lang_name}...")
    new_desc = clean(call_deepseek(meta.get("description", ""), target_lang_name))

    print(f"Перевожу текст статьи на {target_lang_name} (это может занять минуту)...")
    new_body = call_deepseek(body, target_lang_name)

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
