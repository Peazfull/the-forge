"""
===========================================
🔄 REFRESH MARKET DAILY OPEN
===========================================
Ingestion des opens journaliers depuis Yahoo Finance
- Récupère les 5 derniers jours (daily)
- Calcule open du jour vs close de la veille
- UPSERT dans market_daily_open
"""

from datetime import datetime, timedelta, timezone, time as dtime
import yfinance as yf

from db.supabase_client import get_supabase
from services.marketbrewery.listes_market import (
    EU_TOP_200,
    FR_SBF_120,
    EU_INDICES,
    EU_FX_PAIRS,
    COMMODITIES_MAJOR,
    CRYPTO_MAJOR,
    EU_BONDS_10Y,
)


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
        # Ne conserver que Open/Close (Volume peut être NaN sur les bonds)
        hist = hist[["Open", "Close"]].dropna()
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


def _get_today_paris_date() -> str:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Paris")).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()


def _fetch_intraday_open(symbol: str, target_date: str) -> float | None:
    """
    Récupère l'open du candle 09:00–09:15 (Europe/Paris) si dispo.
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d", interval="15m")
        if hist.empty:
            return None
        hist = hist[["Open"]].dropna()
        if hist.empty:
            return None

        # Normaliser en timezone Europe/Paris pour filtrer 09:00–09:15
        try:
            from zoneinfo import ZoneInfo
            tz_paris = ZoneInfo("Europe/Paris")
            idx = hist.index
            if idx.tz is None:
                idx = idx.tz_localize(timezone.utc)
            idx = idx.tz_convert(tz_paris)
        except Exception:
            idx = hist.index

        target_dt = datetime.fromisoformat(target_date)
        start = datetime.combine(target_dt.date(), dtime(9, 0))
        end = datetime.combine(target_dt.date(), dtime(9, 15))

        # Filtrer sur la fenêtre 09:00–09:15
        for i, ts in enumerate(idx):
            if start <= ts.replace(tzinfo=None) < end:
                return float(hist.iloc[i]["Open"])

        return None
    except Exception:
        return None


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

    symbols = list(dict.fromkeys(
        EU_TOP_200 + FR_SBF_120 + EU_INDICES + EU_FX_PAIRS + COMMODITIES_MAJOR + CRYPTO_MAJOR + EU_BONDS_10Y
    ))

    target_date = _get_today_paris_date()

    for symbol in symbols:
        asset_id = asset_mapping.get(symbol)
        if not asset_id:
            continue

        daily_data = _fetch_daily_data(symbol, days=5)
        if len(daily_data) < 2:
            continue

        close_prev = daily_data[-2]["close"]
        if close_prev == 0:
            continue

        # 1) Open M15 (09:00–09:15) si dispo
        open_value = _fetch_intraday_open(symbol, target_date)
        # 2) Fallback sur open daily du jour si dispo
        if open_value is None:
            if daily_data[-1]["date"] != target_date:
                continue
            open_value = daily_data[-1]["open"]

        pct_change = ((open_value - close_prev) / close_prev) * 100
        point = {
            "date": target_date,
            "open_value": open_value,
            "close_prev_value": close_prev,
            "pct_change": pct_change,
        }
        _upsert_open_data(supabase, asset_id, point)

    _clean_old_open_data(supabase, days=10)
