import streamlit as st
from db.supabase_client import get_supabase

# ======================================================
# PAGE CONFIG
# ======================================================

st.title("📊 Carrousel Bourse")
st.divider()

# ======================================================
# CONTENT
# ======================================================

st.info("📌 Cette page est en cours de construction")

st.markdown("""
### Objectif
Générer un carrousel de **8 actualités bourse** avec la répartition suivante :
- Top 3 : Label **Action** (entreprises hors EU/FR)
- Top 2 : Label **PEA** (entreprises EU/FR)
- Top 2 : Label **Indices** (mouvements indices boursiers)
- Top 1 : Label **Commodités** (matières premières)

### Filtres prévus
- Période (7 derniers jours)
- Score minimum (ex: >75)

### Output attendu
- Format carousel Instagram (JSON structuré)
- Preview visuel (mockup)
- Export automatique
""")
