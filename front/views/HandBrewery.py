import json
import uuid
import streamlit as st

from services.hand_brewery.article_pipeline import (
    run_rewrite,
    run_split,
    run_final_items,
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
        "structured_news": [],
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
    article["structured_news"] = []
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


def _run_step1(article: dict) -> bool:
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

    return True


def _run_step2(article: dict) -> bool:
    article["status"] = "processing"
    article["error"] = None
    article["needs_clarification"] = False
    article["questions"] = []

    result = run_split(article["rewrite_text"])
    if result["status"] != "success":
        _set_error(article, result.get("message", "Erreur inconnue"))
        return False

    article["structured_news"] = result.get("structured_news", [])
    if result.get("needs_clarification"):
        _set_questions(article, result.get("questions", []))
        return False

    return True


def _run_step3(article: dict) -> bool:
    article["status"] = "processing"
    article["error"] = None
    article["needs_clarification"] = False
    article["questions"] = []

    result = run_final_items(article["structured_news"])
    if result["status"] != "success":
        _set_error(article, result.get("message", "Erreur inconnue"))
        return False

    article["final_items"] = result.get("final_items", [])
    if result.get("needs_clarification"):
        _set_questions(article, result.get("questions", []))
        return False

    return True


def _run_full_pipeline(article: dict) -> None:
    if not _run_step1(article):
        return
    if not _run_step2(article):
        return
    if not _run_step3(article):
        return
    article["status"] = "done"


def _collect_all_final_items() -> list:
    items = []
    for article in st.session_state.articles:
        items.extend(article.get("final_items", []))
    return items


# ======================================================
# INIT SESSION STATE
# ======================================================

if "articles" not in st.session_state:
    st.session_state.articles = []

if "job" not in st.session_state:
    st.session_state.job = {
        "status": "idle",
        "article_ids": [],
        "final_items": [],
    }


# ======================================================
# PAGE TITLE
# ======================================================

st.title("🧠 Hand Brewery — Multi Input")
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
            st.session_state.job = {"status": "idle", "article_ids": [], "final_items": []}
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
# GLOBAL JOB
# ======================================================

with st.expander("🧰 Job global (tous les articles)", expanded=False):
    if not st.session_state.articles:
        st.caption("Ajoute au moins un article pour lancer le job global")
    else:
        col_run, col_status = st.columns([1, 2])
        with col_run:
            if st.button("▶ Lancer tout le job", use_container_width=True):
                st.session_state.job["status"] = "running"
                st.session_state.job["article_ids"] = [a["id"] for a in st.session_state.articles]
                progress = st.progress(0)
                total = len(st.session_state.articles)

                for idx, article in enumerate(st.session_state.articles, start=1):
                    _run_full_pipeline(article)
                    progress.progress(int(idx / total * 100))

                st.session_state.job["status"] = "completed"
                st.success("Job global terminé")

        with col_status:
            st.caption(f"Statut job: {st.session_state.job['status']}")

        all_items = _collect_all_final_items()
        if all_items:
            st.markdown("**Preview finale (tous articles)**")
            st.text_area(
                label="",
                value=json.dumps({"items": all_items}, ensure_ascii=False, indent=2),
                height=300,
                key="hand_all_preview",
            )
        else:
            st.caption("Aucun final_item généré pour le moment")

        if all_items:
            if st.button("✅ Valider et envoyer TOUT en DB", use_container_width=True, key="hand_send_all"):
                enriched_items = enrich_raw_items(
                    all_items,
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
                if st.button("▶ Lancer cet article", use_container_width=True, key=f"run_{article_id}"):
                    _run_full_pipeline(article)
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
            st.markdown("**Étape 1 — Rewrite (anti-plagiat)**")
            col_step1_a, col_step1_b = st.columns([1, 2])
            with col_step1_a:
                if st.button("Relancer étape 1", use_container_width=True, key=f"step1_{article_id}"):
                    _run_step1(article)
                    st.rerun()
            with col_step1_b:
                st.caption("Preview rewrite (éditable)")

            rewrite_key = f"rewrite_{article_id}"
            if rewrite_key not in st.session_state:
                st.session_state[rewrite_key] = article.get("rewrite_text", "")
            st.text_area(
                label="",
                height=200,
                key=rewrite_key,
            )
            article["rewrite_text"] = st.session_state[rewrite_key]

            st.divider()
            st.markdown("**Étape 2 — Clean & Split**")
            col_step2_a, col_step2_b = st.columns([1, 2])
            with col_step2_a:
                if st.button("Relancer étape 2", use_container_width=True, key=f"step2_{article_id}"):
                    _run_step2(article)
                    st.rerun()
            with col_step2_b:
                st.caption("Chaque news est éditable")

            structured_news = article.get("structured_news", [])
            if structured_news:
                delete_news_idx = None
                merge_news_idx = None
                for n_idx, news in enumerate(structured_news):
                    with st.expander(f"News {n_idx + 1}", expanded=False):
                        sections = news.get("sections", [])
                        for s_idx, section in enumerate(sections):
                            title_key = f"sec_title_{article_id}_{n_idx}_{s_idx}"
                            content_key = f"sec_content_{article_id}_{n_idx}_{s_idx}"
                            if title_key not in st.session_state:
                                st.session_state[title_key] = section.get("title", "")
                            if content_key not in st.session_state:
                                st.session_state[content_key] = section.get("content", "")

                            st.text_input("Titre", key=title_key)
                            st.text_area("Contenu", key=content_key, height=120)

                            section["title"] = st.session_state[title_key]
                            section["content"] = st.session_state[content_key]

                        col_news_1, col_news_2 = st.columns(2)
                        with col_news_1:
                            if st.button("🗑️ Supprimer cette news", use_container_width=True, key=f"del_news_{article_id}_{n_idx}"):
                                delete_news_idx = n_idx
                        with col_news_2:
                            if n_idx > 0 and st.button("🔀 Fusionner avec la précédente", use_container_width=True, key=f"merge_news_{article_id}_{n_idx}"):
                                merge_news_idx = n_idx

                if merge_news_idx is not None:
                    structured_news[merge_news_idx - 1]["sections"].extend(
                        structured_news[merge_news_idx].get("sections", [])
                    )
                    structured_news.pop(merge_news_idx)
                    st.rerun()

                if delete_news_idx is not None:
                    structured_news.pop(delete_news_idx)
                    st.rerun()
            else:
                st.caption("Aucune news structurée pour le moment")

            article["structured_news"] = structured_news

            st.divider()
            st.markdown("**Étape 3 — Final items (DB)**")
            col_step3_a, col_step3_b = st.columns([1, 2])
            with col_step3_a:
                if st.button("Relancer étape 3", use_container_width=True, key=f"step3_{article_id}"):
                    _run_step3(article)
                    st.rerun()
            with col_step3_b:
                st.caption("Items finaux prêts DB")

            final_items = article.get("final_items", [])
            if final_items:
                labels = [
                    "macro",
                    "markets",
                    "stocks",
                    "rates",
                    "fx",
                    "commodities",
                    "crypto",
                    "geopolitics",
                    "companies",
                    "indices",
                    "other",
                ]

                for f_idx, item in enumerate(final_items):
                    with st.expander(f"Final item {f_idx + 1}", expanded=False):
                        title_key = f"final_title_{article_id}_{f_idx}"
                        content_key = f"final_content_{article_id}_{f_idx}"
                        label_key = f"final_label_{article_id}_{f_idx}"
                        importance_key = f"final_importance_{article_id}_{f_idx}"

                        if title_key not in st.session_state:
                            st.session_state[title_key] = item.get("title", "")
                        if content_key not in st.session_state:
                            st.session_state[content_key] = item.get("content", "")
                        if label_key not in st.session_state:
                            current_label = item.get("label", "other")
                            if current_label not in labels:
                                current_label = "other"
                            st.session_state[label_key] = current_label
                        if importance_key not in st.session_state:
                            try:
                                importance_value = int(item.get("importance", 1) or 1)
                            except (TypeError, ValueError):
                                importance_value = 1
                            st.session_state[importance_key] = max(1, min(5, importance_value))

                        st.text_input("Titre", key=title_key)
                        st.text_area("Contenu", key=content_key, height=140)
                        st.selectbox("Label", labels, key=label_key)
                        st.slider("Importance", 1, 5, key=importance_key)

                        item["title"] = st.session_state[title_key]
                        item["content"] = st.session_state[content_key]
                        item["label"] = st.session_state[label_key]
                        item["importance"] = st.session_state[importance_key]
                        item["source_type"] = "hand_text"

                if st.button("✅ Valider et envoyer CET article en DB", use_container_width=True, key=f"send_{article_id}"):
                    enriched_items = enrich_raw_items(
                        final_items,
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
            else:
                st.caption("Aucun final_item pour le moment")


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
