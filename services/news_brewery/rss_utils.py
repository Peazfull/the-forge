from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Dict, List
from urllib.request import Request, urlopen
import re

import feedparser


def fetch_rss_items(
    feed_url: str,
    max_items: int,
    mode: str,
    hours_window: int,
    ignore_time_filter: bool = False,
) -> List[Dict[str, str]]:
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

        if published_dt and not ignore_time_filter:
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


def _parse_time_label(text: str) -> datetime | None:
    time_match = re.search(r"\b(\d{1,2})h(\d{2})\b", text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        now = datetime.now()
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    date_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", text)
    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3))
        if year < 100:
            year += 2000
        return datetime(year, month, day)
    month_match = re.search(
        r"\b(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s*(\d{4})?\b",
        text,
        re.IGNORECASE,
    )
    if month_match:
        day = int(month_match.group(1))
        month_name = month_match.group(2).lower()
        year = int(month_match.group(3)) if month_match.group(3) else datetime.now().year
        months = {
            "janvier": 1,
            "février": 2,
            "fevrier": 2,
            "mars": 3,
            "avril": 4,
            "mai": 5,
            "juin": 6,
            "juillet": 7,
            "août": 8,
            "aout": 8,
            "septembre": 9,
            "octobre": 10,
            "novembre": 11,
            "décembre": 12,
            "decembre": 12,
        }
        month = months.get(month_name)
        if month:
            return datetime(year, month, day)
    return None


def _within_window(label_dt: datetime | None, mode: str, hours_window: int) -> bool:
    if label_dt is None:
        return True
    now = datetime.now()
    if mode == "today":
        return label_dt.date() == now.date()
    if mode == "last_hours":
        return now - label_dt <= timedelta(hours=hours_window)
    return True


def fetch_dom_items(
    page_url: str,
    max_items: int,
    mode: str,
    hours_window: int,
) -> List[Dict[str, str]]:
    try:
        req = Request(page_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=20) as resp:
            html_text = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    wrapper_match = re.search(r'<div class="wrapper-news-list">(.*?)<div class="pagination">', html_text, re.S)
    content = wrapper_match.group(1) if wrapper_match else html_text

    items: List[Dict[str, str]] = []
    seen = set()
    pattern = re.compile(
        r'<div class="item">.*?<div class="meta-date">\s*([^<]+)\s*</div>.*?<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        re.S,
    )

    for time_text, href, title_html in pattern.findall(content):
        url = href.strip()
        if not url:
            continue
        if url.startswith("/"):
            url = f"https://www.tradingsat.com{url}"
        if url in seen:
            continue
        seen.add(url)

        title = re.sub(r"<.*?>", "", title_html)
        title = unescape(title).strip()

        label_dt = _parse_time_label(time_text.strip())
        if not _within_window(label_dt, mode, hours_window):
            continue

        items.append({
            "url": url,
            "title": title,
            "label_dt": label_dt.isoformat() if label_dt else "",
        })
        if len(items) >= max_items:
            break

    return items


def merge_article_items(
    primary: List[Dict[str, str]],
    secondary: List[Dict[str, str]],
    limit: int,
) -> List[Dict[str, str]]:
    seen = set()
    merged: List[Dict[str, str]] = []
    for group in (primary, secondary):
        for item in group:
            url = item.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            merged.append(item)
            if limit and len(merged) >= limit:
                return merged
    return merged
