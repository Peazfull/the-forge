"""
===========================================
🧪 TEST INSTALLATION MARKET BREWERY
===========================================
Script de validation de l'installation
"""

import sys


def test_imports():
    """Test des imports Python"""
    print("\n" + "="*60)
    print("🧪 TEST 1/5 : Imports Python")
    print("="*60)
    
    try:
        import yfinance
        print("✅ yfinance installé")
    except ImportError:
        print("❌ yfinance manquant → pip install yfinance")
        return False
    
    try:
        import pandas
        print("✅ pandas installé")
    except ImportError:
        print("❌ pandas manquant → pip install pandas")
        return False
    
    try:
        from db.supabase_client import get_supabase
        print("✅ supabase_client importé")
    except ImportError as e:
        print(f"❌ Erreur import supabase_client : {e}")
        return False
    
    return True


def test_supabase_connection():
    """Test connexion Supabase"""
    print("\n" + "="*60)
    print("🧪 TEST 2/5 : Connexion Supabase")
    print("="*60)
    
    try:
        from db.supabase_client import get_supabase
        supabase = get_supabase()
        
        # Test simple
        response = supabase.table("assets").select("id").limit(1).execute()
        print("✅ Connexion Supabase OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur connexion Supabase : {e}")
        return False


def test_assets_table():
    """Test table assets"""
    print("\n" + "="*60)
    print("🧪 TEST 3/5 : Table 'assets'")
    print("="*60)
    
    try:
        from db.supabase_client import get_supabase
        supabase = get_supabase()
        
        response = supabase.table("assets").select("id, symbol").limit(5).execute()
        
        if not response.data:
            print("⚠️  Table 'assets' vide → lancer init_assets.py")
            return False
        
        print(f"✅ Table 'assets' OK ({len(response.data)} assets trouvés en échantillon)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur table 'assets' : {e}")
        print("   → Vérifier que la table existe dans Supabase")
        return False


def test_market_daily_close_table():
    """Test table market_daily_close"""
    print("\n" + "="*60)
    print("🧪 TEST 4/5 : Table 'market_daily_close'")
    print("="*60)
    
    try:
        from db.supabase_client import get_supabase
        supabase = get_supabase()
        
        response = supabase.table("market_daily_close").select("id").limit(1).execute()
        
        if not response.data:
            print("⚠️  Table 'market_daily_close' vide → lancer refresh_market_daily_close.py")
            return True  # Table existe mais vide = OK
        
        print(f"✅ Table 'market_daily_close' OK (contient des données)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur table 'market_daily_close' : {e}")
        print("   → Vérifier que la table existe dans Supabase")
        return False


def test_yahoo_finance():
    """Test Yahoo Finance API"""
    print("\n" + "="*60)
    print("🧪 TEST 5/5 : Yahoo Finance API")
    print("="*60)
    
    try:
        import yfinance as yf
        
        ticker = yf.Ticker("AAPL")
        hist = ticker.history(period="5d")
        
        if hist.empty:
            print("❌ Aucune donnée retournée par Yahoo Finance")
            return False
        
        print(f"✅ Yahoo Finance OK (récupéré {len(hist)} jours pour AAPL)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur Yahoo Finance : {e}")
        return False


def main():
    """Lance tous les tests"""
    print("\n" + "🍺"*30)
    print("MARKET BREWERY — TEST D'INSTALLATION")
    print("🍺"*30)
    
    results = []
    
    results.append(("Imports Python", test_imports()))
    results.append(("Connexion Supabase", test_supabase_connection()))
    results.append(("Table assets", test_assets_table()))
    results.append(("Table market_daily_close", test_market_daily_close_table()))
    results.append(("Yahoo Finance API", test_yahoo_finance()))
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print("\n" + "="*60)
    if passed == total:
        print(f"🎉 TOUS LES TESTS PASSÉS ({passed}/{total})")
        print("="*60)
        print("\n✅ Market Brewery est prêt à l'emploi !")
        print("\n📝 Prochaines étapes :")
        print("   1. Lancer : python -m services.marketbrewery.refresh_market_daily_close")
        print("   2. Ouvrir Streamlit et aller sur vue5.py")
        return 0
    else:
        print(f"⚠️  {passed}/{total} TESTS RÉUSSIS")
        print("="*60)
        print("\n❌ Des problèmes doivent être résolus avant utilisation.")
        print("\n📖 Consulter : services/marketbrewery/QUICKSTART.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
