#!/usr/bin/env python3
# সাহিত্য বাতায়ন: Google Sheet (CSV) থেকে হোমপেজ, লেখার পেজ ও sitemap তৈরি করে

import csv
import html
import io
import os
import re
import urllib.request

SITE = "https://digital-bd.github.io/sahiya-batayan-new"  # কাস্টম ডোমেইন হলে এখানে বদলান
SITE_NAME = "সাহিত্য বাতায়ন"
TAGLINE = "বাংলা সাহিত্য, কবিতা, গল্প ও প্রবন্ধের অনলাইন পত্রিকা"
SHEET_CSV_URL = os.environ.get("SHEET_CSV_URL", "").strip()
PUBLIC_STATUS = {"approved", "published", "প্রকাশিত"}
DEFAULT_IMG = SITE + "/img/og-default.png"
FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+Bengali:wght@400;700'
    '&family=Noto+Sans+Bengali:wght@400;600&display=swap" rel="stylesheet">'
)


def esc(s):
    return html.escape((s or "").strip(), quote=True)


def load_rows():
    if SHEET_CSV_URL:
        raw = urllib.request.urlopen(SHEET_CSV_URL, timeout=30).read().decode("utf-8")
    else:
        with open("articles.csv", encoding="utf-8") as f:
            raw = f.read()
    raw = raw.replace("\r\n", "\n").lstrip("\ufeff")
    return list(csv.DictReader(io.StringIO(raw)))


def get_articles():
    arts = []
    for n, row in enumerate(load_rows(), 1):
        if (row.get("status") or "").strip().lower() not in PUBLIC_STATUS:
            continue
        if not (row.get("title") or "").strip():
            continue
        slug = re.sub(r"[^A-Za-z0-9_-]", "", (row.get("id") or "").strip()) or f"lekha-{n}"
        row["_slug"] = slug
        arts.append(row)
    if not arts:
        # শিট পড়তে সমস্যা হলে পুরনো পেজগুলো মুছে ফেলা থেকে বিরত থাকি
        raise SystemExit("কোনো প্রকাশিত লেখা পাওয়া যায়নি। কিছুই বদলানো হয়নি।")
    return arts[::-1]  # শিটের নিচের সারি = সবচেয়ে নতুন ধরা হয়েছে


def cat_of(a):
    return (a.get("category") or "").strip() or "অন্যান্য"


def body_html(text):
    paras = [p for p in re.split(r"\n\s*\n", (text or "").strip()) if p.strip()]
    return "\n".join("<p>" + esc(p).replace("\n", "<br>") + "</p>" for p in paras)


def head(title, desc, url, img, css, og_type, prefix):
    return f"""<!doctype html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{esc(img)}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:locale" content="bn_BD">
<meta name="twitter:card" content="summary_large_image">
{FONTS}
<link rel="stylesheet" href="{css}">
</head>
<body>
<header class="masthead">
  <a class="brand" href="{prefix}index.html">{SITE_NAME}</a>
  <div class="tagline">{TAGLINE}</div>
</header>
"""


def article_page(a):
    title = (a.get("title") or "").strip()
    summary = (a.get("excerpt") or "").strip()
    img = (a.get("image") or "").strip()
    cat = esc(a.get("category"))
    author = esc(a.get("author"))
    date = esc(a.get("date"))
    url = f"{SITE}/articles/{a['_slug']}.html"
    img_html = f'<figure><img src="{esc(img)}" alt="{esc(title)}"></figure>' if img else ""
    sum_html = f'<p class="summary">{esc(summary)}</p>' if summary else ""
    top = head(f"{title} | {SITE_NAME}", summary or title, url, img or DEFAULT_IMG,
               "../style.css", "article", "../")
    body = body_html(a.get("content"))
    return top + f"""<main class="article">
  <p class="cat">{cat}</p>
  <h1>{esc(title)}</h1>
  <p class="meta">{author} · {date}</p>
  {img_html}
  {sum_html}
  <div class="body">{body}</div>
  <p class="back"><a href="../index.html">← প্রচ্ছদে ফিরুন</a></p>
</main>
<footer>© {SITE_NAME}</footer>
</body>
</html>
"""


def card(a):
    img = (a.get("image") or "").strip()
    img_html = f'<img src="{esc(img)}" alt="" loading="lazy">' if img else ""
    href = f"articles/{a['_slug']}.html"
    return (f'<article class="card">{img_html}'
            f'<h3><a href="{href}">{esc(a.get("title"))}</a></h3>'
            f'<p>{esc(a.get("excerpt"))}</p>'
            f'<small>{esc(a.get("author"))} · {esc(a.get("date"))}</small></article>')


def home_page(arts):
    cats = []
    for a in arts:
        if cat_of(a) not in cats:
            cats.append(cat_of(a))

    lead = arts[0]
    lead_img = (lead.get("image") or "").strip()
    lead_img_tag = f'<img src="{esc(lead_img)}" alt="">' if lead_img else ""
    lead_html = (f'<a class="lead" href="articles/{lead["_slug"]}.html">{lead_img_tag}'
                 f'<div><span class="cat">{esc(lead.get("category"))}</span>'
                 f'<h2>{esc(lead.get("title"))}</h2>'
                 f'<p>{esc(lead.get("excerpt"))}</p></div></a>')

    nav = "".join(f'<a href="#c{i}">{esc(c)}</a>' for i, c in enumerate(cats))
    secs = []
    for i, c in enumerate(cats):
        items = [a for a in arts if cat_of(a) == c][:6]
        secs.append(f'<section id="c{i}"><h2 class="sec">{esc(c)}</h2>'
                    f'<div class="grid">' + "".join(card(a) for a in items) + "</div></section>")

    top = head(f"{SITE_NAME}: অনলাইন পত্রিকা", TAGLINE, SITE + "/", DEFAULT_IMG,
               "style.css", "website", "")
    return (top + f'<nav class="cats">{nav}</nav>'
            f'<main class="home">{lead_html}{"".join(secs)}</main>'
            f'<footer>© {SITE_NAME}</footer></body></html>')


def sitemap(arts):
    urls = [SITE + "/"] + [f"{SITE}/articles/{a['_slug']}.html" for a in arts]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + body + "\n</urlset>\n")


def main():
    arts = get_articles()  # আগে পড়া, যাতে ব্যর্থ হলে পুরনো ফাইল না মোছে
    os.makedirs("articles", exist_ok=True)
    for f in os.listdir("articles"):
        if f.endswith(".html"):
            os.remove(os.path.join("articles", f))

    for a in arts:
        with open(f"articles/{a['_slug']}.html", "w", encoding="utf-8") as f:
            f.write(article_page(a))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(home_page(arts))
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap(arts))
    open(".nojekyll", "w").close()
    print(f"{len(arts)}টি লেখা তৈরি হয়েছে")


if __name__ == "__main__":
    main()