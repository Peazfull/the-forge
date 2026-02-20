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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        /* Couleurs boutons - Style clair sans border */
        --button-primary: #fffdf4;
        --button-text: #1f2937;
        --button-hover: #fef9e7;
        
        /* Couleurs accents (progress bars, badges, borders) - Violet */
        --accent: #5E17EB;
        --accent-light: #ede9fe;
        
        /* Couleurs grises */
        --gray-50: #f9fafb;
        --gray-100: #f3f4f6;
        --gray-200: #e5e7eb;
        --gray-600: #4b5563;
        --gray-700: #374151;
        --gray-900: #111827;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
    }

    .section-header {
        margin: 1rem 0 0.75rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid var(--gray-200);
    }

    .section-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--gray-700);
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .section-title--small {
        font-size: 0.65rem;
    }

    .stat-card {
        background: #fff;
        border: 1px solid var(--gray-200);
        border-left: 3px solid var(--accent);
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
    }

    .stat-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--gray-900);
        margin: 0;
        line-height: 1;
    }

    .stat-label {
        font-size: 0.75rem;
        color: var(--gray-600);
        margin-top: 0.35rem;
    }

    .control-card {
        background: #fff;
        border-radius: 8px;
        padding: 0.9rem;
        border: 1px solid var(--gray-200);
        height: 100%;
    }

    .control-card-header {
        margin-bottom: 0.35rem;
    }

    .control-card-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--gray-900);
        margin: 0;
    }

    .control-card-subtitle {
        font-size: 0.75rem;
        color: var(--gray-600);
        margin: 0 0 0.75rem 0;
    }

    .status-badge {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        background: var(--accent-light);
        color: var(--accent);
        border: 1px solid var(--accent);
    }

    .status-success,
    .status-running,
    .status-warning,
    .status-error {
        background: var(--accent-light);
        color: var(--accent);
        border: 1px solid var(--accent);
    }

    .stProgress > div > div > div {
        background: var(--accent);
    }

    .stButton > button {
        background: var(--button-primary) !important;
        color: var(--button-text) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }
    
    .stButton > button:hover {
        background: var(--button-hover) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08) !important;
    }
    }

    .stButton > button:hover {
        opacity: 0.92;
    }

    .stSelectbox label {
        font-size: 0.8rem !important;
        color: var(--gray-600);
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
    # ======================================================
    # HERO SECTION
    # ======================================================
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("front/layout/assets/Theforge_logo.png", width=400)
    
    # Quick Stats Cards
    try:
        supabase = get_supabase()
        stats = get_brew_items_stats()
        enrich_stats = get_enrichment_stats()
        score_stats = get_scoring_stats()
        
        total_items = stats.get("count", 0)
        enriched_items = enrich_stats.get("enriched_items", 0) if enrich_stats.get("status") == "success" else 0
        scored_items = score_stats.get("scored_items", 0) if score_stats.get("status") == "success" else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{total_items}</div>
                <div class="stat-label">Bulletins</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{enriched_items}</div>
                <div class="stat-label">Enrichis</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{scored_items}</div>
                <div class="stat-label">Scorés</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_score = score_stats.get("average_score", 0) if score_stats.get("status") == "success" else 0
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{avg_score}</div>
                <div class="stat-label">Score moyen</div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erreur chargement stats : {str(e)}")
    
    # ======================================================
    # DATABASE STATUS
    # ======================================================
    
    st.markdown("""
    <div class="section-header">
        <h5 class="section-title section-title--small">Base de données</h5>
    </div>
    """, unsafe_allow_html=True)

    try:
        supabase = get_supabase()
        supabase.table("brew_items").select("id").limit(1).execute()

        stats = get_brew_items_stats()

        if "error" in stats:
            st.markdown('<span class="status-badge status-error">Erreur</span>', unsafe_allow_html=True)
            st.error(f"Erreur DB : {stats['error']}")
        else:
            if stats["count"] == 0:
                st.markdown('<span class="status-badge status-success">Connecté</span>', unsafe_allow_html=True)
                st.info("Aucun bulletin en base")
            else:
                st.markdown('<span class="status-badge status-success">Connecté</span>', unsafe_allow_html=True)
                st.success(
                    f"{stats['count']} bulletins · {format_datetime(stats['min_date'])} → {format_datetime(stats['max_date'])}"
                )

        if st.button("Clear DB", use_container_width=False):
            result = brew_items_erase()

            if result["status"] == "success":
                st.success(f"DB nettoyée · {result['deleted']} éléments supprimés")
                st.rerun()
            else:
                st.error(f"Erreur suppression : {result.get('message')}")

    except Exception as e:
        st.markdown('<span class="status-badge status-error">❌ ERREUR</span>', unsafe_allow_html=True)
        st.error(f"Connexion Supabase : {str(e)}")

    # ======================================================
    # CONTROL PANEL - BREWERY & MINISTRY
    # ======================================================
    
    st.markdown("""
    <div class="section-header">
        <h5 class="section-title section-title--small">Control Panel</h5>
    </div>
    """, unsafe_allow_html=True)
    
    col_nl, col_mega, col_ministry = st.columns(3)
    
    # ---------- NL BREWERY ----------
    with col_nl:
        st.markdown('<span class="status-badge status-warning">IDLE</span>', unsafe_allow_html=True)
        st.markdown("""
        <div class="control-card">
            <div class="control-card-header">
                <h5 class="control-card-title">NL Brewery</h5>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Lancer NL Brewery", use_container_width=True, type="primary", key="nl_brewery_btn"):
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
                    eta_line.caption(f"⏱️ {format_duration(eta_sec)}")

            with st.spinner("NL Brewery en cours…"):
                result = run_full_nl_brewery(last_hours=20, progress_cb=_update_progress)

            if result.get("status") == "success":
                st.success(f"✅ Terminé · {result.get('inserted', 0)} items")
            else:
                st.error("❌ Erreur process")
                st.caption(result.get("message", "Erreur inconnue"))

            errors = result.get("errors") or []
            if errors:
                st.caption("⚠️ Erreurs :")
                for err in errors[:5]:
                    st.write(f"• {err}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ---------- MEGA JOB ----------
    with col_mega:
        mega_job = get_mega_job()
        mega_status = mega_job.get_status()
        
        status_color = "success" if mega_status.get("state") == "completed" else (
            "running" if mega_status.get("state") == "running" else "warning"
        )
        status_text = mega_status.get("state", "idle").upper()
        
        st.markdown(f'<span class="status-badge status-{status_color}">{status_text}</span>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="control-card">
            <div class="control-card-header">
                <h5 class="control-card-title">Mega Job</h5>
            </div>
        """, unsafe_allow_html=True)
        
        col_mega_20h, col_mega_6h = st.columns(2)
        with col_mega_20h:
            launch_20h = st.button("20h", use_container_width=True, type="primary", key="mega_20h")
        with col_mega_6h:
            launch_6h = st.button("6h", use_container_width=True, key="mega_6h")

        with st.expander("⚙️ Réglages (performance)", expanded=False):
            st.caption("Augmente progressivement. Trop haut peut provoquer des 429 (rate limit).")
            col_a, col_b = st.columns(2)
            with col_a:
                mega_batch_size = st.number_input(
                    "Batch size",
                    min_value=1,
                    max_value=50,
                    value=5,
                    step=1,
                    key="mega_batch_size",
                )
                mega_firecrawl_workers = st.number_input(
                    "Firecrawl concurrency",
                    min_value=1,
                    max_value=10,
                    value=3,
                    step=1,
                    key="mega_firecrawl_concurrency",
                )
            with col_b:
                mega_llm_workers = st.number_input(
                    "Structure concurrency",
                    min_value=1,
                    max_value=6,
                    value=3,
                    step=1,
                    key="mega_llm_concurrency",
                )

        if launch_20h or launch_6h:
            if mega_status.get("state") == "running":
                st.warning("⚠️ Déjà en cours")
            else:
                hours = 6 if launch_6h else 20
                with st.spinner("Collecte URLs…"):
                    urls, statuses = collect_mega_urls(mega_hours=hours)
                if not urls:
                    st.warning("Aucune URL")
                else:
                    config = MegaJobConfig(
                        source_name="Mega Job Multi-Sources",
                        source_link="",
                        remove_buffer_after_success=False,
                        dry_run=False,
                        batch_size=int(st.session_state.get("mega_batch_size", 5)),
                        firecrawl_concurrency=int(st.session_state.get("mega_firecrawl_concurrency", 3)),
                        llm_concurrency=int(st.session_state.get("mega_llm_concurrency", 3)),
                    )
                    mega_job.set_config(config)
                    mega_job.start_auto_scraping(urls)
                    st.success(f"✅ Lancé ({hours}h) · {len(urls)} URL(s)")
                    st.rerun()

        if mega_status.get("state") == "running":
            if st.button("⏹️ Stop", use_container_width=True, key="mega_stop"):
                mega_job.stop()
                st.rerun()
            progress = mega_status.get("current_index", 0) / max(mega_status.get("total", 1), 1)
            st.progress(progress)
            st.caption(f"📊 {mega_status.get('current_index', 0)}/{mega_status.get('total', 0)} · ✅ {mega_status.get('processed', 0)}")
            time.sleep(1)
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ---------- THE MINISTRY ----------
    with col_ministry:
        st.markdown('<span class="status-badge status-warning">IDLE</span>', unsafe_allow_html=True)
        st.markdown("""
        <div class="control-card">
            <div class="control-card-header">
                <h5 class="control-card-title">The Ministry</h5>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Lancer Ministry", use_container_width=True, type="primary", key="ministry_btn"):
            # Enrich
            enrich_progress = st.progress(0)
            enrich_status = st.empty()
            enrich_items = fetch_ministry_enrich_items()
            enrich_total = len(enrich_items)
            enrich_success = 0
            enrich_errors = 0

            if enrich_total == 0:
                enrich_status.info("✓ Aucun à enrichir")
                enrich_progress.progress(1.0)
            else:
                for idx, item in enumerate(enrich_items, start=1):
                    enrich_status.text(f"Enrich {idx}/{enrich_total}")
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
                score_status.info("✓ Aucun à scorer")
                score_progress.progress(1.0)
            else:
                for idx, item in enumerate(score_items, start=1):
                    score_status.text(f"Score {idx}/{score_total}")
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

            st.success(f"✅ Terminé · Enrich {enrich_success}/{enrich_total} · Score {score_success}/{score_total}")
            if enrich_errors or score_errors:
                st.warning(f"⚠️ Erreurs: {enrich_errors + score_errors}")
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ======================================================
    # ANALYTICS DASHBOARD
    # ======================================================
    
    st.markdown("""
    <div class="section-header">
        <h5 class="section-title section-title--small">Analytics</h5>
    </div>
    """, unsafe_allow_html=True)
    
    # Récupération des stats
    stats_enrich = get_enrichment_stats()
    stats_score = get_scoring_stats()
    
    # Layout en 4 colonnes pour les métriques principales
    col1, col2, col3, col4 = st.columns(4)
    if stats_enrich.get("status") == "success":
        by_tags = stats_enrich.get("by_tags", {})
        total_items = stats_enrich.get("total_items", 0)
        enriched_items = stats_enrich.get("enriched_items", 0)
    else:
        by_tags = {}
        total_items = "—"
        enriched_items = "—"

    if stats_score.get("status") == "success":
        scored_items = stats_score.get("scored_items", 0)
        average_score = stats_score.get("average_score", 0)
    else:
        scored_items = "—"
        average_score = "—"

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{total_items}</div>
            <div class="stat-label">Total</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{enriched_items}</div>
            <div class="stat-label">Enrichis</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{scored_items}</div>
            <div class="stat-label">Scorés</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{average_score}</div>
            <div class="stat-label">Moyenne</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Distribution par catégories
    if stats_enrich.get("status") == "success":
        bourse_total = by_tags.get("BOURSE", 0)
        bourse_pea = 0
        try:
            supabase = get_supabase()
            bourse_pea_resp = (
                supabase.table("brew_items")
                .select("id", count="exact")
                .eq("tags", "BOURSE")
                .eq("labels", "PEA")
                .execute()
            )
            bourse_pea = bourse_pea_resp.count or 0
        except Exception:
            bourse_pea = 0

        bourse_no_pea = max(bourse_total - bourse_pea, 0)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{by_tags.get("ECO", 0)}</div>
                <div class="stat-label">ECO</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{bourse_no_pea}</div>
                <div class="stat-label">BOURSE</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{bourse_pea}</div>
                <div class="stat-label">PEA</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{by_tags.get("CRYPTO", 0)}</div>
                <div class="stat-label">CRYPTO</div>
            </div>
            """, unsafe_allow_html=True)

    # ======================================================
    # BREW ITEMS PREVIEW & EDIT
    # ======================================================
    
    st.markdown("""
    <div class="section-header">
        <h5 class="section-title">Brew Items</h5>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("Filtrer et modifier les scores")

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
            index=1,
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
        st.info("Aucun item trouvé avec ces filtres.")
    else:
        import pandas as pd

        df = pd.DataFrame(items)
        df = df.reset_index(drop=True)
        df["title_short"] = df["title"].fillna("").str[:60] + "..."
        df["content_short"] = df["content"].fillna("").str[:100] + "..."
        df["score_display"] = df["score_global"].fillna("—")

        df_table = df[["title_short", "content_short", "tags", "score_display"]]
        df_table.columns = ["Titre", "Contenu", "Tag", "Score"]

        event = st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
            height=350,
            on_select="rerun",
            selection_mode="single-row",
        )

        if event.selection and "rows" in event.selection and len(event.selection["rows"]) > 0:
            selected_idx = event.selection["rows"][0]
            selected_item = df.iloc[selected_idx]

            st.markdown("""
            <div class="section-header">
                <h5 class="section-title">Édition du score</h5>
            </div>
            """, unsafe_allow_html=True)

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
        st.image("front/layout/assets/pixel_epee.gif", width=250)
