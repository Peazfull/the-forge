"""
===========================================
🍺 MARKET CLOSE SERVICE
===========================================
Service central exposant :
- refresh_data() : ingestion daily close
- get_close_top_flop() : top/flop daily close
"""

from typing import Dict, List
from datetime import datetime, timedelta

from db.supabase_client import get_supabase
from services.marketbrewery.refresh_market_daily_close_daily import refresh_market_daily_close_daily
from services.marketbrewery.listes_market import SYMBOL_TO_NAME


def refresh_data() -> Dict[str, str]:
    """
    Lance le refresh des données market close (daily).
    """
    try:
        refresh_market_daily_close_daily()
        return {"status": "success", "message": "Données market close rafraîchies avec succès"}
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


def _get_latest_close_date(supabase) -> str | None:
    response = (
        supabase.table("market_daily_close_daily")
        .select("date")
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0].get("date")
    return None


def _fetch_close_performances(symbols: List[str]) -> List[Dict[str, object]]:
    """
    Retourne toutes les performances close (daily),
    en gardant la dernière valeur disponible par asset sur 10 jours.
    """
    supabase = get_supabase()
    asset_mapping = _get_asset_id_mapping()
    asset_meta = _get_asset_meta_mapping()
    asset_ids = [asset_mapping.get(symbol) for symbol in symbols if asset_mapping.get(symbol)]
    if not asset_ids:
        return []

    cutoff = (datetime.utcnow() - timedelta(days=10)).date().isoformat()
    response = (
        supabase.table("market_daily_close_daily")
        .select("asset_id, date, close_value, close_prev_value, pct_change")
        .in_("asset_id", asset_ids)
        .gte("date", cutoff)
        .order("date", desc=True)
        .execute()
    )

    performances: List[Dict[str, object]] = []
    seen_asset_ids = set()
    for row in (response.data or []):
        asset_id = row.get("asset_id")
        if not asset_id or asset_id in seen_asset_ids:
            continue
        seen_asset_ids.add(asset_id)
        meta = asset_meta.get(asset_id, {})
        symbol = meta.get("symbol", "")
        performances.append({
            "symbol": symbol,
            "name": SYMBOL_TO_NAME.get(symbol, symbol),
            "pct_change": float(row.get("pct_change", 0)),
            "close": float(row.get("close_value", 0)),
            "date": row.get("date"),
        })

    return performances


def get_close_top_flop(
    symbols: List[str],
    limit: int = 10,
) -> Dict[str, object]:
    """
    Retourne top/flop daily close.
    """
    performances = _fetch_close_performances(symbols)

    positives = [p for p in performances if p.get("pct_change", 0) > 0]
    negatives = [p for p in performances if p.get("pct_change", 0) < 0]

    positives.sort(key=lambda x: x.get("pct_change", 0), reverse=True)
    negatives.sort(key=lambda x: x.get("pct_change", 0))

    top = positives[:limit]
    flop = negatives[:limit]

    return {
        "status": "success",
        "top": top,
        "flop": flop,
    }


def get_close_performances(
    symbols: List[str],
) -> Dict[str, object]:
    """
    Retourne toutes les performances close, triées.
    """
    performances = _fetch_close_performances(symbols)
    performances.sort(key=lambda x: x.get("pct_change", 0), reverse=True)
    return {
        "status": "success",
        "items": performances,
    }


def get_last_close_date() -> str | None:
    """
    Retourne la date du dernier point disponible.
    """
    supabase = get_supabase()
    try:
        return _get_latest_close_date(supabase)
    except Exception:
        return None
    return None
