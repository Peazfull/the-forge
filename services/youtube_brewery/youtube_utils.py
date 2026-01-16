import requests
import xml.etree.ElementTree as ET
from typing import Optional, Dict
from services.youtube_brewery.rss_utils import get_rss_url_from_channel_url
from services.youtube_brewery.ytdlp_utils import get_latest_video_from_channel_ytdlp


def _parse_rss_latest(rss_url: str) -> Optional[Dict[str, str]]:
    try:
        r = requests.get(rss_url, timeout=10)
        r.raise_for_status()

        root = ET.fromstring(r.text)
        entry = root.find("{http://www.w3.org/2005/Atom}entry")
        if entry is None:
            return None

        title = entry.find("{http://www.w3.org/2005/Atom}title").text
        video_id = entry.find("{http://www.youtube.com/xml/schemas/2015}videoId").text
        published = entry.find("{http://www.w3.org/2005/Atom}published").text

        channel_name = None
        author = entry.find("{http://www.w3.org/2005/Atom}author")
        if author is not None:
            name_el = author.find("{http://www.w3.org/2005/Atom}name")
            if name_el is not None:
                channel_name = name_el.text

        return {
            "channel_name": channel_name,
            "video_id": video_id,
            "title": title,
            "published": published,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "source": "rss",
        }
    except Exception:
        return None


def get_channel_name_from_url(channel_url: str) -> Optional[str]:
    rss_url = get_rss_url_from_channel_url(channel_url)
    if not rss_url:
        return None

    try:
        r = requests.get(rss_url, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        title = root.find("{http://www.w3.org/2005/Atom}title")
        if title is not None:
            return title.text.strip()
    except Exception:
        return None

    return None


def get_latest_video_from_channel(channel_url: str) -> Optional[Dict[str, str]]:
    rss_url = get_rss_url_from_channel_url(channel_url)
    if rss_url:
        rss_video = _parse_rss_latest(rss_url)
        if rss_video:
            return rss_video

    return get_latest_video_from_channel_ytdlp(channel_url)
