"""
===========================================
🔄 REFRESH MARKET WEEKLY CLOSE
===========================================
Ingestion des weekly close depuis Yahoo Finance
- Récupère les 8 dernières semaines (interval 1wk)
- Calcule close semaine N vs close N-1
- UPSERT dans market_weekly_close
"""

from datetime import datetime, timedelta
import yfinance as yf

from db.supabase_client import get_supabase
from services.marketbrewery.listes_market import (
    US_TOP_200,
    FR_SBF_120,
    EU_TOP_200,
    CRYPTO_TOP_30,
    INDICES,
)


def _get_asset_id_mapping(supabase):
    try:
        response = supabase.table("assets").select("id, symbol").execute()
        return {row["symbol"]: row["id"] for row in (response.data or [])}
    except Exception:
        return {}


def _fetch_weekly_closes(symbol, weeks=8):
    """
    Récupère les N dernières semaines (weekly) depuis Yahoo Finance.
    Retourne une liste de dict {date, close}.
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{weeks}wk", interval="1wk")
        if hist.empty:
            return []
        hist = hist[["Close"]].dropna()
        results = []
        for date, row in hist.iterrows():
            results.append({
                "date": date.strftime("%Y-%m-%d"),
                "close": float(row["Close"]),
            })
        return results
    except Exception:
        return []


def _upsert_weekly_close(supabase, asset_id, point):
    supabase.table("market_weekly_close").upsert({
        "asset_id": asset_id,
        "date": point["date"],
        "close_value": point["close_value"],
        "close_prev_value": point["close_prev_value"],
        "pct_change": point["pct_change"],
    }, on_conflict="asset_id,date").execute()


def _clean_old_weekly_close(supabase, weeks=12):
    cutoff_date = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y-%m-%d")
    supabase.table("market_weekly_close").delete().lt("date", cutoff_date).execute()


def refresh_market_weekly_close():
    supabase = get_supabase()
    asset_mapping = _get_asset_id_mapping(supabase)
    if not asset_mapping:
        return

    symbols = list(dict.fromkeys(
        US_TOP_200 + FR_SBF_120 + EU_TOP_200 + CRYPTO_TOP_30 + INDICES
    ))

    for symbol in symbols:
        asset_id = asset_mapping.get(symbol)
        if not asset_id:
            continue

        weekly = _fetch_weekly_closes(symbol, weeks=8)
        if len(weekly) < 2:
            continue

        close_value = weekly[-1]["close"]
        close_prev = weekly[-2]["close"]
        if close_prev == 0:
            continue

        pct_change = ((close_value - close_prev) / close_prev) * 100
        point = {
            "date": weekly[-1]["date"],
            "close_value": close_value,
            "close_prev_value": close_prev,
            "pct_change": pct_change,
        }
        _upsert_weekly_close(supabase, asset_id, point)

    _clean_old_weekly_close(supabase, weeks=12)
