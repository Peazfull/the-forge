from typing import Optional, Dict, Any, List
from datetime import datetime
from yt_dlp import YoutubeDL


def _format_date(upload_date: Optional[str], timestamp: Optional[int]) -> Optional[str]:
    if upload_date and len(upload_date) == 8:
        return f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    if timestamp:
        try:
            return datetime.utcfromtimestamp(timestamp).isoformat() + "Z"
        except Exception:
            return None
    return None


def _normalize_channel_videos_url(channel_url: str) -> str:
    if channel_url.endswith("/videos"):
        return channel_url
    return channel_url.rstrip("/") + "/videos"


def _pick_thumbnail(entry: Dict[str, Any]) -> str:
    thumbnail = entry.get("thumbnail")
    if thumbnail:
        return thumbnail
    thumbs = entry.get("thumbnails") or []
    if isinstance(thumbs, list) and thumbs:
        return thumbs[-1].get("url") or ""
    return ""


def _find_first_video(entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for entry in entries:
        if entry.get("id") and entry.get("title"):
            return entry
    return None


def get_latest_video_from_channel_ytdlp(channel_url: str) -> Optional[Dict[str, str]]:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
        "playlistend": 1,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(_normalize_channel_videos_url(channel_url), download=False)

        entries = info.get("entries") if isinstance(info, dict) else None
        if not entries:
            return None

        entry = _find_first_video(entries) or entries[0]
        video_id = entry.get("id")
        title = entry.get("title")
        published = _format_date(entry.get("upload_date"), entry.get("timestamp"))
        channel_name = (
            entry.get("uploader")
            or entry.get("channel")
            or entry.get("channel_name")
            or info.get("uploader")
            or info.get("channel")
        )
        url = entry.get("webpage_url") or entry.get("url")
        if url and not url.startswith("http"):
            url = f"https://www.youtube.com/watch?v={url}"
        if not url and video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
        thumbnail = _pick_thumbnail(entry)
        if not thumbnail and video_id:
            thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        if not video_id or not title:
            return None

        return {
            "channel_name": channel_name,
            "video_id": video_id,
            "title": title,
            "published": published or "",
            "url": url or "",
            "thumbnail": thumbnail or "",
            "source": "yt-dlp",
        }
    except Exception:
        return None
