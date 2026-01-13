import streamlit as st
from datetime import datetime

# ======================================================
# TITRE PAGE
# ======================================================

st.title("👨🏻‍💻 Hand Brewery")
st.divider()

# ======================================================
# SESSION STATE (FRONT ONLY)
# ======================================================

# --- URL workflow ---
if "url_status" not in st.session_state:
    st.session_state.url_status = []

if "url_progress" not in st.session_state:
    st.session_state.url_progress = 0

# --- TEXTE workflow ---
if "text_status" not in st.session_state:
    st.session_state.text_status = []

if "text_progress" not in st.session_state:
    st.session_state.text_progress = 0

# ======================================================
# BLOC 1 — URL
# ======================================================

st.subheader("📰 Ajouter une URL d’article")

# Layout : input 3/5 – bouton lancer 1/5 – bouton clear 1/5
col_input, col_launch, col_clear = st.columns([3, 1, 1])

with col_input:
    url = st.text_input(
    label="",
    placeholder="https://example.com/article",
    label_visibility="collapsed"
)


with col_launch:
    if st.button("🚀 Lancer", use_container_width=True):
        # TODO: process_url(url)
        st.session_state.url_progress = 20
        st.session_state.url_status = [
            "Traitement scrapping en cours",
            "Envoi du texte à l’IA",
            "Output de l’IA",
            "X news retournées",
            "Traitement JSON pour DB",
            f"Ajout en DB à {datetime.now().strftime('%H:%M:%S')}",
        ]

with col_clear:
    if st.button("🧹 Clear", use_container_width=True):
        url = ""
        st.session_state.url_status = []
        st.session_state.url_progress = 0

# --- STATUT URL ---
if st.session_state.url_status:
    st.progress(st.session_state.url_progress)
    for step in st.session_state.url_status:
        st.write(f"⏳ {step}")

st.divider()

# ======================================================
# BLOC 2 — TEXTE LIBRE
# ======================================================

st.subheader("✍️ Coller du texte")

text_input = st.text_area(
    "Texte à analyser",
    placeholder="Colle ici ton article ou ton texte brut…",
    height=250
)

col_text_1, col_text_2 = st.columns(2)

with col_text_1:
    if st.button("🚀 Lancer le workflow TEXTE", use_container_width=True):
        # TODO: process_text(text_input)
        st.session_state.text_progress = 30
        st.session_state.text_status = [
            "Traitement du texte en cours",
            "Envoi du texte à l’IA",
            "Output de l’IA",
            "X news retournées",
            "Traitement JSON pour DB",
            f"Ajout en DB à {datetime.now().strftime('%H:%M:%S')}",
        ]

with col_text_2:
    if st.button("🧹 Clear TEXTE", use_container_width=True):
        text_input = ""
        st.session_state.text_status = []
        st.session_state.text_progress = 0

# --- STATUT TEXTE ---
if st.session_state.text_status:
    st.progress(st.session_state.text_progress)
    for step in st.session_state.text_status:
        st.write(f"⏳ {step}")

st.divider()

# ======================================================
# BLOC 3 — TABLE DB (MOCK)
# ======================================================

st.subheader("🗄️ Contenu de la base de données")

# MOCK DB — FRONT ONLY
mock_db = [
    {
        "id": 1,
        "source": "URL",
        "input": "https://example.com/article-1",
        "nb_news": 4,
        "status": "DONE",
        "finished_at": "2026-01-12 14:32",
    },
    {
        "id": 2,
        "source": "TEXTE",
        "input": "Copié / collé",
        "nb_news": 7,
        "status": "DONE",
        "finished_at": "2026-01-12 14:45",
    },
]

st.dataframe(
    mock_db,
    use_container_width=True,
    hide_index=True
)

st.divider()
