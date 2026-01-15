import streamlit as st
import json
from datetime import datetime
from services.hand_brewery.process_text import process_text

# ======================================================
# CALLBACKS
# ======================================================

def clear_text_input():
    st.session_state.hand_text_input = ""
    st.session_state.text_status = []
    st.session_state.ai_preview_text = ""

# ======================================================
# INIT SESSION STATE
# ======================================================

if "text_status" not in st.session_state:
    st.session_state.text_status = []

if "ai_preview_text" not in st.session_state:
    st.session_state.ai_preview_text = ""

# ======================================================
# PAGE TITLE
# ======================================================

st.title("👨🏻‍💻 Hand Brewery")
st.divider()

# ======================================================
# BLOC 1 — URL (PLACEHOLDER)
# ======================================================

st.subheader("📰 Ajouter une URL d’article")

col_input, col_launch, col_clear = st.columns([3, 1, 1])

with col_input:
    st.text_input(
        label="",
        placeholder="https://example.com/article",
        label_visibility="collapsed",
        disabled=True
    )

with col_launch:
    st.button("🚀 Lancer", use_container_width=True, disabled=True)

with col_clear:
    st.button("🧹 Clear", use_container_width=True, disabled=True)

st.caption("⏳ Workflow URL à venir")
st.divider()

# ======================================================
# BLOC 2 — TEXTE → IA
# ======================================================

st.subheader("✍️ Coller du texte")

text_input = st.text_area(
    "Texte à analyser",
    placeholder="Colle ici ton article ou ton texte brut…",
    height=250,
    key="hand_text_input"
)

col_text_1, col_text_2 = st.columns(2)

with col_text_1:
    if st.button("🚀 Lancer le workflow TEXTE", use_container_width=True):

        st.session_state.text_status = [
            "Traitement du texte",
            "Analyse IA en cours"
        ]
        st.session_state.ai_preview_text = ""

        result = process_text(text_input)

        if result["status"] == "success":

            st.session_state.text_status.append(
                f"{len(result['items'])} informations structurées"
            )

            # Preview brute (JSON)
            st.session_state.ai_preview_text = json.dumps(
                {"items": result["items"]},
                indent=2,
                ensure_ascii=False
            )

            st.success("Traitement terminé · Preview générée")

        else:
            st.error("Erreur lors du traitement")
            st.caption(result.get("message", "Erreur inconnue"))

with col_text_2:
    st.button(
        "🧹 Clear TEXTE",
        use_container_width=True,
        on_click=clear_text_input
    )

# --- STATUT TEXTE ---
if st.session_state.text_status:
    st.markdown("**Statut :**")
    for step in st.session_state.text_status:
        st.write(f"⏳ {step}")

st.divider()

# ======================================================
# BLOC 3 — PREVIEW ÉDITABLE
# ======================================================

st.subheader("👀 Preview IA (éditable)")

if st.session_state.ai_preview_text:
    edited_preview = st.text_area(
        label="",
        value=st.session_state.ai_preview_text,
        height=450,
        key="ai_preview_editor"
    )

    col_validate, col_clear = st.columns(2)

    with col_validate:
        if st.button("✅ Valider et envoyer en DB", use_container_width=True):
            st.info("🔜 Insertion DB à brancher")

    with col_clear:
        if st.button("🧹 Clear preview", use_container_width=True):
            st.session_state.ai_preview_text = ""
            st.rerun()
else:
    st.caption("Aucune preview générée pour le moment")

st.divider()

# ======================================================
# BLOC 4 — DB (MOCK)
# ======================================================

st.subheader("🗄️ Contenu de la base (mock)")

mock_db = [
    {
        "source": "TEXTE",
        "nb_news": 6,
        "status": "DONE",
        "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
]

st.dataframe(mock_db, use_container_width=True, hide_index=True)
