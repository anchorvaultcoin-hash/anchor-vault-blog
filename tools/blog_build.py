"""
Собирает блог из markdown-файлов.

Кладёшь статью в docs/blog/posts/*.md — получаешь готовую HTML-страницу
в стиле лендинга, обновлённый список статей, RSS-ленту и разметку для Google.

Запуск:  python3 tools/blog_build.py
Нужен:   pip install markdown
"""
import hashlib
import html
import json
import os
import re
import shutil
from datetime import datetime, timezone

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "docs", "posts")
OUT_DIR = os.path.join(ROOT, "docs")
# Блог живёт отдельным репозиторием, основной сайт — соседним
SITE_URL = "https://anchorvaultcoin-hash.github.io/anchor-vault-frontend"
BASE_URL = "https://anchorvaultcoin-hash.github.io/anchor-vault-blog"
BLOG_URL = BASE_URL


IC_X = ('<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true">'
        '<path d="M18.24 2.25h3.31l-7.23 8.26 8.5 11.24h-6.65l-5.21-6.82-5.97 6.82H1.68'
        'l7.73-8.84L1.25 2.25h6.83l4.71 6.23zm-1.16 17.52h1.83L7.08 4.13H5.11z"/></svg>')

IC_TG = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">'
         '<path d="M11.94 15.4l-.2 2.83c.29 0 .41-.12.56-.27l1.35-1.29 2.8 2.05c.51.29.88.14'
         '1.02-.47l1.85-8.67c.17-.76-.28-1.06-.78-.88L4.4 13.1c-.75.29-.74.71-.13.9l3.5 1.09'
         '8.12-5.11c.38-.25.73-.11.44.14z"/></svg>')

COUNTER_JS = """<script>
fetch('https://abacus.jasoncameron.dev/hit/anchor-vault-blog/visits')
  .then(function(r){ return r.json(); })
  .then(function(d){
    document.getElementById('vcn').textContent = d.value.toLocaleString();
    document.getElementById('vc').style.display = 'inline-block';
  })
  .catch(function(){});
</script>"""

# Реакции на посты: общий счётчик через тот же Abacus, что и просмотры.
# GET /get — читает без инкремента (для загрузки текущих цифр).
# GET /hit — увеличивает на 1 (для клика). localStorage не даёт накрутить
# один эмодзи с одного браузера больше одного раза — не защита от накрутки
# вообще, но от случайного повторного клика бережёт.
# Abacus принимает в ключах только [A-Za-z0-9_\-.] — эмодзи туда положить нельзя
# (сервер вернёт "Invalid key"). Поэтому у каждой реакции два значения:
# сам эмодзи (для показа) и латинский код (для ключа счётчика).
REACTION_EMOJI = [("🔥", "fire"), ("👍", "like"), ("🤯", "mind")]


def reaction_key(slug):
    """Короткий стабильный идентификатор поста для ключа счётчика.

    Abacus ограничивает ключ 64 символами, а slug переведённых статей бывает
    длиной 60+ ("multisig-didnt-save-them-how-36-million-leaked-from-a-single").
    Ключ вида reactions-<slug>-fire вылезал за лимит, и сервер отклонял запрос.
    Хеш даёт фиксированные 16 символов независимо от длины заголовка.
    """
    return hashlib.md5(slug.encode("utf-8")).hexdigest()[:16]

REACTIONS_JS = """<script>
(function(){
  var NS = 'anchor-vault-blog';
  var EMOJI = """ + json.dumps(REACTION_EMOJI, ensure_ascii=False) + """; // [[emoji, code], ...]

  function keyFor(rkey, code){ return 'r-' + rkey + '-' + code; }
  function votedKey(rkey, code){ return 'reacted:' + rkey + ':' + code; }

  function renderCount(el, value){
    el.textContent = (value || 0).toLocaleString();
  }

  function loadCounts(root){
    var rkey = root.getAttribute('data-rkey');
    root.querySelectorAll('.reaction-btn').forEach(function(btn){
      var code = btn.getAttribute('data-code');
      fetch('https://abacus.jasoncameron.dev/get/' + NS + '/' + keyFor(rkey, code))
        .then(function(r){ return r.ok ? r.json() : null; })
        .then(function(d){
          // Счётчика может не быть вовсе (никто не голосовал) — это 404 и нормальный 0.
          // А вот при 429/500 значение неизвестно, и затирать его нулём нельзя.
          if (d && typeof d.value === 'number') {
            renderCount(btn.querySelector('.reaction-count'), d.value);
          }
        })
        .catch(function(){});
      if (localStorage.getItem(votedKey(rkey, code))) btn.classList.add('voted');
    });
  }

  function vote(root, btn){
    var rkey = root.getAttribute('data-rkey');
    var code = btn.getAttribute('data-code');
    if (localStorage.getItem(votedKey(rkey, code))) return; // уже жал эту реакцию
    localStorage.setItem(votedKey(rkey, code), '1');
    btn.classList.add('voted');

    function rollback(){
      btn.classList.remove('voted');
      localStorage.removeItem(votedKey(rkey, code));
    }

    fetch('https://abacus.jasoncameron.dev/hit/' + NS + '/' + keyFor(rkey, code))
      .then(function(r){
        // 429 (лимит 30 запросов/10 сек) отдаёт валидный JSON с ошибкой,
        // поэтому одного .catch мало — проверяем статус явно.
        if (!r.ok) throw new Error('http ' + r.status);
        return r.json();
      })
      .then(function(d){
        if (typeof d.value !== 'number') throw new Error('no value');
        renderCount(btn.querySelector('.reaction-count'), d.value);
      })
      .catch(rollback);
  }

  document.querySelectorAll('.reactions').forEach(function(root){
    loadCounts(root);
    root.querySelectorAll('.reaction-btn').forEach(function(btn){
      btn.addEventListener('click', function(){ vote(root, btn); });
    });
  });

  // Виджет на карточках главной. Только чтение, без кликов.
  //
  // ВАЖНО: у Abacus лимит 30 запросов с IP за 10 секунд. На главной может быть
  // 18+ постов x 3 реакции = 54+ запроса. Если слать их разом, часть отвалится
  // и счётчики покажут нули. Поэтому: сначала берём из кэша (мгновенно),
  // затем догружаем очередью по одному запросу раз в 350 мс.
  var CACHE_TTL = 5 * 60 * 1000; // 5 минут
  var queue = [];
  var queueRunning = false;

  function cacheGet(key){
    try {
      var raw = localStorage.getItem('rc:' + key);
      if (!raw) return null;
      var obj = JSON.parse(raw);
      if (Date.now() - obj.t > CACHE_TTL) return null;
      return obj.v;
    } catch(e){ return null; }
  }

  function cacheSet(key, value){
    try { localStorage.setItem('rc:' + key, JSON.stringify({v: value, t: Date.now()})); } catch(e){}
  }

  function runQueue(){
    if (queueRunning || queue.length === 0) return;
    queueRunning = true;
    var job = queue.shift();
    fetch('https://abacus.jasoncameron.dev/get/' + NS + '/' + job.key)
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(d){
        if (d && typeof d.value === 'number'){
          cacheSet(job.key, d.value);
          job.span.textContent = job.emoji + ' ' + d.value;
        }
      })
      .catch(function(){})
      .then(function(){
        queueRunning = false;
        setTimeout(runQueue, 350); // ~3 запроса/сек, с запасом под лимит
      });
  }

  document.querySelectorAll('.reactions-mini').forEach(function(mini){
    var rkey = mini.getAttribute('data-rkey');
    EMOJI.forEach(function(pair){
      var emoji = pair[0], code = pair[1];
      var key = keyFor(rkey, code);
      var span = document.createElement('span');
      var cached = cacheGet(key);
      span.textContent = emoji + ' ' + (cached === null ? 0 : cached);
      mini.appendChild(span);
      queue.push({key: key, span: span, emoji: emoji});
    });
  });
  runQueue();
})();
</script>"""

SITE_NAME = "AnchorVaultCoin"
BLOG_TITLE = "Блог о безопасности криптовалюты"
BLOG_DESC = ("Разборы реальных краж, простые объяснения и практические советы "
             "о том, как не потерять свои монеты.")

CSS = """
:root{
  --bg:#0b0d11; --bg2:#181e2c; --bg3:#0f1318;
  --gold:#d4a843; --gold2:#b8911e;
  --accent:#f97316; --accent2:#fdba74;
  --text:#e2e8f0; --text2:#94a3b8; --text3:#7c8aa0;
  --border:#2a3347;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--bg); color:var(--text);
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  line-height:1.7; -webkit-font-smoothing:antialiased;
}
a{color:var(--gold); text-decoration:none}
a:hover{color:var(--accent2); text-decoration:underline}
.wrap{max-width:720px; margin:0 auto; padding:0 20px}
header.top{
  border-bottom:1px solid var(--border); background:var(--bg3);
  position:sticky; top:0; z-index:10; backdrop-filter:blur(8px);
}
header.top .wrap{display:flex; align-items:center; justify-content:space-between; height:60px}
.brand{font-weight:700; font-size:17px; color:var(--text); letter-spacing:-.2px}
.brand span{color:var(--gold)}
.nav a{color:var(--text2); font-size:14px; margin-left:20px}
.nav a:hover{color:var(--gold); text-decoration:none}
.nav .soc{display:inline-flex; align-items:center; gap:6px}
.nav .soc svg{opacity:.85}
@media(max-width:560px){.nav .soc span{display:none} .nav .soc{margin-left:16px}}
main{padding:48px 0 72px}
h1{font-size:34px; line-height:1.25; margin:0 0 14px; letter-spacing:-.6px}
h2{font-size:23px; margin:38px 0 12px; letter-spacing:-.3px}
h3{font-size:19px; margin:30px 0 10px; color:var(--gold)}
p{margin:0 0 18px; color:var(--text)}
ul,ol{margin:0 0 18px; padding-left:22px}
li{margin-bottom:8px}
blockquote{
  margin:24px 0; padding:14px 20px; border-left:3px solid var(--gold);
  background:var(--bg2); border-radius:0 8px 8px 0; color:var(--text2);
}
blockquote p:last-child{margin-bottom:0}
code{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:13.5px;
  background:var(--bg2); padding:2px 6px; border-radius:4px; color:var(--accent2);
}
pre{background:var(--bg2); padding:16px; border-radius:8px; overflow-x:auto; border:1px solid var(--border)}
pre code{background:none; padding:0; color:var(--text)}
hr{border:none; border-top:1px solid var(--border); margin:36px 0}
.meta{color:var(--text3); font-size:14px; margin-bottom:34px}
.lead{font-size:18px; color:var(--text2); margin-bottom:30px}
.card{
  display:flex; gap:18px; align-items:flex-start;
  padding:22px; margin-bottom:16px; border:1px solid var(--border);
  border-radius:12px; background:var(--bg3); transition:border-color .2s, transform .2s;
}
.card-body{flex:1; min-width:0}
.card-thumb{
  width:104px; height:104px; flex-shrink:0; object-fit:cover;
  border-radius:10px; border:1px solid var(--border); background:var(--bg2);
}
@media(max-width:600px){
  .card{gap:13px; padding:18px}
  .card-thumb{width:74px; height:74px}
}
.card:hover{border-color:var(--gold2); text-decoration:none; transform:translateY(-2px)}
.card h2{margin:0 0 8px; font-size:20px; color:var(--text)}
.card p{color:var(--text2); margin:0 0 10px; font-size:15px}
.card .meta{margin:0; font-size:13px}
footer.bottom{border-top:1px solid var(--border); padding:28px 0; color:var(--text3); font-size:14px}
footer.bottom .wrap{display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px}
.soc-row{display:flex; gap:10px; flex-wrap:wrap}
#vc{
  display:none; margin-left:12px; padding:2px 10px;
  background:#fff; color:#0b0d11; border-radius:20px;
  font-size:12.5px; font-weight:600; vertical-align:1px;
}
.soc-btn{
  display:inline-flex; align-items:center; gap:8px; padding:9px 16px;
  border:1px solid var(--border); border-radius:9px; background:var(--bg2);
  color:var(--text); font-size:14px; font-weight:500; transition:all .2s;
}
.soc-btn:hover{border-color:var(--gold); color:var(--gold); text-decoration:none; background:var(--bg3)}
.soc-btn svg{opacity:.9}
.back{display:inline-block; margin-bottom:28px; font-size:14px; color:var(--text2)}
.share{display:flex; gap:8px; flex-wrap:wrap; margin:34px 0}
.share-btn{
  display:inline-flex; align-items:center; gap:7px; padding:8px 14px;
  border:1px solid var(--border); border-radius:9px; background:var(--bg3);
  color:var(--text2); font-size:13.5px; transition:.2s; cursor:pointer;
  font-family:inherit;
}
.share-btn:hover{border-color:var(--gold); color:var(--gold); text-decoration:none}
.share-btn svg{opacity:.85}
.reactions{display:flex; gap:8px; flex-wrap:wrap; margin:18px 0 0 0}
.reaction-btn{
  display:inline-flex; align-items:center; gap:6px; padding:7px 13px;
  border:1px solid var(--border); border-radius:20px; background:var(--bg3);
  color:var(--text2); font-size:14px; transition:.2s; cursor:pointer;
  font-family:inherit;
}
.reaction-btn:hover{border-color:var(--gold); background:var(--bg2)}
.reaction-btn.voted{border-color:var(--gold); background:rgba(212,175,55,.12); color:var(--gold)}
.reaction-count{font-size:12.5px; color:var(--text2); min-width:8px}
.reaction-btn.voted .reaction-count{color:var(--gold)}
.card .pin{font-size:15px; opacity:.9}
.card .reactions-mini{
  display:flex; gap:10px; margin-top:8px; font-size:12.5px; color:var(--text2);
}
main img{
  display:block; max-width:100%; height:auto; margin:30px auto 8px;
  border:1px solid var(--border); border-radius:12px; background:var(--bg2);
  box-shadow:0 6px 24px rgba(0,0,0,.4);
}
main img + em{
  display:block; margin:0 0 30px; text-align:center;
  color:var(--text3); font-size:13.5px; font-style:normal; line-height:1.5;
}
main figure{margin:30px 0}
main figure img{margin:0 auto 8px}
main figcaption{
  text-align:center; color:var(--text3); font-size:13.5px; line-height:1.5;
}
@media(max-width:600px){
  main img{border-radius:9px; margin:22px auto 8px}
}
@media(max-width:600px){
  h1{font-size:27px} main{padding:32px 0 52px}
  .nav a{margin-left:14px; font-size:13px}
}
"""


def read_front_matter(raw):
    """Разбирает блок --- ... --- в начале файла."""
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


def slugify(name):
    return re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))


SHARE_LABELS = {
    "ru": {"copy": "Скопировать ссылку", "copied": "Скопировано"},
    "en": {"copy": "Copy link", "copied": "Copied"},
    "zh": {"copy": "复制链接", "copied": "已复制"},
}
UI = {
    "ru": {"blog": "Блог", "about": "О сервисе", "back": "← Все статьи", "guide": "Как пользоваться"},
    "en": {"blog": "Blog", "about": "About", "back": "← All articles", "guide": "How it works"},
    "zh": {"blog": "博客", "about": "关于我们", "back": "← 所有文章", "guide": "使用指南"},
}

# Статья-гайд "как пользоваться" — по одной на каждый язык, все три уже
# переведены и опубликованы (kak-polzovatsya-kriptoseyfom-3-adresa-i-tri*.md)
GUIDE_SLUG = {
    "ru": "kak-polzovatsya-kriptoseyfom-3-adresa-i-tri",
    "en": "kak-polzovatsya-kriptoseyfom-3-adresa-i-tri-en",
    "zh": "kak-polzovatsya-kriptoseyfom-3-adresa-i-tri-zh",
}


def page(title, description, canonical, body, lang="ru", jsonld="", lang_switch="", hreflang_tags=""):
    ui = UI.get(lang, UI["ru"])
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{canonical}">
{hreflang_tags}
<meta name="yandex-verification" content="c44efc0436415d5b">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@Anchorvaultcoin">
<link rel="icon" href="{SITE_URL}/favicon.png">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{BLOG_URL}/rss.xml">
<style>{CSS}</style>
{jsonld}
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="{SITE_URL}/landing.html" style="display:flex;align-items:center;gap:8px">
    <img src="{BLOG_URL}/favicon.png" alt="" width="28" height="28" style="border-radius:50%">
    Anchor<span>Vault</span>Coin
  </a>
  <nav class="nav">
    <a href="{BLOG_URL}/">{ui["blog"]}</a>
    <a href="{SITE_URL}/landing.html">{ui["about"]}</a>
    <a href="{BLOG_URL}/{GUIDE_SLUG.get(lang, GUIDE_SLUG['ru'])}.html">{ui["guide"]}</a>
    <a class="soc" href="https://x.com/Anchorvaultcoin" aria-label="X">{IC_X}<span>X</span></a>
    <a class="soc" href="https://t.me/AnchorVaultCoin" aria-label="Telegram">{IC_TG}<span>Telegram</span></a>
    {lang_switch}
  </nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer class="bottom"><div class="wrap">
  <div>© {datetime.now().year} {SITE_NAME}<span id="vc"><span id="vcn"></span></span></div>
  <div class="soc-row">
    <a class="soc-btn" href="https://x.com/Anchorvaultcoin">{IC_X}<span>Читать в X</span></a>
    <a class="soc-btn" href="https://t.me/AnchorVaultCoin">{IC_TG}<span>Telegram-канал</span></a>
  </div>
</div></footer>
{COUNTER_JS}
{REACTIONS_JS}
</body>
</html>
"""


def main():
    if not os.path.isdir(POSTS_DIR):
        os.makedirs(POSTS_DIR, exist_ok=True)
        print(f"Создал папку {POSTS_DIR}. Положи туда .md файлы.")
        return

    # Полный список того, что умеет отдавать GitHub Pages как картинку.
    KNOWN_IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg", ".bmp", ".JPG", ".JPEG", ".PNG", ".WEBP", ".GIF")

    _img_dir_cache = None

    def _list_img_dir():
        nonlocal _img_dir_cache
        if _img_dir_cache is None:
            img_dir = os.path.join(OUT_DIR, "img")
            _img_dir_cache = os.listdir(img_dir) if os.path.isdir(img_dir) else []
        return _img_dir_cache

    def resolve_img_ext(path):
        """Возвращает путь к картинке с тем расширением, что реально лежит на диске.
        Всеяден: сначала пробует путь как есть, затем перебирает известные
        расширения по стему, затем ищет файл по стему без учёта регистра.
        Если ничего не найдено — путь не трогаем (лучше явная 404, чем тихая подмена)."""
        if not path.startswith(f"{BLOG_URL}/img/"):
            return path
        fname = path.rsplit("/", 1)[-1]
        stem = fname.rsplit(".", 1)[0]
        img_dir = os.path.join(OUT_DIR, "img")

        # 1) путь уже верный — самый частый случай, не трогаем его
        if os.path.isfile(os.path.join(img_dir, fname)):
            return path

        # 2) перебор известных расширений по тому же стему
        for ext in KNOWN_IMG_EXT:
            if os.path.isfile(os.path.join(img_dir, stem + ext)):
                return f"{BLOG_URL}/img/{stem}{ext}"

        # 3) регистронезависимый поиск по стему — на случай Stem.PNG vs stem.png
        stem_lower = stem.lower()
        for real_name in _list_img_dir():
            real_stem = real_name.rsplit(".", 1)[0]
            if real_stem.lower() == stem_lower:
                return f"{BLOG_URL}/img/{real_name}"

        return path

    def fix_image_ext(body):
        """Меняет расширение картинки в markdown на то, что реально лежит на диске."""
        def repl(m):
            alt, path = m.group(1), m.group(2)
            fixed = resolve_img_ext(path)
            return f"![{alt}]({fixed})" if fixed != path else m.group(0)
        return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, body)

    md = markdown.Markdown(extensions=["extra", "sane_lists", "smarty"])
    posts = []

    # первый проход: читаем метаданные всех статей, строим группы переводов
    raw_items = []
    for fn in sorted(os.listdir(POSTS_DIR)):
        if not fn.endswith(".md") or fn.startswith("draft-"):
            continue
        fpath = os.path.join(POSTS_DIR, fn)
        mtime = os.path.getmtime(fpath)
        with open(fpath, encoding="utf-8") as f:
            meta, body = read_front_matter(f.read())

        slug = meta.get("slug") or slugify(os.path.splitext(fn)[0])
        title = meta.get("title", slug)
        desc = meta.get("description", "")
        date = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
        lang = meta.get("lang", "ru")
        group = meta.get("group", "")
        pinned = str(meta.get("pinned", "")).strip().lower() in ("true", "yes", "1")
        m = re.search(r"!\[[^\]]*\]\(([^)]+)\)", body)
        raw_items.append({"slug": slug, "title": title, "desc": desc, "date": date,
                           "lang": lang, "group": group, "body": body, "mtime": mtime,
                           "pinned": pinned,
                           "img": resolve_img_ext(m.group(1)) if m else ""})

    LANG_NAMES = {"ru": "RU", "en": "EN", "zh": "ZH"}

    groups = {}
    for item in raw_items:
        if item["group"]:
            groups.setdefault(item["group"], {})[item["lang"]] = item["slug"]

    # Закрепление ставится в одном файле, а действовать должно на все языки:
    # если помечена русская версия, английская и китайская тоже идут наверх.
    pinned_groups = {it["group"] for it in raw_items if it["pinned"] and it["group"]}
    for item in raw_items:
        if item["group"] in pinned_groups:
            item["pinned"] = True

    for item in raw_items:
        slug, title, desc, date, lang = (item["slug"], item["title"], item["desc"],
                                          item["date"], item["lang"])
        body = item["body"]

        lang_switch = ""
        hreflang_tags = ""
        if item["group"] and item["group"] in groups and len(groups[item["group"]]) > 1:
            parts = []
            for l, s in sorted(groups[item["group"]].items()):
                label = LANG_NAMES.get(l, l.upper())
                if l == lang:
                    parts.append(f'<span style="color:var(--gold);font-weight:600">{label}</span>')
                else:
                    parts.append(f'<a href="{BLOG_URL}/{s}.html">{label}</a>')
            lang_switch = '<span class="soc" style="gap:8px">' + " · ".join(parts) + "</span>"

            # SEO: hreflang говорит Google/Яндексу, что это переводы одной статьи,
            # а не разноязычные дубли контента.
            hf_rows = [f'<link rel="alternate" hreflang="{l}" href="{BLOG_URL}/{s}.html">'
                       for l, s in sorted(groups[item["group"]].items())]
            default_lang, default_slug = sorted(groups[item["group"]].items())[0]
            hf_rows.append(f'<link rel="alternate" hreflang="x-default" href="{BLOG_URL}/{default_slug}.html">')
            hreflang_tags = "\n".join(hf_rows)

        body = fix_image_ext(body)
        md.reset()
        content = md.convert(body)
        url = f"{BLOG_URL}/{slug}.html"

        jsonld = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BlogPosting",
"headline":{html.escape(title)!r},
"description":{html.escape(desc)!r},
"datePublished":"{date}","inLanguage":"{lang}",
"mainEntityOfPage":{{"@type":"WebPage","@id":"{url}"}},
"image":"{SITE_URL}/og.png",
"author":{{"@type":"Organization","name":"{SITE_NAME}","url":"{SITE_URL}/landing.html"}},
"publisher":{{"@type":"Organization","name":"{SITE_NAME}",
"logo":{{"@type":"ImageObject","url":"{SITE_URL}/og.png"}}}}}}
</script>'''.replace("'", '"')

        from urllib.parse import quote
        share_url = quote(url, safe="")
        share_q = quote(f"{title} — {desc}" if desc else title, safe="")
        share_copy = SHARE_LABELS.get(lang, SHARE_LABELS["en"])["copy"]
        share_copied = SHARE_LABELS.get(lang, SHARE_LABELS["en"])["copied"]

        ui = UI.get(lang, UI["ru"])
        article = f'''<a class="back" href="{BLOG_URL}/">{ui["back"]}</a>
<h1>{html.escape(title)}</h1>
<div class="meta">{date}</div>
{content}

<div class="share">
  <a class="share-btn" href="https://twitter.com/intent/tweet?url={share_url}&text={share_q}" target="_blank" rel="noopener noreferrer">{IC_X} X</a>
  <a class="share-btn" href="https://t.me/share/url?url={share_url}&text={share_q}" target="_blank" rel="noopener noreferrer">{IC_TG} Telegram</a>
  <a class="share-btn" href="https://api.whatsapp.com/send?text={share_q}%20{share_url}" target="_blank" rel="noopener noreferrer">WhatsApp</a>
  <a class="share-btn" href="https://www.reddit.com/submit?url={share_url}&title={share_q}" target="_blank" rel="noopener noreferrer">Reddit</a>
  <button class="share-btn" onclick="navigator.clipboard.writeText('{url}');this.textContent='{share_copied}'" type="button">{share_copy}</button>
</div>

<div class="reactions" data-rkey="{reaction_key(slug)}">
{"".join(f'<button class="reaction-btn" data-code="{code}" type="button">{e}<span class="reaction-count">0</span></button>' for e, code in REACTION_EMOJI)}
</div>

<hr>
<p class="meta">AnchorVaultCoin — сервис хранения и переводов криптовалюты,
где каждая операция подтверждается двумя отдельными ключами.
<a href="{SITE_URL}/landing.html">Подробнее</a>.</p>'''

        with open(os.path.join(OUT_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(page(f"{title} — {SITE_NAME}", desc, url, article, lang, jsonld, lang_switch, hreflang_tags))

        posts.append({"slug": slug, "title": title, "desc": desc, "date": date,
                      "url": url, "lang": lang, "img": item["img"],
                      "mtime": item.get("mtime", 0), "pinned": item.get("pinned", False)})
        print(f"собрано: {slug}.html")

    # Дата в front matter одна на весь день, поэтому статьи, вышедшие в один
    # день, шли в алфавитном порядке и новая могла оказаться в середине списка.
    # Вторичный ключ — время изменения файла: свежая статья поднимается выше.
    posts.sort(key=lambda p: (p.get("pinned", False), p["date"], p.get("mtime", 0)), reverse=True)

    INDEX_I18N = {
        "en": {"title": "Crypto Security Blog",
               "desc": "Breakdowns of real thefts, plain-language explanations, "
                       "and practical advice on not losing your coins.",
               "empty": "Nothing here yet."},
        "ru": {"title": BLOG_TITLE, "desc": BLOG_DESC, "empty": "Пока пусто."},
        "zh": {"title": "加密货币安全博客",
               "desc": "真实盗窃案例分析、通俗易懂的讲解，以及避免资产被盗的实用建议。",
               "empty": "暂无内容。"},
    }
    LANG_PATH = {"en": "", "ru": "ru/", "zh": "zh/"}

    def build_index(lang):
        info = INDEX_I18N[lang]
        lang_posts = [pp for pp in posts if pp["lang"] == lang]
        def card(pp):
            thumb = (f'<img class="card-thumb" src="{pp["img"]}" alt="" loading="lazy">'
                     if pp.get("img") else "")
            pin = '<span class="pin">📌</span> ' if pp.get("pinned") else ""
            return (f'<a class="card" href="{pp["url"]}"><div class="card-body">'
                    f'<h2>{pin}{html.escape(pp["title"])}</h2>'
                    f'<p>{html.escape(pp["desc"])}</p>'
                    f'<div class="meta">{pp["date"]}</div>'
                    f'<div class="reactions-mini" data-rkey="{reaction_key(pp["slug"])}"></div>'
                    f'</div>{thumb}</a>')

        cards = "\n".join(card(pp) for pp in lang_posts) or f"<p>{info['empty']}</p>"

        parts = []
        for l, path in LANG_PATH.items():
            label = LANG_NAMES.get(l, l.upper())
            if l == lang:
                parts.append(f'<span style="color:var(--gold);font-weight:600">{label}</span>')
            else:
                parts.append(f'<a href="{BLOG_URL}/{path}">{label}</a>')
        lang_switch = '<span class="soc" style="gap:8px">' + " · ".join(parts) + "</span>"

        index_body = f'''<h1>{info["title"]}</h1>
<p class="lead">{info["desc"]}</p>
{cards}'''
        out_dir = OUT_DIR if not LANG_PATH[lang] else os.path.join(OUT_DIR, LANG_PATH[lang])
        os.makedirs(out_dir, exist_ok=True)
        canonical = f"{BLOG_URL}/{LANG_PATH[lang]}"
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page(f"{info['title']} — {SITE_NAME}", info["desc"], canonical,
                         index_body, lang, "", lang_switch))

    for lang in LANG_PATH:
        build_index(lang)

    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = "\n".join(f'''  <item>
    <title>{html.escape(p["title"])}</title>
    <link>{p["url"]}</link>
    <guid>{p["url"]}</guid>
    <description>{html.escape(p["desc"])}</description>
  </item>''' for p in posts)
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>{BLOG_TITLE} — {SITE_NAME}</title>
  <link>{BLOG_URL}/</link>
  <description>{BLOG_DESC}</description>
  <language>en</language>
  <lastBuildDate>{now}</lastBuildDate>
{items}
</channel></rss>'''
    with open(os.path.join(OUT_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss)

    # Карта сайта: сначала постоянные страницы (все языковые версии главной), потом статьи блога
    static_pages = [
        (f"{BLOG_URL}/{path}", "1.0", "weekly") for path in LANG_PATH.values()
    ]
    today = datetime.now().strftime("%Y-%m-%d")
    rows = [f"""  <url>
    <loc>{u}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{cf}</changefreq>
    <priority>{pr}</priority>
  </url>""" for u, pr, cf in static_pages]

    for p in posts:
        rows.append(f"""  <url>
    <loc>{p['url']}</loc>
    <lastmod>{p['date']}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>""")

    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "\n".join(rows) + "\n</urlset>\n")
    with open(os.path.join(OUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    robots = f"""User-agent: *
Allow: /

User-agent: Yandex
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
"""
    with open(os.path.join(OUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)

    print(f"\nГотово. Статей: {len(posts)}. Обновлены index.html, rss.xml, sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
