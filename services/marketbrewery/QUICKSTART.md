# 🚀 Market Brewery — Quick Start

## ⚡ Installation (5 minutes)

### 1️⃣ Installer les dépendances

```bash
cd "/Users/gaelpons/Desktop/The Forge"
source venv/bin/activate
pip install -r requirements.txt
```

---

### 2️⃣ Vérifier la structure Supabase

Vérifier que ces **2 tables existent** :

#### Table `assets`
```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    type TEXT, -- 'stock', 'crypto', 'index', 'commodity'
    zone TEXT, -- 'US', 'FR', 'EU', 'CRYPTO', 'GLOBAL'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Table `market_daily_close`
```sql
CREATE TABLE market_daily_close (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC NOT NULL,
    volume BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(asset_id, date)
);

-- Index pour performances
CREATE INDEX idx_market_daily_close_asset_date ON market_daily_close(asset_id, date DESC);
```

---

### 3️⃣ Initialiser les assets (si la table est vide)

```bash
python -m services.marketbrewery.init_assets
```

Ce script va peupler la table `assets` avec tous les symboles définis dans `listes_market.py`.

**Résultat attendu :**
- ~200 assets US
- ~75 assets FR
- ~75 assets EU
- ~30 assets CRYPTO
- ~10 indices
- ~8 commodities

**Total : ~400 assets**

---

### 4️⃣ Premier refresh des données

```bash
python -m services.marketbrewery.refresh_market_daily_close
```

⏱️ **Durée estimée :** 3-5 minutes (selon Yahoo Finance)

**Ce qui se passe :**
- Pour chaque symbol, récupération des 8 derniers daily close
- UPSERT dans `market_daily_close`
- Nettoyage des données > J-10

---

### 5️⃣ Lancer Streamlit

```bash
streamlit run app.py
```

**Dans la sidebar :**
- Cliquer sur **"vue5"** (ou le nom de votre page Market Brewery)

**Vous devriez voir :**
- 🍺 Market Brewery — Market Screener
- Sections US / FR / EU / Crypto
- Top/Flop Daily et Weekly

---

## ✅ Checklist de validation

- [ ] `pip install yfinance pandas` réussi
- [ ] Table `assets` créée dans Supabase
- [ ] Table `market_daily_close` créée dans Supabase
- [ ] `init_assets.py` exécuté → ~400 assets insérés
- [ ] `refresh_market_daily_close.py` exécuté → données ingérées
- [ ] Streamlit lancé → vue5.py affiche les données

---

## 🔄 Usage quotidien

### Option 1 : Refresh manuel (depuis Streamlit)

1. Ouvrir `vue5.py` dans Streamlit
2. Cliquer sur **"🔄 Refresh Market Data"**
3. Attendre la fin (~2-3 min)
4. Les tableaux se rafraîchissent automatiquement

### Option 2 : Refresh automatique (cron)

Ajouter dans votre `crontab` :

```bash
# Tous les jours à 16h (après clôture US)
0 16 * * * cd /Users/gaelpons/Desktop/The\ Forge && source venv/bin/activate && python -m services.marketbrewery.refresh_market_daily_close >> logs/market_refresh.log 2>&1
```

---

## 🐛 Troubleshooting

### Erreur : "Table 'assets' does not exist"
→ Créer les tables dans Supabase (voir étape 2)

### Erreur : "No module named 'yfinance'"
```bash
pip install yfinance pandas
```

### Aucune donnée affichée dans Streamlit
→ Vérifier que `refresh_market_daily_close.py` a bien tourné
→ Vérifier les logs pour des erreurs Yahoo Finance

### Symboles non trouvés dans assets
→ Relancer `init_assets.py` pour ajouter les manquants

### Performance lente
→ Yahoo Finance peut être lent aux heures de pointe
→ Lancer le refresh en dehors des heures US (16h-18h EST)

---

## 📞 Support

En cas de problème :
1. Vérifier les logs dans le terminal
2. Vérifier la connexion Supabase (page d'accueil de The Forge)
3. Tester Yahoo Finance manuellement :
   ```python
   import yfinance as yf
   ticker = yf.Ticker("AAPL")
   print(ticker.history(period="5d"))
   ```

---

**Enjoy! 🍺**
