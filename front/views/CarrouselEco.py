import streamlit as st
from db.supabase_client import get_supabase

# ======================================================
# PAGE CONFIG
# ======================================================

st.title("🌍 Carrousel Eco")
st.divider()

# ======================================================
# CONTENT
# ======================================================

st.info("📌 Cette page est en cours de construction")

st.markdown("""
### Objectif
Générer un carrousel de **8 actualités économiques** top scorées avec le label **Eco-Geopol**.

### Filtres prévus
- Zone géographique (USA, Europe, ASIA)
- Période (7 derniers jours)
- Score minimum (ex: >70)

### Output attendu
- Format carousel Instagram (JSON structuré)
- Preview visuel (mockup)
- Export automatique
""")
