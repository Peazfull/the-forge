import streamlit as st
from front.layout.sidebar import render_sidebar
from db.supabase_client import get_supabase
from services.raw_storage.brew_items_read import get_brew_items_stats
from services.raw_storage.brew_items_erase import brew_items_erase
from services.nl_brewery.nl_brewery_service import run_full_nl_brewery
from services.enrichment.enrichment_service import enrich_single_item, get_enrichment_stats
from services.scoring.scoring_service import fetch_items_to_score, score_single_item
from services.scoring.update_score import update_item_score
from services.scoring.scoring_service import get_scoring_stats
from services.news_brewery.mega_job import MegaJobConfig, get_mega_job
from services.news_brewery.sources_registry import collect_mega_urls
import os
import time
from datetime import datetime, timedelta
from typing import Optional

def format_datetime(dt_str: Optional[str]) -> str:
    if not dt_str:
        return "—"
    try:
        return datetime.fromisoformat(dt_str).strftime("%d/%m/%Y · %H:%M")
    except Exception:
        return dt_str


def format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "—"
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def fetch_ministry_enrich_items() -> list:
    try:
        supabase = get_supabase()
        response = (
            supabase.table("brew_items")
            .select("id, title, content")
            .is_("labels", "null")
            .is_("tags", "null")
            .execute()
        )
        return response.data or []
    except Exception:
        return []


# ======================================================
# PAGE CONFIG
# ======================================================

st.set_page_config(
    page_title="THE FORGE",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# GLOBAL STYLES
# ======================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
# SESSION STATE
# ======================================================

if "current_page" not in st.session_state:
    st.session_state.current_page = None

# ======================================================
# SIDEBAR
# ======================================================

render_sidebar()

# ======================================================
# ROUTER
# ======================================================

if st.session_state.current_page:
    try:
        page_path = os.path.join(
            os.path.dirname(__file__),
            st.session_state.current_page + ".py"
        )

        if os.path.exists(page_path):
            with open(page_path, "r", encoding="utf-8") as f:
                code = f.read()
            exec(code, {"st": st, "__file__": page_path})
        else:
            st.error(f"Page non trouvée : {page_path}")
            st.session_state.current_page = None

    except Exception as e:
        st.error(f"Erreur lors du chargement de la page : {e}")
        st.session_state.current_page = None

# ======================================================
# HOME
# ======================================================

else:
    # ---------- LOGO ----------
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("front/layout/assets/Theforge_logo.png", width=500)

    st.divider()

    # ---------- DB STATUS ----------
    st.write("🗄️ Statut base de données")

    col_status, col_clear = st.columns([3, 1])

    try:
        supabase = get_supabase()
        supabase.table("brew_items").select("id").limit(1).execute()

        stats = get_brew_items_stats()

        with col_status:
            if "error" in stats:
                st.error(f"Erreur DB : {stats['error']}")
            else:
                if stats["count"] == 0:
                    st.success("Connexion DB OK · Aucun bulletin en base")
                else:
                    st.success(
                        f"Connexion DB OK · {stats['count']} bulletins "
                        f"({format_datetime(stats['min_date'])} → {format_datetime(stats['max_date'])})"
                    )

        with col_clear:
            if st.button("🧹 Clear DB", use_container_width=True):
                result = brew_items_erase()

                if result["status"] == "success":
                    st.success(f"DB nettoyée · {result['deleted']} éléments supprimés")
                    st.rerun()
                else:
                    st.error(f"Erreur suppression : {result.get('message')}")

    except Exception as e:
        st.error(f"❌ Connexion Supabase : ERREUR ({str(e)})")

    st.divider()

    # ---------- NL BREWERY QUICK RUN ----------
    st.write("📨 NL Brewery — Exécution rapide")
    st.caption("Scrape des newsletters des 20 dernières heures, pipeline IA complet, insertion DB.")

    if st.button("🚀 Lancer NL Brewery", use_container_width=True, type="primary"):
        progress_bar = st.progress(0)
        status_line = st.empty()
        eta_line = st.empty()

        def _update_progress(payload: dict) -> None:
            progress = payload.get("progress")
            if progress is not None:
                progress_bar.progress(min(max(progress, 0), 1))
            message = payload.get("message")
            if message:
                status_line.write(message)
            eta_sec = payload.get("eta_sec")
            if eta_sec is not None:
                eta_line.caption(f"Temps estimé restant : {format_duration(eta_sec)}")

        with st.spinner("NL Brewery en cours…"):
            result = run_full_nl_brewery(last_hours=20, progress_cb=_update_progress)

        if result.get("status") == "success":
            st.success(f"✅ NL Brewery terminé · {result.get('inserted', 0)} items insérés")
        else:
            st.error("❌ Erreur durant le process NL Brewery")
            st.caption(result.get("message", "Erreur inconnue"))

        errors = result.get("errors") or []
        if errors:
            st.caption("Erreurs détectées :")
            for err in errors[:5]:
                st.write(f"⚠️ {err}")

    st.divider()

    # ---------- MEGA JOB QUICK RUN ----------
    st.write("🧭 Mega Job — Exécution rapide")
    st.caption("Collecte toutes les sources, 20 dernières heures, insertion automatique en DB.")

    mega_job = get_mega_job()
    mega_status = mega_job.get_status()

    col_mega_20h, col_mega_6h = st.columns(2)
    with col_mega_20h:
        launch_20h = st.button("🚀 Lancer Mega Job (20h)", use_container_width=True, type="primary")
    with col_mega_6h:
        launch_6h = st.button("⚡ Lancer Mega Job (6h)", use_container_width=True)

    if launch_20h or launch_6h:
        if mega_status.get("state") == "running":
            st.warning("Mega Job déjà en cours.")
        else:
            hours = 6 if launch_6h else 20
            with st.spinner("Collecte des URLs en cours…"):
                urls, statuses = collect_mega_urls(mega_hours=hours)
            if not urls:
                st.warning("Aucune URL trouvée.")
            else:
                config = MegaJobConfig(
                    source_name="Mega Job Multi-Sources",
                    source_link="",
                    remove_buffer_after_success=False,
                    dry_run=False,
                )
                mega_job.set_config(config)
                mega_job.start_auto_scraping(urls)
                st.success(f"✅ Mega Job lancé ({hours}h) · {len(urls)} URL(s)")
                st.rerun()

    if mega_status.get("state") == "running":
        st.divider()
        if st.button("⏹️ Stop Mega Job", use_container_width=True):
            mega_job.stop()
            st.rerun()
        progress = mega_status.get("current_index", 0) / max(mega_status.get("total", 1), 1)
        st.progress(progress)
        st.caption(f"📊 Progression : {mega_status.get('current_index', 0)}/{mega_status.get('total', 0)} URLs")
        st.caption(f"✅ Traités : {mega_status.get('processed', 0)} · ⏭️ Ignorés : {mega_status.get('skipped', 0)}")

        if mega_status.get("last_log"):
            st.info(mega_status.get("last_log"))

        if mega_status.get("errors"):
            with st.expander(f"⚠️ Erreurs ({len(mega_status.get('errors'))})", expanded=False):
                for err in mega_status.get("errors")[-10:]:
                    st.warning(err)

        time.sleep(1)
        st.rerun()

    elif mega_status.get("state") == "completed":
        st.success(f"✅ Mega Job terminé · {mega_status.get('processed', 0)} articles traités")
    elif mega_status.get("state") == "failed":
        st.error("❌ Mega Job échoué")
    elif mega_status.get("state") == "stopped":
        st.warning("⏹️ Mega Job arrêté")

    st.divider()

    # ---------- THE MINISTRY QUICK RUN ----------
    st.write("🏛️ The Ministry — Exécution rapide")
    st.caption("Enrich (sans tag/label) puis score (sans score).")

    if st.button("🏛️ Lancer The Ministry", use_container_width=True, type="primary"):
        # Enrich
        enrich_progress = st.progress(0)
        enrich_status = st.empty()
        enrich_items = fetch_ministry_enrich_items()
        enrich_total = len(enrich_items)
        enrich_success = 0
        enrich_errors = 0

        if enrich_total == 0:
            enrich_status.info("Aucun item à enrichir (tags/labels déjà présents).")
            enrich_progress.progress(1.0)
        else:
            for idx, item in enumerate(enrich_items, start=1):
                enrich_status.text(f"Enrich {idx}/{enrich_total} · {item.get('title','')[:60]}")
                result = enrich_single_item(
                    item.get("id"),
                    item.get("title", ""),
                    item.get("content", "")
                )
                if result.get("status") == "success":
                    enrich_success += 1
                else:
                    enrich_errors += 1
                enrich_progress.progress(idx / enrich_total)

        # Score
        score_progress = st.progress(0)
        score_status = st.empty()
        score_items = fetch_items_to_score(limit=None, force_all=False)
        score_total = len(score_items)
        score_success = 0
        score_errors = 0

        if score_total == 0:
            score_status.info("Aucun item à scorer (déjà scoré ou non enrichi).")
            score_progress.progress(1.0)
        else:
            for idx, item in enumerate(score_items, start=1):
                score_status.text(f"Score {idx}/{score_total} · {item.get('title','')[:60]}")
                result = score_single_item(
                    item.get("id"),
                    item.get("title", ""),
                    item.get("content", ""),
                    item.get("tags"),
                    item.get("labels"),
                    item.get("entities"),
                    item.get("source_type"),
                )
                if result.get("status") == "success":
                    score_success += 1
                else:
                    score_errors += 1
                score_progress.progress(idx / score_total)

        st.success(
            "✅ The Ministry terminé · "
            f"Enrich {enrich_success}/{enrich_total} · "
            f"Score {score_success}/{score_total}"
        )
        if enrich_errors or score_errors:
            st.warning(f"⚠️ Erreurs enrich: {enrich_errors} · score: {score_errors}")

    st.divider()

    # ---------- THE MINISTRY DASHBOARD ----------
    st.write("📊 The Ministry — Dashboard")
    col_enrich, col_score = st.columns(2)

    with col_enrich:
        stats_enrich = get_enrichment_stats()
        if stats_enrich.get("status") == "success":
            by_tags = stats_enrich.get("by_tags", {})
            st.caption("Enrich")
            cols = st.columns(4)
            with cols[0]:
                st.metric("Total", stats_enrich.get("total_items", 0))
            with cols[1]:
                st.metric("Enrichis", stats_enrich.get("enriched_items", 0))
            with cols[2]:
                st.metric("Eco", by_tags.get("ECO", 0))
            with cols[3]:
                st.metric("Bourse", by_tags.get("BOURSE", 0))
            st.caption(f"Crypto: {by_tags.get('CRYPTO', 0)}")
        else:
            st.error(stats_enrich.get("message", "Erreur stats enrich"))

    with col_score:
        stats_score = get_scoring_stats()
        if stats_score.get("status") == "success":
            st.caption("Score")
            cols = st.columns(4)
            with cols[0]:
                st.metric("Total", stats_score.get("total_items", 0))
            with cols[1]:
                st.metric("Scorés", stats_score.get("scored_items", 0))
            with cols[2]:
                st.metric("Non scorés", stats_score.get("not_scored", 0))
            with cols[3]:
                st.metric("Moyenne", stats_score.get("average_score", 0))
        else:
            st.error(stats_score.get("message", "Erreur stats score"))

    st.divider()

    # ---------- BREW ITEMS PREVIEW & EDIT ----------
    st.write("🧾 Brew Items — Preview & Édition")
    st.caption("Filtrer par date, tag, label et modifier le score manuellement.")

    col_tag, col_label, col_date, col_sort = st.columns(4)
    with col_tag:
        filter_tag = st.selectbox(
            "Tag",
            options=["Tous", "ECO", "BOURSE", "CRYPTO"],
            index=0,
            label_visibility="collapsed",
            placeholder="Tag",
        )
    with col_label:
        filter_label = st.selectbox(
            "Label",
            options=["Tous", "Eco-Geopol", "Indices", "PEA", "Action", "Commodités", "Crypto"],
            index=0,
            label_visibility="collapsed",
            placeholder="Label",
        )
    with col_date:
        filter_date = st.selectbox(
            "Date",
            options=["Toutes", "Dernières 24h"],
            index=0,
            label_visibility="collapsed",
            placeholder="Date",
        )
    with col_sort:
        filter_sort = st.selectbox(
            "Tri",
            options=["Score ↓", "Date ↓"],
            index=0,
            label_visibility="collapsed",
            placeholder="Tri",
        )

    try:
        supabase = get_supabase()
        query = supabase.table("brew_items").select(
            "id, title, content, tags, labels, score_global, processed_at"
        )

        if filter_tag != "Tous":
            query = query.eq("tags", filter_tag)
        if filter_label != "Tous":
            query = query.eq("labels", filter_label)
        if filter_date == "Dernières 24h":
            since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            query = query.gte("processed_at", since)

        if filter_sort == "Score ↓":
            query = query.order("score_global", desc=True)
            query = query.order("processed_at", desc=True)
        else:
            query = query.order("processed_at", desc=True)

        response = query.execute()
        items = response.data or []
    except Exception as e:
        items = []
        st.error(f"Erreur DB : {str(e)}")

    if not items:
        st.caption("Aucun item trouvé avec ces filtres.")
    else:
        import pandas as pd

        df = pd.DataFrame(items)
        df = df.reset_index(drop=True)
        df["title_short"] = df["title"].fillna("").str[:50] + "..."
        df["content_short"] = df["content"].fillna("").str[:80] + "..."
        df["score_display"] = df["score_global"].fillna("—")

        df_table = df[["title_short", "content_short", "tags", "labels", "score_display"]]
        df_table.columns = ["Titre", "Contenu", "Tag", "Label", "Score"]

        event = st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
            height=450,
            on_select="rerun",
            selection_mode="single-row",
        )

        if event.selection and "rows" in event.selection and len(event.selection["rows"]) > 0:
            selected_idx = event.selection["rows"][0]
            selected_item = df.iloc[selected_idx]

            st.markdown("")
            st.markdown("#### ✏️ Édition du score")

            col_left, col_right = st.columns([2, 1])
            with col_left:
                st.markdown(f"**{selected_item['title']}**")
                st.markdown(selected_item["content"])
                st.caption(f"Tag: {selected_item.get('tags') or '—'} · Label: {selected_item.get('labels') or '—'}")
                st.caption(f"Date: {format_datetime(selected_item.get('processed_at'))}")

            with col_right:
                current_score = selected_item.get("score_global")
                score_value = st.number_input(
                    "Score",
                    min_value=0,
                    max_value=100,
                    value=int(current_score) if isinstance(current_score, (int, float)) else 0,
                    step=1,
                    key=f"home_score_{selected_item['id']}",
                )
                if st.button("✅ Enregistrer le score", use_container_width=True):
                    result = update_item_score(selected_item["id"], int(score_value))
                    if result.get("status") == "success":
                        st.success(result.get("message", "Score mis à jour"))
                        st.rerun()
                    else:
                        st.error(result.get("message", "Erreur DB"))

    # ---------- GIF ----------
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col3:
        st.image("front/layout/assets/pixel_epee.gif", width=300)
