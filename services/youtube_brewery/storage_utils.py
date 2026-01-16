import json
import os
from typing import List, Dict


def _data_file_path() -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "youtube_channels.json")


def load_channels() -> List[Dict[str, object]]:
    path = _data_file_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        cleaned = []
        for item in data:
            if not isinstance(item, dict):
                continue
            cleaned.append({
                "url": item.get("url", ""),
                "name": item.get("name", ""),
                "enabled": bool(item.get("enabled", True)),
            })
        return cleaned
    except Exception:
        return []


def save_channels(channels: List[Dict[str, object]]) -> None:
    path = _data_file_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)
