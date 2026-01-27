import streamlit as st
from db.supabase_client import get_supabase

# ======================================================
# PAGE CONFIG
# ======================================================

st.title("📁 Carrousel Doss'")
st.divider()

# ======================================================
# CONTENT
# ======================================================

st.info("📌 Cette page est en cours de construction")

st.markdown("""
### Objectif
Générer des **Carrousels thématiques** (dossiers approfondis) sur un sujet précis.

### Exemples de dossiers
- "Les GAFAM en 2026 : bilan du T1"
- "L'or : pourquoi les records se multiplient"
- "La Fed : rétrospective des décisions 2025-2026"

### Fonctionnalités prévues
- Sélection d'items par entité (ex: tous les bulletins sur "Fed")
- Regroupement thématique automatique
- Génération d'un carrousel de synthèse (8-10 slides)

### Output attendu
- Format carousel Instagram (JSON structuré)
- Preview visuel (mockup)
- Export automatique
""")
