import json
import uuid
import streamlit as st

from services.hand_brewery.article_pipeline import (
    run_rewrite,
    run_extract_news,
    run_jsonify,
)
from services.hand_brewery.firecrawl_client import fetch_url_text
from services.raw_storage.raw_news_service import (
    enrich_raw_items,
    insert_raw_news,
    fetch_raw_news,
)


# ======================================================
# HELPERS
# ======================================================

def _new_article(raw_text: str = "") -> dict:
    return {
        "id": str(uuid.uuid4()),
        "raw_text": raw_text,
        "rewrite_text": "",
        "extract_text": "",
        "final_items": [],
        "status": "idle",
        "error": None,
        "needs_clarification": False,
        "questions": [],
    }


def _get_article_index(article_id: str) -> int:
    for idx, article in enumerate(st.session_state.articles):
        if article["id"] == article_id:
            return idx
    return -1


def _reset_article(article: dict) -> None:
    article["rewrite_text"] = ""
    article["extract_text"] = ""
    article["final_items"] = []
    article["status"] = "idle"
    article["error"] = None
    article["needs_clarification"] = False
    article["questions"] = []


def _set_error(article: dict, message: str) -> None:
    article["status"] = "error"
    article["error"] = message


def _set_questions(article: dict, questions: list) -> None:
    article["status"] = "needs_clarification"
    article["needs_clarification"] = True
    article["questions"] = questions or []


def _run_rewrite(article: dict) -> bool:
    article["status"] = "processing"
    article["error"] = None
    article["needs_clarification"] = False
    article["questions"] = []

    result = run_rewrite(article["raw_text"])
    if result["status"] != "success":
        _set_error(article, result.get("message", "Erreur inconnue"))
        return False

    article["rewrite_text"] = result.get("rewrite_text", "")
    if result.get("needs_clarification"):
        _set_questions(article, result.get("questions", []))
        return False

    article["status"] = "ready"
    return True


def _run_jsonify(article: dict) -> bool:
    article["status"] = "processing"
    article["error"] = None

    result = run_jsonify(article["extract_text"])
    if result["status"] != "success":
        _set_error(article, result.get("message", "Erreur inconnue"))
        return False

    article["final_items"] = result.get("items", [])
    if not article["final_items"]:
        _set_error(article, "Aucun item JSON généré")
        return False

    article["status"] = "ready"
    return True


def _run_extract(article: dict) -> bool:
    article["status"] = "processing"
    article["error"] = None
    article["needs_clarification"] = False
    article["questions"] = []

    result = run_extract_news(article["rewrite_text"])
    if result["status"] != "success":
        _set_error(article, result.get("message", "Erreur inconnue"))
        return False
    article["extract_text"] = result.get("extracted_text", "")
    article["status"] = "ready"
    return True


# ======================================================
# INIT SESSION STATE
# ======================================================

if "articles" not in st.session_state:
    st.session_state.articles = []


# ======================================================
# PAGE TITLE
# ======================================================

st.title("🧠 Hand Brewery — Simple Buffer")
st.divider()


# ======================================================
# ADD ARTICLES
# ======================================================

with st.expander("➕ Ajouter des articles", expanded=True):
    col_add, col_clear = st.columns([2, 1])

    with col_add:
        if st.button("Ajouter un article vide", use_container_width=True):
            st.session_state.articles.append(_new_article())
            st.rerun()

    with col_clear:
        if st.button("Clear tous les articles", use_container_width=True):
            st.session_state.articles = []
            st.rerun()

    st.markdown("**Importer via URL**")
    col_url_input, col_url_launch = st.columns([3, 1])

    with col_url_input:
        url_input = st.text_input(
            label="",
            placeholder="https://example.com/article",
            label_visibility="collapsed",
            key="hand_url_input",
        )

    with col_url_launch:
        if st.button("Importer URL", use_container_width=True, key="hand_url_launch"):
            if not url_input.strip():
                st.error("❌ URL vide")
            else:
                try:
                    raw_text = fetch_url_text(url_input)
                except Exception as exc:
                    st.error("❌ Impossible de scrapper l’URL")
                    st.caption(str(exc))
                    st.stop()
                st.session_state.articles.append(_new_article(raw_text=raw_text))
                st.success("Article importé")
                st.rerun()


# ======================================================
# ARTICLES LIST
# ======================================================

if not st.session_state.articles:
    st.info("Aucun article pour le moment. Ajoute-en un pour démarrer.")
else:
    for idx, article in enumerate(st.session_state.articles, start=1):
        article_id = article["id"]
        with st.expander(f"📝 Article {idx}", expanded=True):
            col_actions_1, col_actions_2, col_actions_3 = st.columns(3)

            with col_actions_1:
                if st.button("▶ Générer preview", use_container_width=True, key=f"run_{article_id}"):
                    _run_rewrite(article)
                    st.rerun()

            with col_actions_2:
                if st.button("🧹 Clear article", use_container_width=True, key=f"clear_{article_id}"):
                    _reset_article(article)
                    st.rerun()

            with col_actions_3:
                if st.button("🗑️ Supprimer article", use_container_width=True, key=f"delete_{article_id}"):
                    delete_idx = _get_article_index(article_id)
                    if delete_idx >= 0:
                        st.session_state.articles.pop(delete_idx)
                        st.rerun()

            status_text = f"Statut: {article['status']}"
            if article.get("error"):
                status_text += f" · Erreur: {article['error']}"
            st.caption(status_text)

            if article.get("needs_clarification") and article.get("questions"):
                st.warning("Questions à clarifier :")
                for q in article["questions"]:
                    st.write(f"- {q}")

            raw_key = f"raw_{article_id}"
            if raw_key not in st.session_state:
                st.session_state[raw_key] = article.get("raw_text", "")
            st.text_area(
                "Texte brut",
                height=200,
                key=raw_key,
            )
            article["raw_text"] = st.session_state[raw_key]

            st.divider()
            st.markdown("**Preview rewrite (buffer éditable)**")
            rewrite_key = f"rewrite_{article_id}"
            if rewrite_key not in st.session_state:
                st.session_state[rewrite_key] = article.get("rewrite_text", "")
            st.text_area(
                label="",
                height=220,
                key=rewrite_key,
            )
            article["rewrite_text"] = st.session_state[rewrite_key]

            col_extract, _ = st.columns(2)
            with col_extract:
                if st.button("🧠 Extraire news", use_container_width=True, key=f"extract_run_{article_id}"):
                    _run_extract(article)
                    st.rerun()

            if article.get("extract_text"):
                st.markdown("**Preview news extraites (buffer éditable)**")
                extract_key = f"extract_{article_id}"
                if extract_key not in st.session_state:
                    st.session_state[extract_key] = article.get("extract_text", "")
                st.text_area(
                    label="",
                    height=220,
                    key=extract_key,
                )
                article["extract_text"] = st.session_state[extract_key]

                if st.button("✅ JSONify", use_container_width=True, key=f"jsonify_{article_id}"):
                    article["extract_text"] = st.session_state[extract_key]
                    _run_jsonify(article)
                    st.rerun()

            if article.get("final_items"):
                st.markdown("**Preview JSON (avant DB)**")
                st.text_area(
                    label="",
                    value=json.dumps({"items": article["final_items"]}, ensure_ascii=False, indent=2),
                    height=240,
                    key=f"json_preview_{article_id}",
                )

                if st.button("📤 Envoyer en DB", use_container_width=True, key=f"send_{article_id}"):
                    enriched_items = enrich_raw_items(
                        article["final_items"],
                        flow="hand_text",
                        source_type="manual",
                        source_raw=None,
                    )
                    result = insert_raw_news(enriched_items)
                    if result["status"] == "success":
                        st.success(f"✅ {result['inserted']} items insérés en base")
                    else:
                        st.error("❌ Erreur lors de l'insertion en DB")
                        st.caption(result.get("message", "Erreur inconnue"))


# ======================================================
# LAST ITEMS IN DB
# ======================================================

with st.expander("🗄️ Derniers contenus en base", expanded=False):
    raw_items = fetch_raw_news(limit=100)

    if not raw_items:
        st.caption("Aucun contenu en base pour le moment")
    else:
        for item in raw_items:
            st.markdown("---")
            st.caption(f"🕒 {item['processed_at']} · Source : {item['source_type']}")
            st.markdown(f"**{item['title']}**")
            st.write(item["content"])
