"""
===========================================
🔧 INIT ASSETS
===========================================
Script d'initialisation de la table assets
À lancer UNE SEULE FOIS si la table est vide
"""

from db.supabase_client import get_supabase
from services.marketbrewery.listes_market import (
    US_TOP_200,
    FR_SBF_120,
    EU_TOP_200,
    CRYPTO_TOP_30,
    INDICES,
    COMMODITIES,
    SYMBOL_TO_NAME,
    EU_FX_PAIRS,
    EU_BONDS_10Y
)


def init_assets():
    """
    Peuple la table assets avec tous les symboles
    """
    print("\n" + "="*60)
    print("🔧 INIT ASSETS — START")
    print("="*60 + "\n")
    
    supabase = get_supabase()
    
    # Vérifier si des assets existent déjà
    existing = supabase.table("assets").select("id").limit(1).execute()
    
    if existing.data:
        print("⚠️  La table 'assets' contient déjà des données.")
        confirm = input("Voulez-vous continuer et ajouter les symboles manquants ? (y/n) : ")
        if confirm.lower() != 'y':
            print("❌ Annulé")
            return
    
    # Définir les listes avec leur zone
    symbol_lists = [
        ("US", "stock", US_TOP_200),
        ("FR", "stock", FR_SBF_120),
        ("EU", "stock", EU_TOP_200),
        ("CRYPTO", "crypto", CRYPTO_TOP_30),
        ("GLOBAL", "index", INDICES),
        ("GLOBAL", "commodity", COMMODITIES),
        ("EU", "fx", EU_FX_PAIRS),
        ("EU", "bond", EU_BONDS_10Y)
    ]
    
    total_inserted = 0
    total_skipped = 0
    
    for zone, asset_type, symbols in symbol_lists:
        print(f"\n📍 Zone : {zone} / Type : {asset_type} ({len(symbols)} symboles)")
        print("-" * 60)
        
        for symbol in symbols:
            try:
                # Vérifier si le symbol existe déjà
                check = supabase.table("assets")\
                    .select("id")\
                    .eq("symbol", symbol)\
                    .limit(1)\
                    .execute()
                
                if check.data:
                    print(f"⏭️  {symbol} : déjà existant (skip)")
                    total_skipped += 1
                    continue
                
                # Déterminer la currency selon la zone / type
                currency = "USD"
                if asset_type == "bond":
                    currency = "GBP" if symbol.startswith("GB") else "EUR"
                elif zone == "FR":
                    currency = "EUR"
                elif zone == "EU":
                    # Pour l'EU, on va regarder le suffix du symbol
                    if ".PA" in symbol or ".DE" in symbol or ".AS" in symbol or ".MI" in symbol or ".BR" in symbol or ".VI" in symbol:
                        currency = "EUR"
                    elif ".L" in symbol:
                        currency = "GBP"
                    elif ".SW" in symbol:
                        currency = "CHF"
                    elif ".ST" in symbol or ".CO" in symbol or ".OL" in symbol or ".HE" in symbol:
                        currency = "EUR"  # Nordic countries
                    else:
                        currency = "USD"
                elif zone == "CRYPTO":
                    currency = "USD"
                
                # Récupérer le nom depuis le dictionnaire
                asset_name = SYMBOL_TO_NAME.get(symbol, symbol)
                
                # Insérer
                supabase.table("assets").insert({
                    "symbol": symbol,
                    "name": asset_name,
                    "asset_type": asset_type,
                    "market": zone,
                    "currency": currency,
                    "is_active": True
                }).execute()
                
                print(f"✅ {symbol} : inséré")
                total_inserted += 1
                
            except Exception as e:
                print(f"❌ {symbol} : erreur ({e})")
    
    # Résumé
    print("\n" + "="*60)
    print(f"✅ TERMINÉ : {total_inserted} insérés, {total_skipped} skippés")
    print("="*60 + "\n")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    init_assets()
