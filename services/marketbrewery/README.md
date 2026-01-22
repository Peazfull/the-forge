# 🍺 Market Brewery

## Vue d'ensemble

**Market Brewery** est le module de curation et screening de données financières de **The Forge**.

Il collecte, stocke et analyse les performances de marchés financiers (actions US, FR, EU, crypto) basées sur les **daily close** officiels.

---

## Architecture

### 📂 Fichiers

```
services/marketbrewery/
├── listes_market.py              # Listes d'actifs (US, FR, EU, Crypto, Indices, Commodities)
├── refresh_market_daily_close.py # Pipeline d'ingestion Yahoo Finance
├── queries_market_metrics.py     # Calculs top/flop par zone
├── market_brewery_service.py     # Service central (API)
└── README.md                      # Documentation
```

---

## 🗄️ Base de données (Supabase)

### Tables utilisées

#### `assets`
```sql
- id (uuid, PK)
- symbol (text, unique)
- name (text)
- type (text) -- "stock", "crypto", "index", "commodity"
- zone (text) -- "US", "FR", "EU", "CRYPTO"
```

#### `market_daily_close`
```sql
- id (uuid, PK)
- asset_id (uuid, FK → assets.id)
- date (date)
- open (numeric)
- high (numeric)
- low (numeric)
- close (numeric)
- volume (bigint)
- UNIQUE (asset_id, date)
```

⚠️ **Clé unique** : `(asset_id, date)` → permet l'UPSERT idempotent.

---

## 🔄 Ingestion des données

### Script : `refresh_market_daily_close.py`

**Rôle :**
- Charge tous les symboles depuis `listes_market.py`
- Requête Yahoo Finance (via `yfinance`)
- Récupère les **8 derniers daily close complets**
- UPSERT dans `market_daily_close`
- Nettoie les données > J-10

**Exécution manuelle :**
```bash
cd /Users/gaelpons/Desktop/The Forge
source venv/bin/activate
python -m services.marketbrewery.refresh_market_daily_close
```

**Depuis le front Streamlit :**
- Bouton "🔄 Refresh Market Data" dans `vue5.py`

---

## 📊 Calculs de performance

### Script : `queries_market_metrics.py`

**Fonctions disponibles :**

```python
get_top_daily(zone, limit=10)      # Top N daily performers
get_flop_daily(zone, limit=10)     # Flop N daily performers
get_top_weekly(zone, limit=10)     # Top N weekly performers
get_flop_weekly(zone, limit=10)    # Flop N weekly performers
```

**Zones supportées :**
- `"US"` → US_TOP_200
- `"FR"` → FR_SBF_120
- `"EU"` → EU_TOP_200
- `"CRYPTO"` → CRYPTO_TOP_30

**Formules :**
- **Daily %** = (close J-1 - close J-2) / close J-2 × 100
- **Weekly %** = (close J-1 - close J-7) / close J-7 × 100

---

## 🎯 Service central

### Script : `market_brewery_service.py`

**API unifiée pour le frontend :**

```python
from services.marketbrewery.market_brewery_service import (
    refresh_data,
    get_top_flop_daily,
    get_top_flop_weekly
)

# Refresh complet
result = refresh_data()

# Top/Flop daily pour les US
data = get_top_flop_daily("US", limit=10)
# → {"status": "success", "top": [...], "flop": [...]}

# Top/Flop weekly pour crypto
data = get_top_flop_weekly("CRYPTO", limit=10)
```

---

## 🖥️ Frontend Streamlit

### Fichier : `front/views/vue5.py`

**UX :**
- Titre : "🍺 Market Brewery — Market Screener"
- Bouton de refresh manuel
- Sections par zone (US, FR, EU, Crypto)
- Pour chaque zone :
  - Top 10 Daily / Flop 10 Daily
  - Top 10 Weekly / Flop 10 Weekly

**Affichage :**
- Tableaux légers et lisibles
- Colonnes : Symbol, % Change, Close, Date
- Tri pré-calculé (backend)

---

## 🔧 Configuration requise

### Dependencies Python

Ajoutées dans `requirements.txt` :
```
yfinance
pandas
```

### Installation
```bash
cd /Users/gaelpons/Desktop/The Forge
source venv/bin/activate
pip install -r requirements.txt
```

---

## ✅ Bonnes pratiques

1. **Idempotence** : Relancer le refresh n'écrase rien, UPSERT intelligent
2. **Pas d'intraday** : Uniquement les daily close complets (évite les données partielles)
3. **Historique limité** : 8-10 jours max pour rester rapide
4. **Logs clairs** : Chaque étape loguée dans le terminal
5. **Gestion d'erreurs** : Si Yahoo Finance échoue pour un symbol → skip, continue

---

## 🚀 Utilisation quotidienne

### Workflow recommandé

1. **Matin (après ouverture marchés US)** :
   - Clic sur "🔄 Refresh Market Data"
   - Attendre ~2-3 min (selon le nombre de symboles)
   - Les données sont rafraîchies

2. **Lecture** :
   - Parcourir les sections US / FR / EU / Crypto
   - Repérer les top/flop daily
   - Identifier les tendances weekly

3. **Automatisation (optionnel)** :
   - Créer un cron job pour `refresh_market_daily_close.py`
   - Ex : tous les jours à 16h (après clôture US)

---

## 📈 Roadmap (si extension future)

- [ ] Ajout de graphiques sparkline
- [ ] Filtres avancés (secteur, cap)
- [ ] Export CSV des résultats
- [ ] Alertes custom sur mouvements > X%
- [ ] Intégration avec brew_items (génération d'articles)

---

## 🛠️ Troubleshooting

### "Aucune donnée disponible"
→ Vérifier que la table `assets` contient bien les symboles
→ Lancer un refresh manuel

### Erreur Yahoo Finance
→ Certains symboles peuvent être temporairement indisponibles
→ Le script continue sur les autres (non-bloquant)

### Performances lentes
→ Réduire le nombre de symboles dans `listes_market.py`
→ Augmenter la limite de days dans `fetch_yahoo_data()`

---

**Auteur :** The Forge Team  
**Version :** 1.0  
**Dernière MAJ :** Janvier 2026
