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

LANG_NAMES = {"en": "English", "zh": "Simplified Chinese", "ru": "Russian"}

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
    return resp.json()["choices"][0]["message"]["content"].strip()


def slugify(name):
    return re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))


def clean(text):
    return text.lstrip("#").strip().strip('"').strip()


def translate_and_save(src_path, meta, body, target_lang, group):
    target_lang_name = LANG_NAMES[target_lang]
    print(f"[{target_lang}] перевожу заголовок...")
    new_title = clean(call_deepseek(meta.get("title", ""), target_lang_name))
    print(f"[{target_lang}] перевожу описание...")
    new_desc = clean(call_deepseek(meta.get("description", ""), target_lang_name))
    print(f"[{target_lang}] перевожу текст статьи...")
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
