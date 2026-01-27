import streamlit as st
from db.supabase_client import get_supabase

# ======================================================
# PAGE CONFIG
# ======================================================

st.title("⚡ Breaking")
st.divider()

# ======================================================
# CONTENT
# ======================================================

st.info("📌 Cette page est en cours de construction")

st.markdown("""
### Objectif
Générer des **Breaking News** (actualités urgentes/très importantes).

### Critères de sélection
- Score **>90**
- Labels prioritaires : **Eco-Geopol**, **Indices**
- Période : **24 dernières heures**
- Événements majeurs : Fed, BCE, records, krachs

### Output attendu
- Format Story Instagram (vertical 9:16)
- Texte court + visuel impactant
- Export automatique
""")
