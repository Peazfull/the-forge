from typing import List, Dict
from db.supabase_client import get_supabase

TABLE_NAME = "youtube_channels"


def load_channels() -> List[Dict[str, object]]:
    try:
        supabase = get_supabase()
        resp = supabase.table(TABLE_NAME).select("url,name,enabled").order("id").execute()
        data = resp.data or []
        cleaned = []
        for item in data:
            if not isinstance(item, dict):
                continue
            cleaned.append({
                "url": item.get("url", "") or "",
                "name": item.get("name", "") or "",
                "enabled": bool(item.get("enabled", True)),
            })
        return cleaned
    except Exception:
        return []


def save_channels(channels: List[Dict[str, object]]) -> None:
    try:
        supabase = get_supabase()
        # Suppression complète de toutes les chaînes existantes
        supabase.table(TABLE_NAME).delete().gte("id", 0).execute()
        
        # Filtrer et réinsérer uniquement les chaînes avec URL non vide
        rows = []
        for item in channels:
            if not isinstance(item, dict):
                continue
            url = (item.get("url") or "").strip()
            # Ne sauvegarder que si l'URL n'est pas vide
            if url:
                rows.append({
                    "url": url,
                    "name": item.get("name", "") or "",
                    "enabled": bool(item.get("enabled", True)),
                })
        if rows:
            supabase.table(TABLE_NAME).insert(rows).execute()
    except Exception:
        return
