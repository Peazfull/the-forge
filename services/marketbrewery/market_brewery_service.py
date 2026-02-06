"""
===========================================
🍺 MARKET BREWERY SERVICE
===========================================
Service central exposant :
- refresh_data() : ingestion complète
- get_top_flop_weekly() : top/flop par zone (weekly)
"""

from typing import Dict, List
from datetime import datetime, timedelta

from db.supabase_client import get_supabase
from services.marketbrewery.refresh_market_weekly_close import refresh_market_weekly_close
from services.marketbrewery.listes_market import (
    US_TOP_200,
    FR_SBF_120,
    EU_TOP_200,
    CRYPTO_TOP_30,
    INDICES,
)


def refresh_data():
    """
    Lance le refresh complet des données market
    """
    try:
        refresh_market_weekly_close()
        return {"status": "success", "message": "Données market rafraîchies avec succès"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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


def _get_latest_weekly_date(supabase) -> str | None:
    response = (
        supabase.table("market_weekly_close")
        .select("date")
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0].get("date")
    return None


def _fetch_weekly_performances(symbols: List[str], target_date: str | None = None):
    supabase = get_supabase()
    asset_mapping = _get_asset_id_mapping()
    asset_meta = _get_asset_meta_mapping()
    asset_ids = [asset_mapping.get(symbol) for symbol in symbols if asset_mapping.get(symbol)]
    if not asset_ids:
        return []

    target_date = target_date or _get_latest_weekly_date(supabase)
    if not target_date:
        return []

    response = (
        supabase.table("market_weekly_close")
        .select("asset_id, date, close_value, close_prev_value, pct_change")
        .in_("asset_id", asset_ids)
        .eq("date", target_date)
        .execute()
    )

    performances = []
    seen_symbols = set()
    for row in (response.data or []):
        asset_id = row.get("asset_id")
        if not asset_id:
            continue
        meta = asset_meta.get(asset_id, {})
        symbol = meta.get("symbol", "")
        if not symbol or symbol in seen_symbols:
            continue
        seen_symbols.add(symbol)
        name = meta.get("name") or symbol
        performances.append({
            "symbol": symbol,
            "name": name,
            "pct_change": float(row.get("pct_change", 0)),
            "close": float(row.get("close_value", 0)),
            "date": row.get("date"),
        })

    return performances


def get_last_weekly_date() -> str | None:
    supabase = get_supabase()
    try:
        return _get_latest_weekly_date(supabase)
    except Exception:
        return None


def _get_zone_symbols(zone: str) -> List[str]:
    zones = {
        "US": US_TOP_200,
        "FR": FR_SBF_120,
        "EU": EU_TOP_200,
        "CRYPTO": CRYPTO_TOP_30,
        "INDICES": INDICES,
    }
    return zones.get(zone, [])


def get_top_flop_weekly(zone="US", limit=10):
    """
    Retourne top & flop weekly pour une zone
    
    Args:
        zone: "US", "FR", "EU", "CRYPTO"
        limit: nombre de résultats (défaut 10)
    
    Returns:
        {"top": [...], "flop": [...]}
    """
    try:
        symbols = _get_zone_symbols(zone)
        performances = _fetch_weekly_performances(symbols)
        performances.sort(key=lambda x: x.get("pct_change", 0), reverse=True)

        top_sorted = performances[:limit]
        flop_sorted = list(reversed(performances[-limit:]))

        return {
            "status": "success",
            "top": top_sorted,
            "flop": flop_sorted
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "top": [],
            "flop": []
        }
