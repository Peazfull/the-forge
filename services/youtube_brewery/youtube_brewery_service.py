from typing import Dict, List, Optional
import time

from services.youtube_brewery.transcript_utils import fetch_video_transcript
from services.youtube_brewery.process_transcript import (
    clean_raw_text,
    merge_topics_text,
    journalist_text,
    copywriter_text,
    jsonfy_text,
)


def _format_temp_block(video: Dict[str, str], content: str) -> str:
    return (
        "=== VIDEO ===\n"
        f"Channel: {video.get('channel_name', '')}\n"
        f"Title: {video.get('title', '')}\n"
        f"Date: {video.get('published', '')}\n"
        f"URL: {video.get('url', '')}\n"
        "\n"
        f"{content.strip()}\n"
    )


def _parse_temp_block(block: str) -> Optional[Dict[str, str]]:
    if not block.strip():
        return None
    lines = block.splitlines()
    header = {}
    body_lines = []
    in_body = False
    for line in lines:
        if not in_body and line.strip() == "":
            in_body = True
            continue
        if not in_body:
            if ":" in line:
                key, value = line.split(":", 1)
                header[key.strip().lower()] = value.strip()
        else:
            body_lines.append(line)
    body_text = "\n".join(body_lines).strip()
    if not body_text:
        return None
    return {
        "channel_name": header.get("channel", ""),
        "title": header.get("title", ""),
        "published": header.get("date", ""),
        "url": header.get("url", ""),
        "body_text": body_text,
    }


def build_temp_transcripts(videos: List[Dict[str, str]]) -> Dict[str, object]:
    blocks: List[str] = []
    errors: List[str] = []
    status_log: List[str] = []
    total = len(videos)

    for idx, video in enumerate(videos, start=1):
        title = video.get("title") or "Sans titre"
        url = video.get("url") or ""
        status_log.append(f"VID {idx}/{total} · démarrage · {title}")

        if not url:
            errors.append(f"URL manquante pour {title}")
            status_log.append(f"VID {idx}/{total} · URL manquante")
            continue

        try:
            step_start = time.time()
            transcript = fetch_video_transcript(url)
            step_duration = time.time() - step_start
            status_log.append(f"VID {idx}/{total} · transcript OK ({step_duration:.1f}s)")
        except Exception as exc:
            errors.append(f"Transcript indisponible pour {title}: {exc}")
            status_log.append(f"VID {idx}/{total} · transcript NOK")
            continue

        step_start = time.time()
        cleaned = clean_raw_text(transcript)
        step_duration = time.time() - step_start
        if cleaned.get("status") != "success":
            errors.append(cleaned.get("message", "Erreur clean"))
            status_log.append(f"VID {idx}/{total} · clean NOK ({step_duration:.1f}s)")
            continue
        status_log.append(f"VID {idx}/{total} · clean OK ({step_duration:.1f}s)")

        step_start = time.time()
        merged = merge_topics_text(cleaned.get("text", ""))
        step_duration = time.time() - step_start
        if merged.get("status") != "success":
            errors.append(merged.get("message", "Erreur merge"))
            status_log.append(f"VID {idx}/{total} · merge NOK ({step_duration:.1f}s)")
            continue
        status_log.append(f"VID {idx}/{total} · merge OK ({step_duration:.1f}s)")

        step_start = time.time()
        journalist = journalist_text(merged.get("text", ""))
        step_duration = time.time() - step_start
        if journalist.get("status") != "success":
            errors.append(journalist.get("message", "Erreur journalist"))
            status_log.append(f"VID {idx}/{total} · journalist NOK ({step_duration:.1f}s)")
            continue
        status_log.append(f"VID {idx}/{total} · journalist OK ({step_duration:.1f}s)")

        step_start = time.time()
        copywritten = copywriter_text(journalist.get("text", ""))
        step_duration = time.time() - step_start
        if copywritten.get("status") != "success":
            errors.append(copywritten.get("message", "Erreur copywriter"))
            status_log.append(f"VID {idx}/{total} · copywriter NOK ({step_duration:.1f}s)")
            continue
        status_log.append(f"VID {idx}/{total} · copywriter OK ({step_duration:.1f}s)")

        blocks.append(_format_temp_block(video, copywritten.get("text", "")))
        status_log.append(f"VID {idx}/{total} · ajouté")

    temp_text = "\n\n".join(blocks).strip()

    return {
        "status": "success",
        "temp_text": temp_text,
        "errors": errors,
        "status_log": status_log,
    }


def jsonfy_temp_text(temp_text: str) -> Dict[str, object]:
    if not temp_text or not temp_text.strip():
        return {"status": "error", "message": "Texte temporaire vide", "items": []}

    blocks = [b.strip() for b in temp_text.split("=== VIDEO ===") if b.strip()]
    items = []
    errors = []

    for block in blocks:
        parsed = _parse_temp_block(block)
        if not parsed:
            continue
        json_result = jsonfy_text(parsed.get("body_text", ""))
        if json_result.get("status") != "success":
            errors.append(json_result.get("message", "Erreur JSON"))
            continue
        for item in json_result.get("items", []):
            if isinstance(item, dict):
                item["source_name"] = parsed.get("channel_name")
                item["source_link"] = parsed.get("url")
                item["source_date"] = parsed.get("published")
                item["source_raw"] = None
                items.append(item)

    return {"status": "success", "items": items, "errors": errors}
