"""
===========================================
🔄 REFRESH MARKET WEEKLY CLOSE
===========================================
Ingestion des weekly close depuis Yahoo Finance
- Récupère les 3 dernières semaines
- UPSERT dans market_daily_close
- Nettoie les données > 4 semaines
"""

import yfinance as yf
from datetime import datetime, timedelta
from db.supabase_client import get_supabase
from services.marketbrewery.listes_market import (
    US_TOP_200,
    FR_SBF_120,
    EU_TOP_200,
    CRYPTO_TOP_30,
    INDICES,
    COMMODITIES,
    EU_FX_PAIRS
)


def get_all_symbols():
    """Retourne tous les symboles à ingérer"""
    return {
        "US": US_TOP_200,
        "FR": FR_SBF_120,
        "EU": EU_TOP_200,
        "CRYPTO": CRYPTO_TOP_30,
        "INDICES": INDICES,
        "COMMODITIES": COMMODITIES,
        "FX_EU": EU_FX_PAIRS
    }


def get_asset_id_mapping(supabase):
    """
    Crée un mapping symbol → asset_id
    """
    print("📊 Chargement des assets depuis la DB...")
    
    try:
        response = supabase.table("assets").select("id, symbol").execute()
        
        mapping = {asset["symbol"]: asset["id"] for asset in response.data}
        
        print(f"✅ {len(mapping)} assets chargés")
        return mapping
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement des assets : {e}")
        return {}


def get_asset_meta_mapping(supabase):
    """
    Crée un mapping asset_id → name
    """
    try:
        response = supabase.table("assets").select("id, name").execute()
        return {asset["id"]: asset.get("name", "") for asset in (response.data or [])}
    except Exception as e:
        print(f"❌ Erreur lors du chargement des noms assets : {e}")
        return {}


def fetch_yahoo_data(symbol, weeks=3):
    """
    Récupère les N dernières weekly close depuis Yahoo Finance
    Retourne une liste de dict {date, open, high, low, close, volume}
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Récupérer les données weekly directement
        hist = ticker.history(period=f"{weeks}wk", interval="1wk")
        
        if hist.empty:
            return []
        
        # Filtrer seulement les lignes avec des données complètes
        hist = hist.dropna()
        
        results = []
        for date, row in hist.iterrows():
            results.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })
        
        return results
        
    except Exception as e:
        print(f"⚠️  Erreur Yahoo Finance pour {symbol} : {e}")
        return []


def upsert_market_data(supabase, asset_id, data_points):
    """
    UPSERT des données dans market_daily_close
    Clé unique : (asset_id, date)
    """
    if not data_points:
        return
    
    for point in data_points:
        try:
            supabase.table("market_daily_close").upsert({
                "asset_id": asset_id,
                "date": point["date"],
                "open": point["open"],
                "high": point["high"],
                "low": point["low"],
                "close": point["close"],
                "volume": point["volume"]
            }).execute()
            
        except Exception as e:
            print(f"❌ Erreur UPSERT pour asset_id={asset_id}, date={point['date']} : {e}")


def clean_old_data(supabase):
    """
    Nettoie les données antérieures à 4 semaines
    """
    print("\n🧹 Nettoyage des données anciennes...")
    
    try:
        cutoff_date = (datetime.now() - timedelta(weeks=4)).strftime("%Y-%m-%d")
        
        response = supabase.table("market_daily_close")\
            .delete()\
            .lt("date", cutoff_date)\
            .execute()
        
        print(f"✅ Données antérieures à {cutoff_date} supprimées")
        
    except Exception as e:
        print(f"❌ Erreur nettoyage : {e}")


def clean_old_top_flop(supabase, days=30):
    """
    Nettoie les anciens top/flop au-delà d'une fenêtre glissante.
    """
    print("\n🧹 Nettoyage des top/flop anciens...")
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        supabase.table("market_top_flop").delete().lt("date_ref", cutoff_date).execute()
        print(f"✅ Top/Flop antérieurs à {cutoff_date} supprimés")
    except Exception as e:
        print(f"❌ Erreur nettoyage top/flop : {e}")


def calculate_and_store_top_flop(supabase, asset_mapping):
    """
    Calcule les top/flop pour chaque zone et les stocke dans market_top_flop
    """
    print("\n📊 Calcul des top/flop par zone...")
    
    from services.marketbrewery.listes_market import (
        US_TOP_200, FR_SBF_120, EU_TOP_200, CRYPTO_TOP_30
    )
    
    zones = {
        "US": US_TOP_200,
        "FR": FR_SBF_120,
        "EU": EU_TOP_200,
        "CRYPTO": CRYPTO_TOP_30
    }
    
    refresh_date = datetime.now().strftime("%Y-%m-%d")
    # Reset complet pour éviter toute accumulation
    try:
        supabase.table("market_top_flop").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    except Exception as e:
        print(f"❌ Erreur reset market_top_flop : {e}")
    
    asset_meta = get_asset_meta_mapping(supabase)

    for zone_name, symbols in zones.items():
        print(f"\n📍 Zone : {zone_name}")
        
        performances = []
        
        for symbol in symbols:
            if symbol not in asset_mapping:
                continue
            
            asset_id = asset_mapping[symbol]
            
            try:
                # Récupérer les 2 dernières semaines
                data_response = supabase.table("market_daily_close")\
                    .select("date, close")\
                    .eq("asset_id", asset_id)\
                    .order("date", desc=True)\
                    .limit(2)\
                    .execute()
                
                if len(data_response.data) < 2:
                    continue
                
                close_current = data_response.data[0]["close"]
                close_previous = data_response.data[1]["close"]
                date_ref = data_response.data[0]["date"]
                
                pct_change = ((close_current - close_previous) / close_previous) * 100
                
                # Récupérer le nom de l'asset depuis la table assets
                asset_name = asset_meta.get(asset_id, "") or symbol
                
                performances.append({
                    "symbol": symbol,
                    "name": asset_name,
                    "pct_change": pct_change,
                    "close": close_current,
                    "date": date_ref
                })
                
            except Exception as e:
                continue
        
        # Trier par performance
        performances.sort(key=lambda x: x["pct_change"], reverse=True)
        
        # Top 10 : les N meilleures performances
        top_10 = performances[:10]
        top_symbols = {perf["symbol"] for perf in top_10}
        for rank, perf in enumerate(top_10, start=1):
            try:
                supabase.table("market_top_flop").insert({
                    "zone": zone_name,
                    "type": "top",
                    "rank": rank,
                    "symbol": perf["symbol"],
                    "asset_name": perf["name"],
                    "pct_change": perf["pct_change"],
                    "close_value": perf["close"],
                    "date_ref": perf["date"],
                    "refresh_date": refresh_date
                }).execute()
            except Exception as e:
                print(f"❌ Erreur insert top {zone_name} : {e}")
        
        # Flop 10 : les N pires performances, sans doublons avec le top
        flop_candidates = sorted(performances, key=lambda x: x["pct_change"])
        flop_10 = []
        for perf in flop_candidates:
            if perf["symbol"] in top_symbols:
                continue
            flop_10.append(perf)
            if len(flop_10) >= 10:
                break
        for rank, perf in enumerate(flop_10, start=1):
            try:
                supabase.table("market_top_flop").insert({
                    "zone": zone_name,
                    "type": "flop",
                    "rank": rank,
                    "symbol": perf["symbol"],
                    "asset_name": perf["name"],
                    "pct_change": perf["pct_change"],
                    "close_value": perf["close"],
                    "date_ref": perf["date"],
                    "refresh_date": refresh_date
                }).execute()
            except Exception as e:
                print(f"❌ Erreur insert flop {zone_name} : {e}")
        
        print(f"✅ Top/Flop {zone_name} stockés")
    
    print("\n✅ Tous les top/flop calculés et stockés")


def refresh_market_daily_close():
    """
    Pipeline principal d'ingestion (weekly data)
    """
    print("\n" + "="*60)
    print("🔄 REFRESH MARKET WEEKLY CLOSE — START")
    print("="*60 + "\n")
    
    supabase = get_supabase()
    
    # 1️⃣ Charger le mapping asset_id
    asset_mapping = get_asset_id_mapping(supabase)
    
    if not asset_mapping:
        print("❌ Aucun asset trouvé en DB. Arrêt.")
        return
    
    # 2️⃣ Charger tous les symboles
    all_symbols = get_all_symbols()
    
    total_processed = 0
    total_success = 0
    
    # 3️⃣ Pour chaque zone, ingérer les données
    for zone, symbols in all_symbols.items():
        print(f"\n📍 Zone : {zone} ({len(symbols)} symboles)")
        print("-" * 60)
        
        for symbol in symbols:
            # Vérifier que le symbol existe dans assets
            if symbol not in asset_mapping:
                print(f"⚠️  {symbol} : non trouvé dans assets (skip)")
                continue
            
            asset_id = asset_mapping[symbol]
            
            # Récupérer les données Yahoo
            data = fetch_yahoo_data(symbol)
            
            if data:
                upsert_market_data(supabase, asset_id, data)
                print(f"✅ {symbol} : {len(data)} jours ingérés")
                total_success += 1
            else:
                print(f"⚠️  {symbol} : aucune donnée")
            
            total_processed += 1
    
    # 4️⃣ Nettoyage
    clean_old_data(supabase)
    
    # 5️⃣ Calcul et stockage des top/flop
    calculate_and_store_top_flop(supabase, asset_mapping)
    
    # 6️⃣ Résumé
    print("\n" + "="*60)
    print(f"✅ TERMINÉ : {total_success}/{total_processed} symboles ingérés")
    print("="*60 + "\n")


# ============================================
# MAIN (pour tests)
# ============================================

if __name__ == "__main__":
    refresh_market_daily_close()
