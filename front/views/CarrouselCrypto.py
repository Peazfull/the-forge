import streamlit as st
from db.supabase_client import get_supabase

# ======================================================
# PAGE CONFIG
# ======================================================

st.title("₿ Carrousel Crypto")
st.divider()

# ======================================================
# CONTENT
# ======================================================

st.info("📌 Cette page est en cours de construction")

st.markdown("""
### Objectif
Générer un carrousel de **8 actualités crypto** top scorées avec le label **Crypto** (cryptomonnaies, blockchain, Web3).

### Filtres prévus
- Période (7 derniers jours)
- Score minimum (ex: >75)
- Exclusion : shitcoins et prédictions (déjà filtrées par le scoring strict)

### Output attendu
- Format carousel Instagram (JSON structuré)
- Preview visuel (mockup)
- Export automatique
""")
