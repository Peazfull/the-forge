import streamlit as st
import json
from datetime import datetime
from services.hand_brewery.process_text import process_text
from services.hand_brewery.process_url import process_url 
from services.raw_storage.raw_news_service import (
    enrich_raw_items,
    insert_raw_news,
    fetch_raw_news
)


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

# =========================
# 1️⃣ URL D'ARTICLE
# =========================
with st.expander("📰 Ajouter une URL d’article", expanded=False):
    col_input, col_launch, col_clear = st.columns([3, 1, 1])

    with col_input:
        url_input = st.text_input(
            label="",
            placeholder="https://example.com/article",
            label_visibility="collapsed",
            key="hand_url_input"
        )

    with col_launch:
        if st.button("🚀 Lancer", use_container_width=True, key="hand_url_launch"):
            st.session_state.text_status = [
                "Scraping de l'URL",
                "Analyse IA en cours"
            ]
            st.session_state.ai_preview_text = ""

            try:
                result = process_url(url_input)
            except Exception as e:
                st.error("❌ Impossible de scrapper l’URL")
                st.caption(str(e))
                st.stop()

            if result["status"] == "success":
                st.session_state.text_status.append(
                    f"{len(result['items'])} informations structurées"
                )

                st.session_state.ai_preview_text = json.dumps(
                    {"items": result["items"]},
                    indent=2,
                    ensure_ascii=False
                )

                st.success("Traitement URL terminé · Preview générée")
            else:
                st.error("Erreur lors du traitement de l’URL")
                st.caption(result.get("message", "Erreur inconnue"))

    with col_clear:
        st.button("🧹 Clear", use_container_width=True, disabled=True, key="hand_url_clear")

    st.caption("⏳ Workflow URL à venir")

# =========================
# 2️⃣ TEXTE À ANALYSER
# =========================
with st.expander("✍️ Coller du texte", expanded=True):
    text_input = st.text_area(
        "Texte à analyser",
        placeholder="Colle ici ton article ou ton texte brut…",
        height=250,
        key="hand_text_input"
    )

    col_text_1, col_text_2 = st.columns(2)

    with col_text_1:
        if st.button("🚀 Lancer le workflow TEXTE", use_container_width=True, key="hand_text_launch"):
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
            on_click=clear_text_input,
            key="hand_text_clear"
        )

    if st.session_state.text_status:
        st.markdown("**Statut :**")
        for step in st.session_state.text_status:
            st.write(f"⏳ {step}")

# =========================
# 3️⃣ PREVIEW IA
# =========================
with st.expander("👀 Preview IA (éditable)", expanded=True):
    if st.session_state.ai_preview_text:
        edited_preview = st.text_area(
            label="",
            value=st.session_state.ai_preview_text,
            height=450,
            key="ai_preview_editor"
        )

        col_validate, col_clear = st.columns(2)

        with col_validate:
            if st.button("✅ Valider et envoyer en DB", use_container_width=True, key="hand_send_db"):
                raw_json_text = st.session_state.ai_preview_text

                try:
                    data = json.loads(raw_json_text)
                except json.JSONDecodeError:
                    st.error("❌ JSON invalide. Corrige la preview avant l'envoi.")
                    st.stop()

                if "items" not in data or not isinstance(data["items"], list):
                    st.error("❌ Format JSON invalide (clé 'items' manquante).")
                    st.stop()

                if not data["items"]:
                    st.error("❌ Aucun item à insérer.")
                    st.stop()

                enriched_items = enrich_raw_items(
                    data["items"],
                    flow="hand_text",
                    source_type="manual",
                    source_raw=None  # C'est le texte brut, on ne l'enregistre pas
                )

                result = insert_raw_news(enriched_items)

                if result["status"] == "success":
                    st.success(f"✅ {result['inserted']} items insérés en base")
                    st.session_state.ai_preview_text = ""
                else:
                    st.error("❌ Erreur lors de l'insertion en DB")
                    st.caption(result.get("message", "Erreur inconnue"))

        with col_clear:
            if st.button("🧹 Clear", use_container_width=True, key="hand_preview_clear"):
                st.session_state.ai_preview_text = ""
                st.rerun()
    else:
        st.caption("Aucune preview générée pour le moment")

# =========================
# 4️⃣ DERNIERS CONTENUS EN BASE
# =========================
with st.expander("🗄️ Derniers contenus en base", expanded=False):
    raw_items = fetch_raw_news(limit=100)

    if not raw_items:
        st.caption("Aucun contenu en base pour le moment")
    else:
        for item in raw_items:
            st.markdown("---")
            st.caption(f"🕒 {item['processed_at']} · Source : {item['source_type']}")
            st.markdown(f"**{item['title']}**")
            st.write(item['content'])
