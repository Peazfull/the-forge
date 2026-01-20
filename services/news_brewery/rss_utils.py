from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Dict, List
from urllib.request import Request, urlopen
import gzip
try:
    import brotli  # type: ignore
except Exception:
    brotli = None

import re
try:
    from services.hand_brewery.firecrawl_client import fetch_url_text
except Exception:
    fetch_url_text = None

import feedparser


def fetch_rss_items(
    feed_url: str,
    max_items: int,
    mode: str,
    hours_window: int,
    ignore_time_filter: bool = False,
) -> List[Dict[str, str]]:
    # Parse RSS feed and return a list of URL + title + timestamp.
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

        # Apply time filter unless explicitly disabled.
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
    # Parse timestamps like "11h44" or "12/01/2026" or "12 janvier 2026".
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
    # Filter by time window ("today" or "last_hours").
    if label_dt is None:
        return True
    now = datetime.now()
    # If the hour appears "in the future", assume it belongs to yesterday.
    if label_dt - now > timedelta(hours=1):
        label_dt = label_dt - timedelta(days=1)
    if mode == "today":
        return label_dt.date() == now.date()
    if mode == "last_hours":
        return now - label_dt <= timedelta(hours=hours_window)
    return True


def _fetch_html_text(page_url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    try:
        req = Request(page_url, headers=headers)
        with urlopen(req, timeout=20) as resp:
            raw = resp.read()
            encoding = (resp.headers.get("Content-Encoding") or "").lower()
            if "gzip" in encoding:
                raw = gzip.decompress(raw)
            elif "br" in encoding and brotli:
                raw = brotli.decompress(raw)
            return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def fetch_dom_items(
    page_url: str,
    max_items: int,
    mode: str,
    hours_window: int,
) -> List[Dict[str, str]]:
    # Fetch the "TOUT" list directly from the HTML DOM (no JS required).
    html_text = _fetch_html_text(page_url)
    if not html_text:
        return []

    # Narrow HTML to the news list block to reduce noise.
    wrapper_match = re.search(r'<div class="wrapper-news-list">(.*?)<div class="pagination">', html_text, re.S)
    content = wrapper_match.group(1) if wrapper_match else html_text

    items: List[Dict[str, str]] = []
    seen = set()
    # Extract time + href + title from each ".item".
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

        # Strip HTML tags from the title.
        title = re.sub(r"<.*?>", "", title_html)
        title = unescape(title).strip()

        # Apply time window filter.
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


def _parse_relative_time(text: str) -> datetime | None:
    match = re.search(r"il y a\s+(\d+)\s+(minute|minutes|heure|heures|jour|jours)", text, re.I)
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2).lower()
    if "minute" in unit:
        return datetime.now() - timedelta(minutes=value)
    if "heure" in unit:
        return datetime.now() - timedelta(hours=value)
    if "jour" in unit:
        return datetime.now() - timedelta(days=value)
    return None


def fetch_beincrypto_dom_items(
    page_url: str,
    max_items: int,
    mode: str,
    hours_window: int,
) -> List[Dict[str, str]]:
    html_text = _fetch_html_text(page_url)
    if not html_text:
        return []

    items: List[Dict[str, str]] = []
    seen = set()

    block_match = re.search(
        r"Les dernières nouvelles.*?<div class=\"ant-card-body\">(.*?)</div>\s*</div>",
        html_text,
        re.S,
    )
    content = block_match.group(1) if block_match else html_text

    pattern = re.compile(
        r'<a[^>]+class="ArticleCardSmall[^"]*"[^>]+href="([^"]+)"[^>]*>.*?'
        r'<time[^>]+datetime="([^"]+)"[^>]*>(.*?)</time>.*?'
        r'<div[^>]+data-testid="main-element"[^>]*>(.*?)</div>',
        re.S,
    )

    for href, datetime_attr, time_text, title_html in pattern.findall(content):
        url = href.strip()
        if not url:
            continue
        if url.startswith("/"):
            url = f"https://fr.beincrypto.com{url}"
        if url in seen:
            continue
        seen.add(url)

        title = re.sub(r"<.*?>", "", title_html)
        title = unescape(title).strip()

        label_dt = None
        if datetime_attr:
            try:
                label_dt = datetime.fromisoformat(datetime_attr.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                label_dt = None
        if label_dt is None and time_text:
            label_dt = _parse_relative_time(time_text.strip())

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


def _parse_boursedirect_datetime(day_text: str, month_year_text: str, time_text: str) -> datetime | None:
    month_year = month_year_text.strip().split()
    if len(month_year) < 1:
        return None
    month_name = month_year[0].lower()
    year = int(month_year[1]) if len(month_year) > 1 and month_year[1].isdigit() else datetime.now().year
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
    if not month:
        return None
    try:
        day = int(day_text)
    except Exception:
        return None
    hour, minute = 0, 0
    if time_text:
        time_match = re.search(r"(\d{1,2}):(\d{2})", time_text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
    return datetime(year, month, day, hour, minute)


def fetch_boursedirect_dom_items(
    page_url: str,
    max_items: int,
    mode: str,
    hours_window: int,
) -> List[Dict[str, str]]:
    html_text = _fetch_html_text(page_url)
    if not html_text:
        return []

    items: List[Dict[str, str]] = []
    seen = set()

    pattern = re.compile(
        r'<div class="timeline-item[^"]*">.*?'
        r'<div class="timeline-date-left[^"]*">([^<]+)</div>.*?'
        r'<span class="publishDay">(\d{1,2})</span>.*?'
        r'<span class="text-muted">([^<]+)</span>.*?'
        r'<a href="([^"]+)">.*?'
        r'<h2 class="timeline-title[^"]*">(.*?)</h2>',
        re.S,
    )

    for time_text, day_text, month_year_text, href, title_html in pattern.findall(html_text):
        url = href.strip()
        if not url:
            continue
        if url.startswith("/"):
            url = f"https://www.boursedirect.fr{url}"
        if url in seen:
            continue
        seen.add(url)

        title = re.sub(r"<.*?>", "", title_html)
        title = unescape(title).strip()

        label_dt = _parse_boursedirect_datetime(day_text, month_year_text, time_text)
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


def fetch_boursier_dom_items(
    page_url: str,
    max_items: int,
    mode: str,
    hours_window: int,
    use_firecrawl_fallback: bool = False,
) -> List[Dict[str, str]]:
    html_text = _fetch_html_text(page_url)
    if not html_text:
        html_text = ""

    items: List[Dict[str, str]] = []
    seen = set()

    pattern = re.compile(
        r'<article[^>]*class="[^"]*item[^"]*"[^>]*>.*?'
        r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>.*?'
        r'<time[^>]+class="date"[^>]+datetime="([^"]+)"',
        re.S,
    )

    for href, title_html, datetime_attr in pattern.findall(html_text):
        url = href.strip()
        if not url:
            continue
        if url.startswith("/"):
            url = f"https://www.boursier.com{url}"
        if url in seen:
            continue
        seen.add(url)

        title = re.sub(r"<.*?>", "", title_html)
        title = unescape(title).strip()

        label_dt = None
        if datetime_attr:
            try:
                label_dt = datetime.fromisoformat(datetime_attr.strip())
            except Exception:
                label_dt = None

        if not _within_window(label_dt, mode, hours_window):
            continue

        items.append({
            "url": url,
            "title": title,
            "label_dt": label_dt.isoformat() if label_dt else "",
        })
        if len(items) >= max_items:
            break

    if items:
        return items

    if use_firecrawl_fallback and fetch_url_text:
        try:
            markdown = fetch_url_text(page_url)
        except Exception:
            markdown = ""
        if markdown:
            link_pattern = re.compile(r"\[([^\]]+)\]\((https?://www\.boursier\.com/[^)]+)\)")
            for title_text, href in link_pattern.findall(markdown):
                url = href.strip()
                if "/actualites/economie/" not in url and "/actions/actualites/economie/" not in url:
                    continue
                if url in seen:
                    continue
                seen.add(url)
                title = title_text.strip()
                if not title:
                    continue
                items.append({
                    "url": url,
                    "title": title,
                    "label_dt": "",
                })
                if len(items) >= max_items:
                    break
            if items:
                return items

    return items


def fetch_boursier_macroeconomie_dom_items(
    page_url: str,
    max_items: int,
    mode: str,
    hours_window: int,
    use_firecrawl_fallback: bool = False,
) -> List[Dict[str, str]]:
    html_text = _fetch_html_text(page_url)
    if not html_text:
        html_text = ""

    items: List[Dict[str, str]] = []
    seen = set()

    pattern = re.compile(
        r'<div class="item[^"]*">.*?'
        r'<time[^>]+class="date"[^>]+datetime="([^"]+)".*?</time>.*?'
        r'<a href="([^"]+)".*?>(.*?)</a>',
        re.S,
    )

    for datetime_attr, href, title_html in pattern.findall(html_text):
        url = href.strip()
        if not url:
            continue
        if url.startswith("/"):
            url = f"https://www.boursier.com{url}"
        if url in seen:
            continue
        seen.add(url)

        title = re.sub(r"<.*?>", "", title_html)
        title = unescape(title).strip()

        label_dt = None
        if datetime_attr:
            try:
                label_dt = datetime.fromisoformat(datetime_attr.strip())
            except Exception:
                label_dt = None

        if not _within_window(label_dt, mode, hours_window):
            continue

        items.append({
            "url": url,
            "title": title,
            "label_dt": label_dt.isoformat() if label_dt else "",
        })
        if len(items) >= max_items:
            break

    if items:
        return items

    if use_firecrawl_fallback and fetch_url_text:
        try:
            markdown = fetch_url_text(page_url)
        except Exception:
            markdown = ""
        if markdown:
            link_pattern = re.compile(r"\[([^\]]+)\]\((https?://www\.boursier\.com/[^)]+)\)")
            for title_text, href in link_pattern.findall(markdown):
                url = href.strip()
                if "/actualites/macroeconomie/" not in url and "/actions/actualites/macroeconomie/" not in url:
                    continue
                if url in seen:
                    continue
                seen.add(url)
                title = title_text.strip()
                if not title:
                    continue
                items.append({
                    "url": url,
                    "title": title,
                    "label_dt": "",
                })
                if len(items) >= max_items:
                    break
            if items:
                return items

    return items


def fetch_boursier_france_dom_items(
    page_url: str,
    max_items: int,
    mode: str,
    hours_window: int,
    use_firecrawl_fallback: bool = False,
) -> List[Dict[str, str]]:
    html_text = _fetch_html_text(page_url)
    if not html_text:
        html_text = ""

    items: List[Dict[str, str]] = []
    seen = set()

    pattern = re.compile(
        r'<div class="item[^"]*">.*?'
        r'<time[^>]+class="date"[^>]+datetime="([^"]+)".*?</time>.*?'
        r'<a href="([^"]+)".*?>(.*?)</a>',
        re.S,
    )

    for datetime_attr, href, title_html in pattern.findall(html_text):
        url = href.strip()
        if not url:
            continue
        if url.startswith("/"):
            url = f"https://www.boursier.com{url}"
        if url in seen:
            continue
        seen.add(url)

        title = re.sub(r"<.*?>", "", title_html)
        title = unescape(title).strip()

        label_dt = None
        if datetime_attr:
            try:
                label_dt = datetime.fromisoformat(datetime_attr.strip())
            except Exception:
                label_dt = None

        if not _within_window(label_dt, mode, hours_window):
            continue

        items.append({
            "url": url,
            "title": title,
            "label_dt": label_dt.isoformat() if label_dt else "",
        })
        if len(items) >= max_items:
            break

    if items:
        return items

    if use_firecrawl_fallback and fetch_url_text:
        try:
            markdown = fetch_url_text(page_url)
        except Exception:
            markdown = ""
        if markdown:
            link_pattern = re.compile(r"\[([^\]]+)\]\((https?://www\.boursier\.com/[^)]+)\)")
            for title_text, href in link_pattern.findall(markdown):
                url = href.strip()
                if "/actualites/france/" not in url and "/actions/actualites/" not in url and "/indices/actualites/" not in url:
                    continue
                if url in seen:
                    continue
                seen.add(url)
                title = title_text.strip()
                if not title:
                    continue
                items.append({
                    "url": url,
                    "title": title,
                    "label_dt": "",
                })
                if len(items) >= max_items:
                    break
            if items:
                return items

    return items


def merge_article_items(
    primary: List[Dict[str, str]],
    secondary: List[Dict[str, str]],
    limit: int,
) -> List[Dict[str, str]]:
    # Merge lists without duplicates, keep order (primary first).
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
