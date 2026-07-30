"""
Собирает блог из markdown-файлов.

Кладёшь статью в docs/blog/posts/*.md — получаешь готовую HTML-страницу
в стиле лендинга, обновлённый список статей, RSS-ленту и разметку для Google.

Запуск:  python3 tools/blog_build.py
Нужен:   pip install markdown
"""
import html
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
  display:block; padding:22px; margin-bottom:16px; border:1px solid var(--border);
  border-radius:12px; background:var(--bg3); transition:border-color .2s, transform .2s;
}
.card:hover{border-color:var(--gold2); text-decoration:none; transform:translateY(-2px)}
.card h2{margin:0 0 8px; font-size:20px; color:var(--text)}
.card p{color:var(--text2); margin:0 0 10px; font-size:15px}
.card .meta{margin:0; font-size:13px}
footer.bottom{border-top:1px solid var(--border); padding:28px 0; color:var(--text3); font-size:14px}
footer.bottom .wrap{display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px}
.soc-row{display:flex; gap:10px; flex-wrap:wrap}
.soc-btn{
  display:inline-flex; align-items:center; gap:8px; padding:9px 16px;
  border:1px solid var(--border); border-radius:9px; background:var(--bg2);
  color:var(--text); font-size:14px; font-weight:500; transition:all .2s;
}
.soc-btn:hover{border-color:var(--gold); color:var(--gold); text-decoration:none; background:var(--bg3)}
.soc-btn svg{opacity:.9}
.back{display:inline-block; margin-bottom:28px; font-size:14px; color:var(--text2)}
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


def page(title, description, canonical, body, lang="ru", jsonld=""):
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{canonical}">
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
  <a class="brand" href="{SITE_URL}/landing.html">Anchor<span>Vault</span>Coin</a>
  <nav class="nav">
    <a href="{BLOG_URL}/">Блог</a>
    <a href="{SITE_URL}/landing.html">О сервисе</a>
    <a class="soc" href="https://x.com/Anchorvaultcoin" aria-label="X">{IC_X}<span>X</span></a>
    <a class="soc" href="https://t.me/AnchorVaultCoin" aria-label="Telegram">{IC_TG}<span>Telegram</span></a>
  </nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer class="bottom"><div class="wrap">
  <div>© {datetime.now().year} {SITE_NAME}</div>
  <div class="soc-row">
    <a class="soc-btn" href="https://x.com/Anchorvaultcoin">{IC_X}<span>Читать в X</span></a>
    <a class="soc-btn" href="https://t.me/AnchorVaultCoin">{IC_TG}<span>Telegram-канал</span></a>
  </div>
</div></footer>
</body>
</html>
"""


def main():
    if not os.path.isdir(POSTS_DIR):
        os.makedirs(POSTS_DIR, exist_ok=True)
        print(f"Создал папку {POSTS_DIR}. Положи туда .md файлы.")
        return

    md = markdown.Markdown(extensions=["extra", "sane_lists", "smarty"])
    posts = []

    for fn in sorted(os.listdir(POSTS_DIR)):
        if not fn.endswith(".md"):
            continue
        with open(os.path.join(POSTS_DIR, fn), encoding="utf-8") as f:
            meta, body = read_front_matter(f.read())

        slug = meta.get("slug") or slugify(os.path.splitext(fn)[0])
        title = meta.get("title", slug)
        desc = meta.get("description", "")
        date = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
        lang = meta.get("lang", "ru")

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

        article = f'''<a class="back" href="{BLOG_URL}/">← Все статьи</a>
<h1>{html.escape(title)}</h1>
<div class="meta">{date}</div>
{content}
<hr>
<p class="meta">AnchorVaultCoin — сервис хранения и переводов криптовалюты,
где каждая операция подтверждается двумя отдельными ключами.
<a href="{SITE_URL}/landing.html">Подробнее</a>.</p>'''

        with open(os.path.join(OUT_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(page(f"{title} — {SITE_NAME}", desc, url, article, lang, jsonld))

        posts.append({"slug": slug, "title": title, "desc": desc, "date": date, "url": url})
        print(f"собрано: {slug}.html")

    posts.sort(key=lambda p: p["date"], reverse=True)

    cards = "\n".join(
        f'''<a class="card" href="{BLOG_URL}/{p["slug"]}.html">
  <h2>{html.escape(p["title"])}</h2>
  <p>{html.escape(p["desc"])}</p>
  <div class="meta">{p["date"]}</div>
</a>''' for p in posts) or "<p>Пока пусто.</p>"

    index_body = f'''<h1>{BLOG_TITLE}</h1>
<p class="lead">{BLOG_DESC}</p>
{cards}'''
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(f"{BLOG_TITLE} — {SITE_NAME}", BLOG_DESC, f"{BLOG_URL}/", index_body))

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
  <language>ru</language>
  <lastBuildDate>{now}</lastBuildDate>
{items}
</channel></rss>'''
    with open(os.path.join(OUT_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss)

    # Карта сайта: сначала постоянные страницы, потом статьи блога
    static_pages = [
        (f"{SITE_URL}/landing.html", "1.0", "weekly"),
        (f"{BASE_URL}/", "1.0", "weekly"),
        (f"{BASE_URL}/pulse.html", "0.8", "weekly"),
        (f"{BLOG_URL}/", "0.9", "weekly"),
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

Sitemap: {BASE_URL}/sitemap.xml
"""
    with open(os.path.join(OUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)

    print(f"\nГотово. Статей: {len(posts)}. Обновлены index.html, rss.xml, sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
