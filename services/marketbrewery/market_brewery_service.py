"""
===========================================
🍺 MARKET BREWERY SERVICE
===========================================
Service central exposant :
- refresh_data() : ingestion complète
- get_top_flop_weekly() : top/flop par zone (weekly)
"""

from services.marketbrewery.refresh_market_daily_close import refresh_market_daily_close
from services.marketbrewery.queries_market_metrics import (
    get_top_weekly,
    get_flop_weekly
)


def refresh_data():
    """
    Lance le refresh complet des données market
    """
    try:
        refresh_market_daily_close()
        return {"status": "success", "message": "Données market rafraîchies avec succès"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
        top = get_top_weekly(zone, limit)
        flop = get_flop_weekly(zone, limit)
        
        return {
            "status": "success",
            "top": top,
            "flop": flop
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "top": [],
            "flop": []
        }
