import streamlit as st
from db.supabase_client import get_supabase

# ======================================================
# PAGE CONFIG
# ======================================================

st.title("📖 Story")
st.divider()

# ======================================================
# CONTENT
# ======================================================

st.info("📌 Cette page est en cours de construction")

st.markdown("""
### Objectif
Générer des **Stories Instagram** (format vertical 9:16) à partir d'actualités sélectionnées.

### Fonctionnalités prévues
- Sélection manuelle d'items depuis la DB
- Template visuel automatique
- Texte adapté au format story (court, impactant)
- Preview temps réel

### Output attendu
- Images 1080x1920 px (9:16)
- Export PNG/JPG
- Batch export (plusieurs stories)
""")
