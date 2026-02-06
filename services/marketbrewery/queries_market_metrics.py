"""
===========================================
📊 QUERIES MARKET METRICS
===========================================
Fonctions de lecture des top / flop par zone
Lecture depuis la table market_top_flop (pré-calculés)
"""

from db.supabase_client import get_supabase


def _get_latest_date_ref(zone, perf_type):
    supabase = get_supabase()
    response = (
        supabase.table("market_top_flop")
        .select("date_ref")
        .eq("zone", zone)
        .eq("type", perf_type)
        .order("date_ref", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0].get("date_ref")
    return None




def get_top_weekly(zone, limit=10):
    """
    Top N weekly performers pour une zone
    Lecture depuis market_top_flop
    """
    supabase = get_supabase()
    
    try:
        latest_date = _get_latest_date_ref(zone, "top")
        if not latest_date:
            return []
        response = supabase.table("market_top_flop")\
            .select("symbol, asset_name, pct_change, close_value, date_ref")\
            .eq("zone", zone)\
            .eq("type", "top")\
            .eq("date_ref", latest_date)\
            .order("rank", desc=False)\
            .limit(limit)\
            .execute()
        
        results = []
        seen_symbols = set()
        for row in response.data:
            symbol = row.get("symbol")
            if not symbol or symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            results.append({
                "symbol": symbol,
                "name": row.get("asset_name", symbol),
                "pct_change": float(row["pct_change"]),
                "close": float(row["close_value"]),
                "date": row["date_ref"],
                "zone": zone
            })
        
        return results
        
    except Exception as e:
        print(f"Erreur get_top_weekly : {e}")
        return []


def get_flop_weekly(zone, limit=10):
    """
    Flop N weekly performers pour une zone
    Lecture depuis market_top_flop
    """
    supabase = get_supabase()
    
    try:
        latest_date = _get_latest_date_ref(zone, "flop")
        if not latest_date:
            return []
        response = supabase.table("market_top_flop")\
            .select("symbol, asset_name, pct_change, close_value, date_ref")\
            .eq("zone", zone)\
            .eq("type", "flop")\
            .eq("date_ref", latest_date)\
            .order("rank", desc=False)\
            .limit(limit)\
            .execute()
        
        results = []
        seen_symbols = set()
        for row in response.data:
            symbol = row.get("symbol")
            if not symbol or symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            results.append({
                "symbol": symbol,
                "name": row.get("asset_name", symbol),
                "pct_change": float(row["pct_change"]),
                "close": float(row["close_value"]),
                "date": row["date_ref"],
                "zone": zone
            })
        
        return results
        
    except Exception as e:
        print(f"Erreur get_flop_weekly : {e}")
        return []


# ============================================
# MAIN (pour tests)
# ============================================

if __name__ == "__main__":
    print("🇺🇸 US — Top 10 Weekly")
    print(get_top_weekly("US", 10))
    
    print("\n🇺🇸 US — Flop 10 Weekly")
    print(get_flop_weekly("US", 10))
