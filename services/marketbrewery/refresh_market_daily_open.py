"""
===========================================
🔄 REFRESH MARKET DAILY OPEN
===========================================
Ingestion des opens journaliers depuis Yahoo Finance
- Récupère les 5 derniers jours (daily)
- Calcule open du jour vs close de la veille
- UPSERT dans market_daily_open
"""

from datetime import datetime, timedelta
import yfinance as yf

from db.supabase_client import get_supabase
from services.marketbrewery.listes_market import EU_TOP_200, EU_INDICES, EU_FX_PAIRS


def _get_asset_id_mapping(supabase):
    try:
        response = supabase.table("assets").select("id, symbol").execute()
        return {row["symbol"]: row["id"] for row in (response.data or [])}
    except Exception:
        return {}


def _fetch_daily_data(symbol, days=5):
    """
    Récupère les N derniers jours (daily) depuis Yahoo Finance
    Retourne une liste de dict {date, open, close}
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{days}d", interval="1d")
        if hist.empty:
            return []
        hist = hist.dropna()
        results = []
        for date, row in hist.iterrows():
            results.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "close": float(row["Close"]),
            })
        return results
    except Exception:
        return []


def _upsert_open_data(supabase, asset_id, point):
    """
    UPSERT dans market_daily_open (clé unique : asset_id, date)
    """
    supabase.table("market_daily_open").upsert({
        "asset_id": asset_id,
        "date": point["date"],
        "open_value": point["open_value"],
        "close_prev_value": point["close_prev_value"],
        "pct_change": point["pct_change"],
    }, on_conflict="asset_id,date").execute()


def _clean_old_open_data(supabase, days=10):
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    supabase.table("market_daily_open").delete().lt("date", cutoff_date).execute()


def refresh_market_daily_open():
    """
    Pipeline principal d'ingestion (daily open Europe)
    """
    supabase = get_supabase()
    asset_mapping = _get_asset_id_mapping(supabase)
    if not asset_mapping:
        return

    symbols = list(dict.fromkeys(EU_TOP_200 + EU_INDICES + EU_FX_PAIRS))

    for symbol in symbols:
        asset_id = asset_mapping.get(symbol)
        if not asset_id:
            continue
        data = _fetch_daily_data(symbol, days=5)
        if len(data) < 2:
            continue

        current = data[-1]
        previous = data[-2]
        close_prev = previous["close"]
        if close_prev == 0:
            continue

        pct_change = ((current["open"] - close_prev) / close_prev) * 100
        point = {
            "date": current["date"],
            "open_value": current["open"],
            "close_prev_value": close_prev,
            "pct_change": pct_change,
        }
        _upsert_open_data(supabase, asset_id, point)

    _clean_old_open_data(supabase, days=10)
