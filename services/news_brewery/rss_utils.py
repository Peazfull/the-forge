from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List

import feedparser


def fetch_rss_items(feed_url: str, max_items: int, mode: str, hours_window: int) -> List[Dict[str, str]]:
    parsed = feedparser.parse(feed_url)
    items: List[Dict[str, str]] = []
    now = datetime.now(timezone.utc)

    for entry in parsed.entries:
        url = entry.get("link") or ""
        title = entry.get("title") or ""
        published = entry.get("published") or entry.get("updated") or ""
        published_dt = None

        if published:
            try:
                published_dt = parsedate_to_datetime(published)
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)
            except Exception:
                published_dt = None

        if published_dt:
            if mode == "today" and published_dt.date() != now.date():
                continue
            if mode == "last_hours":
                if now - published_dt > timedelta(hours=hours_window):
                    continue

        if not url:
            continue

        items.append({
            "url": url,
            "title": title,
            "label_dt": published_dt.isoformat() if published_dt else "",
        })

        if len(items) >= max_items:
            break

    return items
