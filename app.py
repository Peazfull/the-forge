import streamlit as st
from front.layout.sidebar import render_sidebar
from db.supabase_client import get_supabase
from services.raw_storage.brew_items_read import get_brew_items_stats
from services.raw_storage.brew_items_erase import brew_items_erase
from services.nl_brewery.nl_brewery_service import run_full_nl_brewery
from services.news_brewery.mega_job import MegaJobConfig, get_mega_job
from services.news_brewery.sources_registry import collect_mega_urls
import os
import time
from datetime import datetime
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

    # ---------- GIF ----------
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col3:
        st.image("front/layout/assets/pixel_epee.gif", width=300)
