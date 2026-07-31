"""
Локальная админка блога AnchorVaultCoin.

Запуск:
    cd ~/anchor-vault-blog
    python3 tools/admin.py

Откроется вкладка в браузере. Вставляешь текст статьи, цепляешь картинку,
жмёшь «Опубликовать» — дальше всё само:
  1. Сжимает и сохраняет картинку в docs/img/
  2. Создаёт русскую статью в docs/posts/
  3. Переводит на английский и китайский через DeepSeek
  4. Пересобирает сайт (blog_build.py)
  5. Коммитит и пушит на GitHub

Работает ТОЛЬКО на твоей машине (127.0.0.1). Ключ DeepSeek берётся из .env
и наружу никуда не уходит.

Нужен:  pip install requests python-dotenv pillow
"""
import base64
import json
import os
import re
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO

import requests
from dotenv import load_dotenv

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "docs", "posts")
IMG_DIR = os.path.join(ROOT, "docs", "img")
BLOG_URL = "https://anchorvaultcoin-hash.github.io/anchor-vault-blog"

load_dotenv(os.path.join(ROOT, ".env"), override=True)
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

PORT = 8765
LANGS = {"en": "English", "zh": "Simplified Chinese"}

SYSTEM_PROMPT = """Translate the following text into {target_lang}.
Preserve Markdown formatting (## headings, **bold**, paragraph breaks).
Keep a calm, direct, non-marketing tone. Adapt idioms naturally.
Output ONLY the translated text, nothing else — no notes, no original text, no labels."""

# Сессия с trust_env=False: игнорирует системный SOCKS-прокси,
# который на этой машине ломает запросы к API.
SESSION = requests.Session()
SESSION.trust_env = False


PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Админка блога — AnchorVaultCoin</title>
<style>
:root{
  --bg:#0b0d11; --bg2:#181e2c; --bg3:#0f1318;
  --gold:#d4a843; --accent2:#fdba74;
  --text:#e2e8f0; --text2:#94a3b8; --text3:#7c8aa0; --border:#2a3347;
  --ok:#4ade80; --err:#f87171;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--bg); color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  line-height:1.6; padding:0 20px 60px;
}
.wrap{max-width:760px; margin:0 auto}
h1{font-size:24px; margin:32px 0 4px; letter-spacing:-.4px}
h1 span{color:var(--gold)}
.sub{color:var(--text3); font-size:14px; margin:0 0 28px}
label{display:block; margin:20px 0 6px; font-size:14px; color:var(--text2)}
label b{color:var(--gold); font-weight:500}
input[type=text], textarea{
  width:100%; background:var(--bg3); color:var(--text);
  border:1px solid var(--border); border-radius:9px;
  padding:11px 13px; font-size:15px; font-family:inherit; line-height:1.6;
}
input[type=text]:focus, textarea:focus{outline:none; border-color:var(--gold)}
textarea{resize:vertical; min-height:340px}
.hint{color:var(--text3); font-size:12.5px; margin-top:5px}
.row{display:flex; gap:14px; flex-wrap:wrap}
.row > div{flex:1; min-width:220px}
input[type=file]{
  width:100%; background:var(--bg3); color:var(--text2);
  border:1px dashed var(--border); border-radius:9px;
  padding:11px 13px; font-size:14px; cursor:pointer;
}
#preview{
  display:none; max-width:260px; margin-top:12px;
  border:1px solid var(--border); border-radius:10px;
}
.chk{display:flex; align-items:center; gap:9px; margin:22px 0 0; color:var(--text2); font-size:14px}
.chk input{width:16px; height:16px; accent-color:var(--gold)}
button{
  margin-top:26px; width:100%; padding:14px;
  background:var(--gold); color:#0b0d11; border:none; border-radius:10px;
  font-size:16px; font-weight:600; cursor:pointer; transition:opacity .2s;
}
button:hover{opacity:.88}
button:disabled{opacity:.4; cursor:not-allowed}
#log{
  display:none; margin-top:24px; padding:16px 18px;
  background:var(--bg3); border:1px solid var(--border); border-radius:10px;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:13px; line-height:1.85; white-space:pre-wrap; color:var(--text2);
}
#log .ok{color:var(--ok)}
#log .err{color:var(--err)}
.spin{
  display:inline-block; width:13px; height:13px; margin-right:8px;
  border:2px solid var(--border); border-top-color:var(--gold);
  border-radius:50%; animation:s .7s linear infinite; vertical-align:-2px;
}
@keyframes s{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="wrap">
  <h1>Админка <span>блога</span></h1>
  <p class="sub">Вставь текст на русском — переведётся на английский и китайский, соберётся и уйдёт на сайт.</p>

  <label><b>Заголовок</b> — под то, что люди ищут в поиске</label>
  <input type="text" id="title" placeholder="Украли сид-фразу: что происходит дальше">

  <label><b>Описание</b> — одно предложение для поисковой выдачи, до 160 символов</label>
  <input type="text" id="desc" placeholder="Честный разбор без паники — что реально произойдёт и почему поддержка не поможет">
  <div class="hint" id="desclen">0 символов</div>

  <label>Адрес страницы (латиницей). Оставь пустым — сделаю сам из заголовка</label>
  <input type="text" id="slug" placeholder="ukrali-seed-frazu">

  <div class="row">
    <div>
      <label>Картинка к статье (необязательно)</label>
      <input type="file" id="img" accept="image/*">
      <img id="preview" alt="">
    </div>
    <div>
      <label>Подпись под картинкой</label>
      <input type="text" id="caption" placeholder="Так выглядит поддельное окно подтверждения">
      <div class="hint">Картинка встанет после первого абзаца. Сожму сама, если тяжёлая.</div>
    </div>
  </div>

  <label><b>Текст статьи</b> — обычный текст. Заголовки внутри — через ##, важное — **жирным**</label>
  <textarea id="body" placeholder="Если вы читаете это в панике — пролистайте сразу к разделу «Что делать прямо сейчас».

## Что произойдёт в ближайшие минуты

Секретная фраза — это не пароль..."></textarea>

  <label class="chk"><input type="checkbox" id="push" checked> Сразу опубликовать на сайт (git push)</label>

  <button id="go">Опубликовать</button>
  <div id="log"></div>
</div>

<script>
const $ = id => document.getElementById(id);
let imgData = null, imgName = null;

$('desc').addEventListener('input', e => {
  const n = e.target.value.length;
  $('desclen').textContent = n + ' символов' + (n > 160 ? ' — длинновато, поиск обрежет' : '');
  $('desclen').style.color = n > 160 ? '#f87171' : '';
});

$('img').addEventListener('change', e => {
  const f = e.target.files[0];
  if (!f) { imgData = null; $('preview').style.display = 'none'; return; }
  imgName = f.name;
  const r = new FileReader();
  r.onload = () => {
    imgData = r.result.split(',')[1];
    $('preview').src = r.result;
    $('preview').style.display = 'block';
  };
  r.readAsDataURL(f);
});

$('go').addEventListener('click', async () => {
  const title = $('title').value.trim();
  const body = $('body').value.trim();
  if (!title || !body) { alert('Нужен хотя бы заголовок и текст.'); return; }

  $('go').disabled = true;
  $('log').style.display = 'block';
  $('log').innerHTML = '<span class="spin"></span>Работаю. Перевод занимает около минуты — не закрывай вкладку.';

  try {
    const res = await fetch('/publish', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        title: title,
        desc: $('desc').value.trim(),
        slug: $('slug').value.trim(),
        caption: $('caption').value.trim(),
        body: body,
        push: $('push').checked,
        img: imgData,
        img_name: imgName
      })
    });
    const data = await res.json();
    $('log').innerHTML = data.log.join('\\n') +
      (data.ok ? '\\n\\n<span class="ok">Готово.</span>'
               : '\\n\\n<span class="err">Оборвалось. Смотри ошибку выше.</span>');
    if (data.ok) {
      $('title').value = ''; $('desc').value = ''; $('slug').value = '';
      $('caption').value = ''; $('body').value = ''; $('img').value = '';
      $('preview').style.display = 'none'; imgData = null;
      $('desclen').textContent = '0 символов';
    }
  } catch (err) {
    $('log').innerHTML = '<span class="err">Сервер не ответил: ' + err + '</span>';
  }
  $('go').disabled = false;
});
</script>
</body>
</html>
"""


def slugify(name, limit=50):
    """Латиница через дефис. Режет по целым словам, не посреди слова."""
    s = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))).strip("-")
    if len(s) <= limit:
        return s
    cut = s[:limit].rsplit("-", 1)[0]
    return cut.strip("-") or s[:limit].strip("-")


def translit(text):
    """Грубая транслитерация кириллицы — чтобы получить адрес страницы из русского заголовка."""
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    return "".join(table.get(ch, ch) for ch in text.lower())


def call_deepseek(text, target_lang_name):
    if not text.strip():
        return ""
    resp = SESSION.post(
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
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def clean(text):
    return text.lstrip("#").strip().strip('"').strip()


def save_image(b64, orig_name, slug, log):
    """Сохраняет картинку, ужимая до 1200px по ширине."""
    os.makedirs(IMG_DIR, exist_ok=True)
    raw = base64.b64decode(b64)
    ext = os.path.splitext(orig_name or "")[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        ext = ".jpg"
    fname = f"{slug}{ext}"
    path = os.path.join(IMG_DIR, fname)

    if HAS_PIL and ext != ".gif":
        try:
            im = Image.open(BytesIO(raw))
            if im.width > 1200:
                im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
            has_alpha = im.mode in ("RGBA", "LA", "P")
            if ext in (".jpg", ".jpeg") or not has_alpha:
                # фото всегда в JPEG — PNG для фотографий весит в разы больше
                if ext not in (".jpg", ".jpeg"):
                    os.remove(path) if os.path.exists(path) else None
                    ext, fname = ".jpg", f"{slug}.jpg"
                    path = os.path.join(IMG_DIR, fname)
                im.convert("RGB").save(path, quality=85, optimize=True)
            else:
                im.save(path, optimize=True)
            log.append(f"  картинка: {fname}, {os.path.getsize(path) // 1024} КБ")
            return fname
        except Exception as e:
            log.append(f"  сжать не вышло ({e}), сохраняю как есть")

    with open(path, "wb") as f:
        f.write(raw)
    log.append(f"  картинка: {fname}, {os.path.getsize(path) // 1024} КБ")
    return fname


def insert_image(body, img_md):
    """Ставит картинку после первого абзаца."""
    if not img_md:
        return body
    parts = body.split("\n\n")
    if len(parts) >= 2:
        return "\n\n".join([parts[0], img_md] + parts[1:])
    return body + "\n\n" + img_md


def write_post(slug, group, lang, title, desc, date, body, img_md):
    front = (f"---\ntitle: {title}\ndescription: {desc}\ndate: {date}\n"
             f"lang: {lang}\nslug: {slug}\ngroup: {group}\n---\n\n")
    name = f"{date}-{slug}.md" if lang == "ru" else f"{group}-{lang}.md"
    path = os.path.join(POSTS_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(front + insert_image(body, img_md) + "\n")
    return name


def publish(d, log):
    if not API_KEY:
        log.append("ОШИБКА: DEEPSEEK_API_KEY не найден в .env")
        return False

    os.makedirs(POSTS_DIR, exist_ok=True)
    title = d["title"]
    desc = d.get("desc", "")
    body = d["body"]
    date = datetime.now().strftime("%Y-%m-%d")

    slug = slugify(d.get("slug") or translit(title)) or "post"
    group = slug
    log.append(f"Адрес страницы: {slug}.html")

    img_md = ""
    img_caption = d.get("caption", "").strip()
    if d.get("img"):
        fname = save_image(d["img"], d.get("img_name"), slug, log)
        img_md = f"![{img_caption or title}]({BLOG_URL}/img/{fname})"
        if img_caption:
            img_md += f"\n*{img_caption}*"

    name = write_post(slug, group, "ru", title, desc, date, body, img_md)
    log.append(f"[ru] сохранено: {name}")

    for lang, lang_name in LANGS.items():
        try:
            log.append(f"[{lang}] перевожу заголовок...")
            t = clean(call_deepseek(title, lang_name))
            log.append(f"[{lang}] перевожу описание...")
            ds = clean(call_deepseek(desc, lang_name))
            log.append(f"[{lang}] перевожу текст...")
            b = call_deepseek(body, lang_name)

            cap = clean(call_deepseek(img_caption, lang_name)) if img_caption else ""
            img_md_l = ""
            if d.get("img"):
                img_md_l = f"![{cap or t}]({BLOG_URL}/img/{slug}{os.path.splitext(d.get('img_name') or '.jpg')[1].lower() or '.jpg'})"
                if cap:
                    img_md_l += f"\n*{cap}*"

            # Адрес для перевода строим от группы: заголовок на китайском
            # даёт мусор, а английский — обрубки слов.
            lslug = f"{group}-{lang}"
            name = write_post(lslug, group, lang, t, ds, date, b, img_md_l)
            log.append(f"[{lang}] сохранено: {name}")
        except Exception as e:
            log.append(f"[{lang}] ОШИБКА перевода: {e}")
            return False

    log.append("Собираю сайт...")
    r = subprocess.run([sys.executable, "tools/blog_build.py"], cwd=ROOT,
                       capture_output=True, text=True)
    log.append(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        log.append("ОШИБКА сборки — на сайт ничего не ушло.")
        return False

    if not d.get("push"):
        log.append("Публикацию пропустил (галочка снята). Файлы на месте.")
        return True

    log.append("Коммичу и пушу...")
    for cmd in (["git", "add", "-A"],
                ["git", "commit", "-m", f"post: {slug}"],
                ["git", "push"]):
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            log.append(f"git {cmd[1]}: {(r.stderr or r.stdout).strip()}")
            if cmd[1] == "push":
                log.append("Пуш не прошёл. Попробуй в терминале: git pull --rebase && git push")
                return False

    log.append(f"Опубликовано: {BLOG_URL}/{slug}.html")
    return True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        body = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        log = []
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            ok = publish(data, log)
        except Exception as e:
            log.append(f"ОШИБКА: {e}")
            ok = False

        for line in log:
            print(line)
        out = json.dumps({"ok": ok, "log": log}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


def main():
    if not API_KEY:
        print("ВНИМАНИЕ: DEEPSEEK_API_KEY не найден в .env — перевод работать не будет.")
    if not HAS_PIL:
        print("ВНИМАНИЕ: Pillow не установлен — картинки не будут сжиматься.")
        print("Поставить: ALL_PROXY= all_proxy= pip install pillow --break-system-packages")

    url = f"http://127.0.0.1:{PORT}/"
    print(f"\nАдминка запущена: {url}")
    print("Остановить — Ctrl+C\n")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")


if __name__ == "__main__":
    main()
