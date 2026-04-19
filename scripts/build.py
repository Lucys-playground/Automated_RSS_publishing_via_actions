from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "docs"
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
PUBLISH_TZ = os.getenv("PUBLISH_TZ", "Europe/Prague")
REBUILD_ALL = os.getenv("REBUILD_ALL", "").strip() == "1"
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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)


def today_iso_date() -> str:
    override = os.getenv("PUBLISH_DATE", "").strip()
    if override:
        return override

    try:
        tz = ZoneInfo(PUBLISH_TZ)
    except Exception:
        tz = timezone.utc

    return datetime.now(tz).date().isoformat()


def post_url(slug: str) -> str:
    return f"/posts/{slug}.html"


def post_output_path(slug: str) -> Path:
    return POSTS_DIR / f"{slug}.html"


def site_path(path: str) -> str:
    normalized = "/" + path.lstrip("/")

    if not SITE_URL:
        return normalized

    parsed = urlparse(SITE_URL)
    base_path = parsed.path.rstrip("/")
    if not base_path:
        return normalized

    return f"{base_path}{normalized}"


def full_url(path: str) -> str:
    normalized = "/" + path.lstrip("/")
    if SITE_URL:
        return f"{SITE_URL}{normalized}"
    return normalized


def format_human_date(value: str) -> str:
    return parse_dt(value).strftime("%d.%m.%Y")


def normalize_posts(raw_posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    posts: list[dict[str, Any]] = []

    for post in raw_posts:
        published_dt = parse_dt(post["published"])
        normalized = dict(post)
        normalized["published_dt"] = published_dt
        normalized["publish_date"] = published_dt.date().isoformat()
        normalized["path"] = post_url(post["slug"])
        posts.append(normalized)

    posts.sort(key=lambda item: item["published_dt"])
    return posts


def normalize_published(raw_published: list[dict[str, Any]]) -> list[dict[str, Any]]:
    published: list[dict[str, Any]] = []

    for post in raw_published:
        published_dt = parse_dt(post["published"])
        normalized = dict(post)
        normalized["published_dt"] = published_dt
        normalized["publish_date"] = published_dt.date().isoformat()
        normalized["path"] = post.get("path") or post_url(post["slug"])
        published.append(normalized)

    published.sort(key=lambda item: item["published_dt"])
    return published


def serialize_published(published: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = ["slug", "title", "summary", "published", "path", "language", "level", "html"]
    return [{key: post.get(key, "") for key in keys} for post in published]


def make_entry(post: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": post["slug"],
        "title": post["title"],
        "summary": post.get("summary", ""),
        "published": post["published"],
        "path": post.get("path") or post_url(post["slug"]),
        "language": post.get("language", ""),
        "level": post.get("level", ""),
        "html": post["html"],
        "published_dt": post["published_dt"],
        "publish_date": post["publish_date"],
    }


def find_post_for_date(posts: list[dict[str, Any]], iso_date: str) -> dict[str, Any] | None:
    for post in posts:
        if post["publish_date"] == iso_date:
            return post
    return None


def html_document(title: str, description: str, body: str, canonical_path: str) -> str:
    canonical_url = full_url(canonical_path)
    feed_url = full_url("/feed.xml")

    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <link rel="canonical" href="{escape(canonical_url)}">
  <link rel="alternate" type="application/rss+xml" title="{escape(SITE_TITLE)}" href="{escape(feed_url)}">
  <style>
    :root {{ color-scheme: light dark; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.6;
      background: #ffffff;
      color: #1f2937;
    }}
    main {{
      max-width: 760px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    h1 {{
      line-height: 1.2;
      margin-bottom: 0.5rem;
    }}
    .meta {{
      color: #6b7280;
      margin-bottom: 1.5rem;
    }}
    .summary {{
      font-size: 1.05rem;
      margin-bottom: 1.5rem;
    }}
    .content {{
      margin: 1.5rem 0 2rem;
    }}
    nav.post-nav {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      margin: 2rem 0;
      flex-wrap: wrap;
    }}
    a {{
      color: #0f766e;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    ul.archive {{
      padding-left: 1.2rem;
    }}
    li {{
      margin: 0.35rem 0;
    }}
    .back {{
      margin-top: 2rem;
    }}
  </style>
</head>
<body>
  <main>
{body}
  </main>
</body>
</html>
"""


def render_post_html(
    post: dict[str, Any],
    prev_post: dict[str, Any] | None,
    next_post: dict[str, Any] | None,
) -> str:
    nav_links: list[str] = []

    if prev_post:
        nav_links.append(
            "<a href='{href}'>← {title}</a>".format(
                href=escape(site_path(prev_post["path"])),
                title=escape(prev_post["title"]),
            )
        )

    if next_post:
        nav_links.append(
            "<a href='{href}'>{title} →</a>".format(
                href=escape(site_path(next_post["path"])),
                title=escape(next_post["title"]),
            )
        )

    nav_html = ""
    if nav_links:
        nav_html = "    <nav class='post-nav'>\n      " + "\n      ".join(nav_links) + "\n    </nav>\n"

    summary_html = ""
    if post.get("summary"):
        summary_html = f"    <p class='summary'>{escape(post['summary'])}</p>\n"

    body = (
        f"    <h1>{escape(post['title'])}</h1>\n"
        f"    <p class='meta'>{escape(format_human_date(post['published']))} · "
        f"{escape(post.get('language', ''))} · {escape(post.get('level', ''))}</p>\n"
        f"{summary_html}"
        "    <div class='content'>\n"
        f"      {post['html']}\n"
        "    </div>\n"
        f"{nav_html}"
        f"    <p class='back'><a href='{escape(site_path('/index.html'))}'>← Zpět na archiv</a></p>\n"
    )

    return html_document(
        title=post["title"],
        description=post.get("summary", SITE_DESCRIPTION),
        body=body,
        canonical_path=post["path"],
    )


def render_index_html(published: list[dict[str, Any]]) -> str:
    items: list[str] = []

    for post in reversed(published):
        items.append(
            f'      <li><a href="{escape(site_path(post["path"]))}">{escape(post["title"])}</a> '
            f'<small>({escape(format_human_date(post["published"]))})</small></li>'
        )

    archive_html = "\n".join(items) if items else "      <li>Zatím tu není žádný publikovaný článek.</li>"

    body = (
        f"    <h1>{escape(SITE_TITLE)}</h1>\n"
        f"    <p>{escape(SITE_DESCRIPTION)}</p>\n"
        f"    <p><a href='{escape(site_path('/feed.xml'))}'>RSS feed</a></p>\n"
        "    <h2>Archiv</h2>\n"
        "    <ul class='archive'>\n"
        f"{archive_html}\n"
        "    </ul>\n"
    )

    return html_document(
        title=SITE_TITLE,
        description=SITE_DESCRIPTION,
        body=body,
        canonical_path="/index.html",
    )


def render_feed_xml(published: list[dict[str, Any]]) -> str:
    last_30 = published[-30:]
    items: list[str] = []

    for post in reversed(last_30):
        url = full_url(post["path"])
        pub_dt = parse_dt(post["published"]).astimezone(timezone.utc)
        description = escape(post.get("summary", ""))

        items.append(
            f"""  <item>
    <title>{escape(post["title"])}</title>
    <link>{escape(url)}</link>
    <guid>{escape(url)}</guid>
    <pubDate>{format_datetime(pub_dt)}</pubDate>
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


def render_post_neighbors(published: list[dict[str, Any]], index: int) -> None:
    post = published[index]
    prev_post = published[index - 1] if index > 0 else None
    next_post = published[index + 1] if index + 1 < len(published) else None

    html = render_post_html(post, prev_post, next_post)
    write_text(post_output_path(post["slug"]), html)


def main() -> None:
    ensure_dirs()

    raw_posts = load_json(POSTS_JSON, default=[])
    raw_published = load_json(PUBLISHED_JSON, default=[])

    posts = normalize_posts(raw_posts)
    published = normalize_published(raw_published)
    published_slugs = {item["slug"] for item in published}

    publish_date = today_iso_date()
    todays_post = find_post_for_date(posts, publish_date)
    changed = False

    if todays_post and todays_post["slug"] not in published_slugs:
        published.append(make_entry(todays_post))
        published.sort(key=lambda item: item["published_dt"])
        changed = True

    if REBUILD_ALL:
        for idx in range(len(published)):
            render_post_neighbors(published, idx)
    elif changed:
        current_index = next(
            i for i, item in enumerate(published) if item["slug"] == todays_post["slug"]
        )
        for idx in {current_index - 1, current_index, current_index + 1}:
            if 0 <= idx < len(published):
                render_post_neighbors(published, idx)
    elif published:
        latest_index = len(published) - 1
        latest_post_path = post_output_path(published[latest_index]["slug"])
        if not latest_post_path.exists():
            render_post_neighbors(published, latest_index)

    save_json(PUBLISHED_JSON, serialize_published(published))
    write_text(INDEX_HTML, render_index_html(published))
    write_text(FEED_XML, render_feed_xml(published))

    if changed:
        print(f"Published post for {publish_date}")
    else:
        print(f"No new post published for {publish_date}")


if __name__ == "__main__":
    main()
