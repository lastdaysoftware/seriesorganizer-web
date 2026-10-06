#!/usr/bin/env python3
"""Build the static Series Organizer+ News pages and RSS feed.

No third-party packages are required. The intentionally small Markdown subset supports
paragraphs, ##/### headings, unordered lists, **bold**, *emphasis*, and HTTP(S)/mailto links.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "news"
NEWS = ROOT / "news"
POSTS = NEWS / "posts"
BASE_URL = "https://seriesorganizer.com"
FEED_URL = f"{BASE_URL}/feed.xml"

GISCUS = '''<script src="https://giscus.app/client.js"
        data-repo="lastdaysoftware/seriesorganizer-web"
        data-repo-id="R_kgDOUZHLzw"
        data-category="Announcements"
        data-category-id="DIC_kwDOUZHLz84DGb6E"
        data-mapping="pathname"
        data-strict="1"
        data-reactions-enabled="1"
        data-emit-metadata="0"
        data-input-position="bottom"
        data-theme="dark"
        data-lang="en"
        crossorigin="anonymous"
        async>
</script>'''

@dataclass(frozen=True)
class Post:
    title: str
    date: str
    slug: str
    summary: str
    body_html: str

    @property
    def url(self) -> str:
        return f"{BASE_URL}/news/posts/{self.slug}.html"


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("News files must start with YAML-style front matter")
    _, header, body = text.split("---\n", 2)
    data: dict[str, str] = {}
    for line in header.strip().splitlines():
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body.strip()


def inline_markup(text: str) -> str:
    text = escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\(((?:https?://|mailto:)[^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append(f"<p>{inline_markup(' '.join(line.strip() for line in paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_paragraph()
            close_list()
        elif line.startswith("### "):
            flush_paragraph(); close_list()
            out.append(f"<h3>{inline_markup(line[4:])}</h3>")
        elif line.startswith("## "):
            flush_paragraph(); close_list()
            out.append(f"<h2>{inline_markup(line[3:])}</h2>")
        elif line.startswith("- "):
            flush_paragraph()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline_markup(line[2:])}</li>")
        else:
            paragraph.append(line)

    flush_paragraph(); close_list()
    return "\n        ".join(out)


def load_posts() -> list[Post]:
    posts: list[Post] = []
    for path in sorted(CONTENT.glob("*.md"), reverse=True):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        required = ("title", "date", "slug", "summary")
        missing = [k for k in required if not meta.get(k)]
        if missing:
            raise ValueError(f"{path}: missing {', '.join(missing)}")
        datetime.strptime(meta["date"], "%Y-%m-%d")
        posts.append(Post(meta["title"], meta["date"], meta["slug"], meta["summary"], markdown_to_html(body)))
    return sorted(posts, key=lambda p: p.date, reverse=True)


def rss_link(prefix: str = "") -> str:
    return f'<link rel="alternate" type="application/rss+xml" title="Series Organizer+ News" href="{prefix}feed.xml" />'


def header(prefix: str = "../") -> str:
    return f'''<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="{prefix}index.html" aria-label="Series Organizer+ home">
      <img class="brand-icon" src="{prefix}assets/brand/series-organizer-plus-mark-dark.svg" alt="" />
      <div class="brand-text">
        <strong>Series Organizer+</strong>
        <small>Movies &amp; TV, organized.</small>
      </div>
    </a>
    <nav class="main-nav" aria-label="Main navigation">
      <a href="{prefix}index.html#features">Features</a>
      <a href="{prefix}index.html#discover">Discover</a>
      <a href="{prefix}news/">News</a>
      <a href="{prefix}index.html#legacy">Our story</a>
      <a href="{prefix}index.html#development">What's next</a>
    </nav>
    <nav class="footer-links" aria-label="Language"><span><strong>EN</strong> | <a href="{prefix}pt/">PT</a></span></nav>
  </div>
</header>'''


def footer(prefix: str = "../") -> str:
    return f'''<footer>
  <div class="container footer-inner">
    <div class="footer-brand">
      <div class="footer-brand-row">
        <img src="{prefix}assets/brand/series-organizer-plus-mark-dark.svg" alt="" />
        <div>
          <strong>Series Organizer+</strong>
          <small>Movies &amp; TV, organized.</small>
        </div>
      </div>
      <p>A LastDay Software project.</p>
      <p class="tmdb-attribution">
        This product uses the TMDB API but is not endorsed or certified by TMDB.
        <a href="https://www.themoviedb.org/">Visit TMDB</a>.
      </p>
    </div>
    <nav class="footer-links" aria-label="Footer navigation">
      <a href="{prefix}privacy.html">Privacy</a>
      <a href="{prefix}website-privacy.html">Website Privacy</a>
      <a href="{prefix}account-deletion.html">Account deletion</a>
      <a href="{prefix}support.html">Support</a>
    </nav>
  </div>
</footer>'''


def document_head(title: str, description: str, canonical: str, prefix: str) -> str:
    social = f"{BASE_URL}/assets/brand/series-organizer-plus-full-dark.png"
    return f'''<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="theme-color" content="#111111" />
<link rel="icon" type="image/svg+xml" href="{prefix}assets/brand/icon_master.svg" />
<link rel="alternate icon" type="image/png" href="{prefix}assets/brand/icon_play_store_512.png" />
<link rel="stylesheet" href="{prefix}styles.css" />
{rss_link(prefix)}
<title>{escape(title)} — Series Organizer+</title>
<meta name="description" content="{escape(description, quote=True)}" />
<link rel="canonical" href="{canonical}" />
<meta property="og:title" content="{escape(title, quote=True)} — Series Organizer+" />
<meta property="og:description" content="{escape(description, quote=True)}" />
<meta property="og:type" content="article" />
<meta property="og:url" content="{canonical}" />
<meta property="og:site_name" content="Series Organizer+" />
<meta property="og:image" content="{social}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{escape(title, quote=True)} — Series Organizer+" />
<meta name="twitter:description" content="{escape(description, quote=True)}" />
<meta name="twitter:image" content="{social}" />'''


def build_index(posts: list[Post]) -> None:
    cards = "\n".join(f'''      <article class="news-card">
        <p class="news-date">{f"{datetime.strptime(p.date, '%Y-%m-%d').strftime('%B')} {datetime.strptime(p.date, '%Y-%m-%d').day}, {datetime.strptime(p.date, '%Y-%m-%d').year}"}</p>
        <h2><a href="posts/{p.slug}.html">{escape(p.title)}</a></h2>
        <p>{escape(p.summary)}</p>
        <a class="news-read-more" href="posts/{p.slug}.html">Read more →</a>
      </article>''' for p in posts)
    html = f'''<!doctype html>
<html lang="en">
<head>
{document_head("News", "News and development updates from Series Organizer+.", f"{BASE_URL}/news/", "../")}
</head>
<body>
{header("../")}
<main class="news-page">
  <div class="container news-container">
    <a class="policy-back" href="../index.html">← Series Organizer+</a>
    <p class="section-label">NEWS</p>
    <h1>News</h1>
    <p class="news-intro">Development updates, release notes and stories from Series Organizer+.</p>
    <p><a class="news-rss-link" href="../feed.xml">RSS feed</a></p>
    <div class="news-list">
{cards}
    </div>
  </div>
</main>
{footer("../")}
</body>
</html>
'''
    NEWS.mkdir(parents=True, exist_ok=True)
    (NEWS / "index.html").write_text(html, encoding="utf-8")


def build_posts(posts: list[Post]) -> None:
    POSTS.mkdir(parents=True, exist_ok=True)
    for p in posts:
        date_label = f"{datetime.strptime(p.date, '%Y-%m-%d').strftime('%B')} {datetime.strptime(p.date, '%Y-%m-%d').day}, {datetime.strptime(p.date, '%Y-%m-%d').year}"
        html = f'''<!doctype html>
<html lang="en">
<head>
{document_head(p.title, p.summary, p.url, "../../")}
<meta property="article:published_time" content="{p.date}T00:00:00Z" />
</head>
<body>
{header("../../")}
<main class="news-page">
  <article class="container news-container news-article">
    <a class="policy-back" href="../">← News</a>
    <p class="section-label">SERIES ORGANIZER+ NEWS</p>
    <h1>{escape(p.title)}</h1>
    <p class="news-date">{date_label}</p>
    <div class="news-body">
        {p.body_html}
    </div>
    <div class="news-comments">
      <h2>Comments</h2>
      {GISCUS}
    </div>
  </article>
</main>
{footer("../../")}
</body>
</html>
'''
        (POSTS / f"{p.slug}.html").write_text(html, encoding="utf-8")


def build_feed(posts: list[Post]) -> None:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    for tag, text in (("title", "Series Organizer+ News"), ("link", f"{BASE_URL}/news/"),
                      ("description", "News and development updates from Series Organizer+."),
                      ("language", "en")):
        ET.SubElement(channel, tag).text = text
    for p in posts[:20]:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = p.title
        ET.SubElement(item, "link").text = p.url
        ET.SubElement(item, "guid", isPermaLink="true").text = p.url
        dt = datetime.strptime(p.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        ET.SubElement(item, "pubDate").text = format_datetime(dt)
        ET.SubElement(item, "description").text = p.summary
    ET.indent(rss, space="  ")
    (ROOT / "feed.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode") + "\n", encoding="utf-8")


def update_sitemap(posts: list[Post]) -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    start = "  <!-- NEWS:START -->"
    end = "  <!-- NEWS:END -->"
    generated = [start,
        "  <url>", f"    <loc>{BASE_URL}/news/</loc>", f"    <lastmod>{posts[0].date if posts else datetime.now().date()}</lastmod>", "  </url>"]
    for p in posts:
        generated += ["  <url>", f"    <loc>{p.url}</loc>", f"    <lastmod>{p.date}</lastmod>", "  </url>"]
    generated.append(end)
    block = "\n".join(generated)
    if start in text and end in text:
        text = re.sub(re.escape(start) + r".*?" + re.escape(end), block, text, flags=re.S)
    else:
        text = text.replace("</urlset>", block + "\n</urlset>")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    posts = load_posts()
    build_index(posts)
    build_posts(posts)
    build_feed(posts)
    update_sitemap(posts)
    print(f"Built {len(posts)} news post(s).")

if __name__ == "__main__":
    main()
