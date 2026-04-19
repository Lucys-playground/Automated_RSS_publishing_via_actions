
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"
POSTS_DIR = SITE_DIR / "posts"

POSTS_JSON = DATA_DIR / "posts.json"
PUBLISHED_JSON = DATA_DIR / "published.json"
INDEX_HTML = SITE_DIR / "index.html"
FEED_XML = SITE_DIR / "feed.xml"

SITE_URL = os.getenv("SITE_URL", "").rstrip("/")
SITE_TITLE = os.getenv("SITE_TITLE", "Španělština každý den")
SITE_DESCRIPTION = os.getenv(
    "SITE_DESCRIPTION",
    "Krátké španělské texty a dialogy pro začátečníky.",
)
TIMEZONE_FALLBACK = timezone.utc


def parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TIMEZONE_FALLBACK)
    return dt


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)


def today_iso_date() -> str:
    override = os.getenv("PUBLISH_DATE")
    if override:
        return override
    return datetime.now(timezone.utc).date().isoformat()


def normalize_posts(raw_posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    posts: list[dict[str, Any]] = []
    for post in raw_posts:
        published_dt = parse_dt(post["published"])
        normalized = dict(post)
        normalized["published_dt"] = published_dt
        normalized["publish_date"] = published_dt.date().isoformat()
        posts.append(normalized)
    posts.sort(key=lambda p: p["published_dt"])
    return posts


def find_post_for_date(posts: list[dict[str, Any]], iso_date: str) -> dict[str, Any] | None:
    for post in posts:
        if post["publish_date"] == iso_date:
            return post
    return None


def post_output_path(slug: str) -> Path:
    return POSTS_DIR / f"{slug}.html"


def post_url(slug: str) -> str:
    return f"/posts/{slug}.html"


def full_url(path: str) -> str:
    if SITE_URL:
        return f"{SITE_URL}{path}"
    return path


def format_human_date(value: str) -> str:
    dt = parse_dt(value)
    return dt.strftime("%d.%m.%Y")


def render_post_html(
    post: dict[str, Any],
    prev_post: dict[str, Any] | None,
    next_post: dict[str, Any] | None,
) -> str:
    title = escape(post["title"])
    summary = escape(post.get("summary", ""))
    published = format_human_date(post["published"])
    level = escape(post.get("level", ""))
    language = escape(post.get("language", ""))

    prev_link = ""
    if prev_post:
        prev_link = (
            f'<a class="nav-link prev" href="{escape(post_url(prev_post["slug"]))}">'
            f'← {escape(prev_post["title"])}'
            f"</a>"
        )

    next_link = ""
    if next_post:
        next_link = (
            f'<a class="nav-link next" href="{escape(post_url(next_post["slug"]))}">'
            f'{escape(next_post["title"])} →'
            f"</a>"
        )

    nav = ""
    if prev_link or next_link:
        nav = (
            '<nav class="post-nav">'
            f'<div class="post-nav-left">{prev_link}</div>'
            f'<div class="post-nav-right">{next_link}</div>'
            "</nav>"
        )

    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{summary}">
  <style>
    body {{
      font-family: system-ui, sans-serif;
      max-width: 760px;
      margin: 0 auto;
      padding: 2rem 1rem 4rem;
      line-height: 1.65;
    }}
    h1 {{ line-height: 1.2; margin-bottom: 0.4rem; }}
    .meta {{ color: #555; margin-bottom: 2rem; font-size: 0.95rem; }}
    .content {{ margin-bottom: 2rem; }}
    .post-nav {{
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      padding-top: 1.5rem;
      border-top: 1px solid #ddd;
      margin-top: 2rem;
    }}
    .post-nav-left, .post-nav-right {{ flex: 1; }}
    .post-nav-right {{ text-align: right; }}
    .nav-link {{ text-decoration: none; }}
    a {{ color: #0b57d0; }}
    .back {{ margin-top: 2rem; display: inline-block; }}
  </style>
</head>
<body>
  <main>
    <article>
      <h1>{title}</h1>
      <div class="meta">{published} · {language} · {level}</div>
      <div class="content">
        {post["html"]}
      </div>
      {nav}
      <p><a class="back" href="/index.html">← Zpět na archiv</a></p>
    </article>
  </main>
</body>
</html>
"""


def render_index_html(published: list[dict[str, Any]]) -> str:
    items: list[str] = []
    for post in reversed(published):
        items.append(
            "<li>"
            f'<a href="{escape(post["path"])}">{escape(post["title"])}</a>'
            f' <small>({escape(format_human_date(post["published"]))})</small>'
            "</li>"
        )
    joined = "\n      ".join(items)

    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(SITE_TITLE)}</title>
  <meta name="description" content="{escape(SITE_DESCRIPTION)}">
  <style>
    body {{
      font-family: system-ui, sans-serif;
      max-width: 760px;
      margin: 0 auto;
      padding: 2rem 1rem 4rem;
      line-height: 1.65;
    }}
    ul {{ padding-left: 1.25rem; }}
    li {{ margin: 0.5rem 0; }}
    a {{ color: #0b57d0; }}
  </style>
</head>
<body>
  <main>
    <h1>{escape(SITE_TITLE)}</h1>
    <p>{escape(SITE_DESCRIPTION)}</p>
    <p><a href="/feed.xml">RSS feed</a></p>
    <h2>Archiv</h2>
    <ul>
      {joined}
    </ul>
  </main>
</body>
</html>
"""


def render_feed_xml(published: list[dict[str, Any]]) -> str:
    last_30 = published[-30:]
    items: list[str] = []
    for post in reversed(last_30):
        url = full_url(post["path"])
        pub_dt = parse_dt(post["published"])
        description = escape(post.get("summary", ""))
        items.append(
            f"""
    <item>
      <title>{escape(post['title'])}</title>
      <link>{escape(url)}</link>
      <guid>{escape(url)}</guid>
      <pubDate>{format_datetime(pub_dt.astimezone(timezone.utc))}</pubDate>
      <description>{description}</description>
    </item>"""
        )

    home = full_url("/index.html")
    xml_items = "\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(SITE_TITLE)}</title>
    <link>{escape(home)}</link>
    <description>{escape(SITE_DESCRIPTION)}</description>
    <language>cs</language>
{xml_items}
  </channel>
</rss>
"""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    ensure_dirs()

    raw_posts = load_json(POSTS_JSON, default=[])
    published = load_json(PUBLISHED_JSON, default=[])

    posts = normalize_posts(raw_posts)
    published_slugs = {item["slug"] for item in published}
    publish_date = today_iso_date()

    todays_post = find_post_for_date(posts, publish_date)
    changed = False

    if todays_post and todays_post["slug"] not in published_slugs:
        prev_post = published[-1] if published else None

        new_entry = {
            "slug": todays_post["slug"],
            "title": todays_post["title"],
            "summary": todays_post.get("summary", ""),
            "published": todays_post["published"],
            "path": post_url(todays_post["slug"]),
            "language": todays_post.get("language", ""),
            "level": todays_post.get("level", ""),
            "html": todays_post["html"],
        }
        published.append(new_entry)
        changed = True

        new_html = render_post_html(todays_post, prev_post, None)
        write_text(post_output_path(todays_post["slug"]), new_html)

        if prev_post:
            prev_prev = published[-3] if len(published) >= 3 else None
            prev_post_full = {
                **prev_post,
                "html": prev_post.get("html", ""),
            }
            prev_html = render_post_html(prev_post_full, prev_prev, new_entry)
            write_text(post_output_path(prev_post["slug"]), prev_html)

        save_json(PUBLISHED_JSON, published)

    index_html = render_index_html(published)
    write_text(INDEX_HTML, index_html)

    feed_xml = render_feed_xml(published)
    write_text(FEED_XML, feed_xml)

    if changed:
        print(f"Published post for {publish_date}")
    else:
        print(f"No new post published for {publish_date}")


if __name__ == "__main__":
    main()
