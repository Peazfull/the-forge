import streamlit as st
from db.supabase_client import get_supabase

# ======================================================
# PAGE CONFIG
# ======================================================

st.title("🇫🇷 Carrousel PEA")
st.divider()

# ======================================================
# CONTENT
# ======================================================

st.info("📌 Cette page est en cours de construction")

st.markdown("""
### Objectif
Générer un carrousel de **8 actualités PEA** top scorées avec le label **PEA** (entreprises européennes et françaises cotées).

### Filtres prévus
- Zone : Europe uniquement
- Période (7 derniers jours)
- Score minimum (ex: >70)
- Bonus : entreprises CAC 40 / SBF 120

### Output attendu
- Format carousel Instagram (JSON structuré)
- Preview visuel (mockup)
- Export automatique
""")
