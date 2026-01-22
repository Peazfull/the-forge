"""
===========================================
📊 QUERIES MARKET METRICS
===========================================
Fonctions de calcul top / flop par zone
- Weekly % = close week actuelle vs week précédente
"""

from db.supabase_client import get_supabase
from services.marketbrewery.listes_market import (
    US_TOP_200,
    FR_SBF_120,
    EU_TOP_200,
    CRYPTO_TOP_30
)




def get_weekly_performance(supabase, symbols, zone_name):
    """
    Calcule la performance weekly pour une liste de symboles
    Retourne une liste de dicts triés
    """
    results = []
    
    for symbol in symbols:
        try:
            # Récupérer l'asset_id
            asset_response = supabase.table("assets")\
                .select("id")\
                .eq("symbol", symbol)\
                .limit(1)\
                .execute()
            
            if not asset_response.data:
                continue
            
            asset_id = asset_response.data[0]["id"]
            
            # Récupérer les 2 dernières semaines
            data_response = supabase.table("market_daily_close")\
                .select("date, close")\
                .eq("asset_id", asset_id)\
                .order("date", desc=True)\
                .limit(2)\
                .execute()
            
            if len(data_response.data) < 2:
                continue
            
            close_week_actuelle = data_response.data[0]["close"]
            close_week_precedente = data_response.data[1]["close"]
            date_actuelle = data_response.data[0]["date"]
            
            # Calcul %
            pct_change = ((close_week_actuelle - close_week_precedente) / close_week_precedente) * 100
            
            results.append({
                "symbol": symbol,
                "close": close_week_actuelle,
                "pct_change": pct_change,
                "date": date_actuelle,
                "zone": zone_name
            })
            
        except Exception as e:
            continue
    
    # Trier par performance décroissante
    results.sort(key=lambda x: x["pct_change"], reverse=True)
    
    return results


def get_top_weekly(zone, limit=10):
    """
    Top N weekly performers pour une zone
    """
    supabase = get_supabase()
    
    zone_mapping = {
        "US": US_TOP_200,
        "FR": FR_SBF_120,
        "EU": EU_TOP_200,
        "CRYPTO": CRYPTO_TOP_30
    }
    
    if zone not in zone_mapping:
        return []
    
    symbols = zone_mapping[zone]
    all_perf = get_weekly_performance(supabase, symbols, zone)
    
    return all_perf[:limit]


def get_flop_weekly(zone, limit=10):
    """
    Flop N weekly performers pour une zone
    """
    supabase = get_supabase()
    
    zone_mapping = {
        "US": US_TOP_200,
        "FR": FR_SBF_120,
        "EU": EU_TOP_200,
        "CRYPTO": CRYPTO_TOP_30
    }
    
    if zone not in zone_mapping:
        return []
    
    symbols = zone_mapping[zone]
    all_perf = get_weekly_performance(supabase, symbols, zone)
    
    # Inverse pour avoir les pires
    return all_perf[-limit:][::-1]


# ============================================
# MAIN (pour tests)
# ============================================

if __name__ == "__main__":
    print("🇺🇸 US — Top 10 Weekly")
    print(get_top_weekly("US", 10))
    
    print("\n🇺🇸 US — Flop 10 Weekly")
    print(get_flop_weekly("US", 10))
