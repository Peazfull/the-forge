"""
===========================================
🍺 MARKET OPENS SERVICE
===========================================
Service central exposant :
- refresh_data() : ingestion complète (via refresh weekly/daily existant)
- get_open_top_flop() : top/flop open vs close précédent
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone

from db.supabase_client import get_supabase
from services.marketbrewery.refresh_market_daily_open import refresh_market_daily_open
from services.marketbrewery.listes_market import SYMBOL_TO_NAME


def refresh_data() -> Dict[str, str]:
    """
    Lance le refresh des données market opens (daily).
    """
    try:
        refresh_market_daily_open()
        return {"status": "success", "message": "Données market opens rafraîchies avec succès"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _get_asset_id_mapping() -> Dict[str, str]:
    supabase = get_supabase()
    try:
        response = supabase.table("assets").select("id, symbol").execute()
        return {row["symbol"]: row["id"] for row in (response.data or [])}
    except Exception:
        return {}


def _get_asset_meta_mapping() -> Dict[str, Dict[str, str]]:
    supabase = get_supabase()
    try:
        response = supabase.table("assets").select("id, symbol, name").execute()
        mapping = {}
        for row in (response.data or []):
            mapping[row["id"]] = {
                "symbol": row.get("symbol", ""),
                "name": row.get("name", ""),
            }
        return mapping
    except Exception:
        return {}


def _get_latest_open_date(supabase) -> str | None:
    response = (
        supabase.table("market_daily_open")
        .select("date")
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0].get("date")
    return None


def _get_today_open_date() -> str:
    """
    Retourne la date du jour en Europe/Paris (YYYY-MM-DD).
    """
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Paris")).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()


def _fetch_open_performances(
    symbols: List[str],
    target_date: Optional[str] = None,
) -> List[Dict[str, object]]:
    """
    Retourne toutes les performances open du jour
    (open du jour vs close de la veille), depuis market_daily_open.
    """
    supabase = get_supabase()
    asset_mapping = _get_asset_id_mapping()
    asset_meta = _get_asset_meta_mapping()
    asset_ids = [asset_mapping.get(symbol) for symbol in symbols if asset_mapping.get(symbol)]
    if not asset_ids:
        return []

    target_date = target_date or _get_latest_open_date(supabase)
    if not target_date:
        return []

    response = (
        supabase.table("market_daily_open")
        .select("asset_id, date, open_value, close_prev_value, pct_change")
        .in_("asset_id", asset_ids)
        .eq("date", target_date)
        .execute()
    )

    performances: List[Dict[str, object]] = []
    for row in (response.data or []):
        asset_id = row.get("asset_id")
        if not asset_id:
            continue
        meta = asset_meta.get(asset_id, {})
        symbol = meta.get("symbol", "")
        performances.append({
            "symbol": symbol,
            "name": SYMBOL_TO_NAME.get(symbol, symbol),
            "pct_change": float(row.get("pct_change", 0)),
            "open": float(row.get("open_value", 0)),
            "date": row.get("date"),
        })

    return performances


def get_open_top_flop(
    symbols: List[str],
    limit: int = 10,
) -> Dict[str, object]:
    """
    Retourne top/flop sur l'open du dernier jour
    (open du jour vs close de la veille).
    """
    performances = _fetch_open_performances(symbols, target_date=_get_today_open_date())
    performances.sort(key=lambda x: x["pct_change"], reverse=True)
    top = performances[:limit]
    flop = performances[-limit:][::-1]

    return {
        "status": "success",
        "top": top,
        "flop": flop,
    }


def get_open_performances(
    symbols: List[str],
) -> Dict[str, object]:
    """
    Retourne toutes les performances open du dernier jour, triées.
    """
    performances = _fetch_open_performances(symbols, target_date=_get_today_open_date())
    performances.sort(key=lambda x: x["pct_change"], reverse=True)
    return {
        "status": "success",
        "items": performances,
    }


def get_last_open_date() -> str | None:
    """
    Retourne la date du dernier point disponible.
    """
    supabase = get_supabase()
    try:
        return _get_latest_open_date(supabase)
    except Exception:
        return None
    return None


def get_today_open_date() -> str:
    return _get_today_open_date()
