import streamlit as st
import json
import re
from datetime import datetime
from services.nl_brewery.nl_brewery_service import (
    load_recipients,
    add_recipient,
    remove_recipient,
    check_gmail_connection,
    fetch_raw_newsletters,
    run_clean_raw,
    run_merge_topics,
    run_journalist,
    run_jsonfy,
)
from services.raw_storage.raw_news_service import (
    enrich_raw_items,
    insert_raw_news,
    fetch_raw_news,
)


def _format_datetime(value: str) -> str:
    if not value:
        return ""
    try:
        fixed = value.replace("Z", "+00:00")
        return datetime.fromisoformat(fixed).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value


def _refresh_recipients() -> None:
    st.session_state.nl_recipients = load_recipients()


def _extract_emails(raw_value: str) -> list:
    if not raw_value:
        return []
    # Accepte des emails séparés par virgules, espaces ou retours à la ligne
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", raw_value)


if "nl_recipients" not in st.session_state:
    _refresh_recipients()

if "nl_ai_preview_text" not in st.session_state:
    st.session_state.nl_ai_preview_text = ""

if "nl_status" not in st.session_state:
    st.session_state.nl_status = []

if "nl_last_email_count" not in st.session_state:
    st.session_state.nl_last_email_count = None

if "nl_raw_preview_text" not in st.session_state:
    st.session_state.nl_raw_preview_text = ""

if "nl_cleaned_text" not in st.session_state:
    st.session_state.nl_cleaned_text = ""

if "nl_merged_text" not in st.session_state:
    st.session_state.nl_merged_text = ""

if "nl_journalist_text" not in st.session_state:
    st.session_state.nl_journalist_text = ""


st.title("📨 NL Brewery")
st.divider()

# =========================
# 1️⃣ ADRESSES NEWSLETTERS
# =========================
with st.expander("📬 Adresses newsletters", expanded=False):
    col_email, col_add = st.columns([4, 1])
    with col_email:
        email_input = st.text_input(
            "Adresse newsletter",
            placeholder="peazfull+eco@gmail.com",
            label_visibility="collapsed",
            key="nl_email_input"
        )
    with col_add:
        if st.button("➕ Ajouter", use_container_width=True, key="nl_add_email"):
            emails = _extract_emails(email_input)
            if not emails:
                st.error("Email invalide.")
            else:
                existing = set(st.session_state.nl_recipients or [])
                added = 0
                skipped = 0
                failed = 0
                for email_addr in emails:
                    if email_addr in existing:
                        skipped += 1
                        continue
                    if add_recipient(email_addr):
                        added += 1
                        existing.add(email_addr)
                    else:
                        failed += 1
                _refresh_recipients()
                if added:
                    st.success(f"{added} adresse(s) ajoutée(s).")
                if skipped:
                    st.warning(f"{skipped} adresse(s) déjà enregistrée(s).")
                if failed:
                    st.error(f"{failed} adresse(s) non ajoutée(s).")

    if st.session_state.nl_recipients:
        st.markdown("**Adresses enregistrées :**")
        for idx, email_addr in enumerate(st.session_state.nl_recipients):
            col_label, col_delete = st.columns([5, 1])
            with col_label:
                st.write(f"📧 {email_addr}")
            with col_delete:
                if st.button("❌", key=f"nl_delete_{idx}"):
                    if remove_recipient(email_addr):
                        _refresh_recipients()
                        st.rerun()
    else:
        st.caption("Aucune adresse enregistrée pour le moment.")

# =========================
# 2️⃣ CONNEXION GMAIL
# =========================
col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 1, 1, 1])
with col1:
    st.write("🔐 Connexion Gmail (Status)")
with col2:
    status = check_gmail_connection()
    if status.get("status") == "success":
        st.success("🟢 Gmail connecté")
    else:
        st.error("🔴 Erreur IMAP")
        st.caption(status.get("message", "Erreur inconnue"))

if st.session_state.nl_last_email_count is not None:
    st.caption(f"📬 {st.session_state.nl_last_email_count} newsletter(s) trouvée(s)")

# =========================
# 3️⃣ FENETRE TEMPORELLE
# =========================
col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 1, 1, 1])
with col1:
    st.write("⏱️ Fenêtre temporelle")
with col2:
    hours_window = st.number_input(
        "Fenêtre d’analyse (heures)",
        min_value=1,
        max_value=168,
        value=24,
        step=1,
        key="nl_hours_window",
        label_visibility="collapsed"
    )
st.caption(f"Analyser les newsletters reçues sur les dernières {hours_window} heures")

# =========================
# 4️⃣ SCRAPER NEWSLETTERS
# =========================
col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 1, 1, 1])
with col1:
    if st.button("🔄 Scraper les newsletters", use_container_width=True, key="nl_scrape"):
        st.session_state.nl_status = [
            "Connexion Gmail",
            "Lecture des emails",
            "Préparation du texte brut"
        ]
        st.session_state.nl_ai_preview_text = ""
        st.session_state.nl_raw_preview_text = ""
        st.session_state.nl_cleaned_text = ""
        st.session_state.nl_merged_text = ""
        st.session_state.nl_journalist_text = ""

        with st.spinner("Récupération et analyse en cours…"):
            result = fetch_raw_newsletters(last_hours=int(hours_window))

        errors = result.get("errors", [])
        st.session_state.nl_last_email_count = result.get("email_count")
        st.session_state.nl_raw_preview_text = result.get("raw_preview", "")

        if st.session_state.nl_raw_preview_text:
            st.success("Texte brut récupéré.")
        else:
            st.warning("Aucun texte brut exploitable trouvé.")

        if errors:
            st.caption("Erreurs détectées :")
            for err in errors[:5]:
                st.write(f"⚠️ {err}")

# =========================
# 5️⃣ TEXTE BRUT (SCRAPING)
# =========================
with st.expander("🧾 Texte brut (scraping)", expanded=True):
    if st.session_state.nl_raw_preview_text:
        edited_raw = st.text_area(
            label="",
            value=st.session_state.nl_raw_preview_text,
            height=300,
            key="nl_raw_preview"
        )
        col_validate, col_clear = st.columns(2)
        with col_validate:
            if st.button("✅ Valider et nettoyer", use_container_width=True, key="nl_run_clean"):
                st.session_state.nl_raw_preview_text = edited_raw
                with st.spinner("Nettoyage en cours…"):
                    result = run_clean_raw(edited_raw)
                if result.get("status") == "success":
                    st.session_state.nl_cleaned_text = result.get("text", "")
                    st.success("Texte nettoyé.")
                else:
                    st.error("❌ Erreur nettoyage")
                    st.caption(result.get("message", "Erreur inconnue"))
        with col_clear:
            if st.button("🧹 Clear", use_container_width=True, key="nl_clear_raw"):
                st.session_state.nl_raw_preview_text = ""
                st.session_state.nl_cleaned_text = ""
                st.session_state.nl_merged_text = ""
                st.session_state.nl_journalist_text = ""
                st.session_state.nl_ai_preview_text = ""
                st.rerun()
    else:
        st.caption("Aucun texte brut à afficher.")

# =========================
# 6️⃣ TEXTE NETTOYÉ
# =========================
with st.expander("🧼 Texte nettoyé", expanded=True):
    if st.session_state.nl_cleaned_text:
        edited_clean = st.text_area(
            label="",
            value=st.session_state.nl_cleaned_text,
            height=300,
            key="nl_cleaned_preview"
        )
        col_validate, col_clear = st.columns(2)
        with col_validate:
            if st.button("🔧 Regrouper les sujets", use_container_width=True, key="nl_run_merge"):
                st.session_state.nl_cleaned_text = edited_clean
                with st.spinner("Regroupement en cours…"):
                    result = run_merge_topics(edited_clean)
                if result.get("status") == "success":
                    st.session_state.nl_merged_text = result.get("text", "")
                    st.success("Texte traité.")
                else:
                    st.error("❌ Erreur regroupement")
                    st.caption(result.get("message", "Erreur inconnue"))
        with col_clear:
            if st.button("🧹 Clear", use_container_width=True, key="nl_clear_cleaned"):
                st.session_state.nl_cleaned_text = ""
                st.session_state.nl_merged_text = ""
                st.session_state.nl_journalist_text = ""
                st.session_state.nl_ai_preview_text = ""
                st.rerun()
    else:
        st.caption("Aucun texte nettoyé pour le moment.")

# =========================
# 7️⃣ TEXTE TRAITÉ
# =========================
with st.expander("🧩 Texte traité (dédupliqué)", expanded=True):
    if st.session_state.nl_merged_text:
        edited_merged = st.text_area(
            label="",
            value=st.session_state.nl_merged_text,
            height=320,
            key="nl_merged_preview"
        )
        col_validate, col_clear = st.columns(2)
        with col_validate:
            if st.button("📰 Générer texte journalist", use_container_width=True, key="nl_run_journalist"):
                st.session_state.nl_merged_text = edited_merged
                with st.spinner("Rédaction journalistique…"):
                    result = run_journalist(edited_merged)
                if result.get("status") == "success":
                    st.session_state.nl_journalist_text = result.get("text", "")
                    st.success("Texte journalist généré.")
                else:
                    st.error("❌ Erreur journalist")
                    st.caption(result.get("message", "Erreur inconnue"))
        with col_clear:
            if st.button("🧹 Clear", use_container_width=True, key="nl_clear_merged"):
                st.session_state.nl_merged_text = ""
                st.session_state.nl_journalist_text = ""
                st.session_state.nl_ai_preview_text = ""
                st.rerun()
    else:
        st.caption("Aucun texte traité pour le moment.")

# =========================
# 8️⃣ TEXTE JOURNALIST
# =========================
with st.expander("📰 Texte journalist", expanded=True):
    if st.session_state.nl_journalist_text:
        edited_journalist = st.text_area(
            label="",
            value=st.session_state.nl_journalist_text,
            height=360,
            key="nl_journalist_preview"
        )
        col_validate, col_clear = st.columns(2)
        with col_validate:
            if st.button("✅ Générer preview IA", use_container_width=True, key="nl_run_jsonfy"):
                st.session_state.nl_journalist_text = edited_journalist
                with st.spinner("Génération JSON…"):
                    result = run_jsonfy(edited_journalist)
                items = result.get("items", [])
                if result.get("status") == "success" and items:
                    st.session_state.nl_ai_preview_text = json.dumps(
                        {"items": items},
                        indent=2,
                        ensure_ascii=False
                    )
                    st.success(f"{len(items)} items générés")
                elif result.get("status") == "success":
                    st.warning("Aucun item exploitable trouvé.")
                else:
                    st.error("❌ Erreur JSON")
                    st.caption(result.get("message", "Erreur inconnue"))
        with col_clear:
            if st.button("🧹 Clear", use_container_width=True, key="nl_clear_journalist"):
                st.session_state.nl_journalist_text = ""
                st.session_state.nl_ai_preview_text = ""
                st.rerun()
    else:
        st.caption("Aucun texte journalist pour le moment.")

# =========================
# 9️⃣ PREVIEW IA
# =========================
with st.expander("👀 Preview IA (éditable)", expanded=True):
    if st.session_state.nl_ai_preview_text:
        edited_preview = st.text_area(
            label="",
            value=st.session_state.nl_ai_preview_text,
            height=450,
            key="nl_preview_editor"
        )

        col_validate, col_clear = st.columns(2)
        with col_validate:
            if st.button("✅ Valider et envoyer en DB", use_container_width=True, key="nl_send_db"):
                try:
                    data = json.loads(edited_preview)
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
                    flow="nl_brewery",
                    source_type="newsletter",
                    source_raw=None
                )
                result = insert_raw_news(enriched_items)

                if result["status"] == "success":
                    st.success(f"✅ {result['inserted']} items insérés en base")
                    st.session_state.nl_ai_preview_text = ""
                else:
                    st.error("❌ Erreur lors de l'insertion en DB")
                    st.caption(result.get("message", "Erreur inconnue"))

        with col_clear:
            if st.button("🧹 Clear", use_container_width=True, key="nl_clear_preview"):
                st.session_state.nl_ai_preview_text = ""
                st.rerun()
    else:
        st.caption("Aucune preview générée pour le moment.")

# =========================
# 10️⃣ DERNIERS CONTENUS DB
# =========================
with st.expander("🗄️ Derniers contenus en base", expanded=False):
    items = fetch_raw_news(limit=50)
    newsletter_items = [item for item in items if item.get("source_type") == "newsletter"]

    if not newsletter_items:
        st.caption("Aucun contenu Newsletter en base pour le moment.")
    else:
        for item in newsletter_items:
            st.write(f"🗓️ {_format_datetime(item.get('processed_at'))}")
            st.write("📌 Source : Newsletter")
            st.write(f"**{item.get('title', '')}**")
            st.write(item.get("content", ""))
            st.divider()
