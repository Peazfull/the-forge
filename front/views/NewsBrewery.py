import time
import streamlit as st
from services.news_brewery.bfm_bourse_job import JobConfig, get_bfm_job
from services.news_brewery.beincrypto_job import JobConfig as BeInJobConfig, get_beincrypto_job
from services.news_brewery.boursedirect_job import JobConfig as BourseDirectJobConfig, get_boursedirect_job
from services.news_brewery.boursedirect_indices_job import (
    JobConfig as BourseDirectIndicesJobConfig,
    get_boursedirect_indices_job,
)
from services.news_brewery.boursier_economie_job import (
    JobConfig as BoursierEconomieJobConfig,
    get_boursier_economie_job,
)
from services.news_brewery.rss_utils import (
    fetch_beincrypto_dom_items,
    fetch_boursedirect_dom_items,
    fetch_boursier_dom_items,
    fetch_dom_items,
    fetch_rss_items,
    merge_article_items,
)
from services.raw_storage.raw_news_service import fetch_raw_news


st.title("🗞️ NEWS Brewery")
st.divider()

job = get_bfm_job()
status = job.get_status()

if "news_rss_candidates" not in st.session_state:
    st.session_state.news_rss_candidates = []
if "news_show_json" in st.session_state:
    st.session_state.pop("news_show_json", None)
if "news_show_json_state" not in st.session_state:
    st.session_state.news_show_json_state = False
if "news_json_ready" not in st.session_state:
    st.session_state.news_json_ready = False
if "bein_rss_candidates" not in st.session_state:
    st.session_state.bein_rss_candidates = []
if "bein_show_json_state" not in st.session_state:
    st.session_state.bein_show_json_state = False
if "bein_json_ready" not in st.session_state:
    st.session_state.bein_json_ready = False
if "boursedirect_rss_candidates" not in st.session_state:
    st.session_state.boursedirect_rss_candidates = []
if "boursedirect_show_json_state" not in st.session_state:
    st.session_state.boursedirect_show_json_state = False
if "boursedirect_json_ready" not in st.session_state:
    st.session_state.boursedirect_json_ready = False
if "boursedirect_indices_rss_candidates" not in st.session_state:
    st.session_state.boursedirect_indices_rss_candidates = []
if "boursedirect_indices_show_json_state" not in st.session_state:
    st.session_state.boursedirect_indices_show_json_state = False
if "boursedirect_indices_json_ready" not in st.session_state:
    st.session_state.boursedirect_indices_json_ready = False
if "boursier_economie_rss_candidates" not in st.session_state:
    st.session_state.boursier_economie_rss_candidates = []
if "boursier_economie_show_json_state" not in st.session_state:
    st.session_state.boursier_economie_show_json_state = False
if "boursier_economie_json_ready" not in st.session_state:
    st.session_state.boursier_economie_json_ready = False

# =========================
# JOB — BFM BOURSE
# =========================
with st.expander("▸ Job — BFM Bourse", expanded=False):
    col_open, col_launch, col_clear = st.columns([2, 1, 1])

    with col_open:
        st.link_button("🔗 Ouvrir l’URL", "https://www.tradingsat.com/actualites/")
    with col_launch:
        launch = st.button("▶️ Lancer", use_container_width=True, key="news_bfm_launch")
    with col_clear:
        clear_job = st.button("🧹 Clear", use_container_width=True, key="news_bfm_clear")

    with st.expander("Fenêtre temporelle", expanded=True):
        mode = st.radio(
            "Mode",
            options=["Aujourd’hui", "Dernières X heures"],
            horizontal=True,
            index=1,
            key="news_mode"
        )
        hours_window = st.slider(
            "Dernières X heures",
            min_value=1,
            max_value=24,
            value=6,
            step=1,
            key="news_hours_window"
        )

    with st.expander("Settings", expanded=False):
        st.markdown("**Limites**")
        col_max_total, col_max_per = st.columns(2)
        with col_max_total:
            max_articles_total = st.number_input(
                "Max articles total",
                min_value=1,
                max_value=100,
                value=20,
                step=1,
                key="news_max_total"
            )
        with col_max_per:
            max_articles_per_bulletin = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=20,
                value=20,
                step=1,
                key="news_max_per"
            )

        st.markdown("**Human behavior**")
        col_scroll_min, col_scroll_max = st.columns(2)
        with col_scroll_min:
            scroll_min_px = st.number_input(
                "Scroll min px",
                min_value=100,
                max_value=2000,
                value=400,
                step=50,
                key="news_scroll_min"
            )
        with col_scroll_max:
            scroll_max_px = st.number_input(
                "Scroll max px",
                min_value=200,
                max_value=4000,
                value=1200,
                step=50,
                key="news_scroll_max"
            )

        col_page_min, col_page_max = st.columns(2)
        with col_page_min:
            min_page_time = st.number_input(
                "Temps min page (s)",
                min_value=1,
                max_value=120,
                value=10,
                step=1,
                key="news_page_min"
            )
        with col_page_max:
            max_page_time = st.number_input(
                "Temps max page (s)",
                min_value=2,
                max_value=180,
                value=45,
                step=1,
                key="news_page_max"
            )

        col_wait_min, col_wait_max = st.columns(2)
        with col_wait_min:
            wait_min_action = st.number_input(
                "Wait min action (s)",
                min_value=0.1,
                max_value=5.0,
                value=0.6,
                step=0.1,
                key="news_wait_min"
            )
        with col_wait_max:
            wait_max_action = st.number_input(
                "Wait max action (s)",
                min_value=0.2,
                max_value=8.0,
                value=2.5,
                step=0.1,
                key="news_wait_max"
            )

        shuffle_urls = st.checkbox("Shuffle URLs", value=True, key="news_shuffle")

        dry_run = st.checkbox("DRY RUN", value=False, key="news_dry_run")

        st.markdown("**Safety**")
        col_err, col_timeout = st.columns(2)
        with col_err:
            max_consecutive_errors = st.number_input(
                "Max erreurs consécutives",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                key="news_max_errors"
            )
        with col_timeout:
            global_timeout_minutes = st.number_input(
                "Timeout global job (min)",
                min_value=1,
                max_value=60,
                value=15,
                step=1,
                key="news_timeout"
            )

        pause_on_captcha = st.checkbox(
            "Pause en cas de captcha/wall",
            value=True,
            key="news_pause_captcha"
        )
        remove_buffer = st.checkbox(
            "Supprimer buffer après succès",
            value=True,
            key="news_remove_buffer"
        )
        st.markdown("**Source URLs**")
        rss_feed_url = st.text_input(
            "RSS feed",
            value="https://www.tradingsat.com/rssfeed.php",
            key="news_rss_feed"
        )
        use_rss = st.checkbox("Mode RSS (prod)", value=True, key="news_use_rss")
        use_firecrawl = st.checkbox("Scraper articles via Firecrawl", value=True, key="news_use_firecrawl")
        rss_ignore_time_filter = st.checkbox(
            "Ignorer filtre temporel RSS",
            value=False,
            key="news_rss_ignore_time"
        )
        rss_use_dom_fallback = st.checkbox(
            "Compléter via DOM (Tout)",
            value=True,
            key="news_rss_dom_fallback"
        )
        headless = st.checkbox(
            "Headless (prod)",
            value=True,
            key="news_headless"
        )

    selected_urls = []
    if use_rss:
        col_clear, col_uncheck = st.columns(2)
        with col_clear:
            if st.button("🧹 Clear liste", use_container_width=True, key="news_rss_clear"):
                st.session_state.news_rss_candidates = []
                st.rerun()
        with col_uncheck:
            if st.button("☐ Décocher tout", use_container_width=True, key="news_rss_uncheck_all"):
                for idx in range(len(st.session_state.news_rss_candidates)):
                    st.session_state[f"news_rss_pick_{idx}"] = False
                st.rerun()

        if st.session_state.news_rss_candidates:
            st.caption("Sélectionne les articles à traiter :")
            for idx, item in enumerate(st.session_state.news_rss_candidates):
                label = f"{item.get('title','')}".strip() or item.get("url", "")
                key = f"news_rss_pick_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = True
                checked = st.checkbox(label, key=key)
                if checked:
                    selected_urls.append(item)
            st.caption(f"{len(selected_urls)} article(s) sélectionné(s)")
        else:
            st.caption("Clique sur Lancer pour charger la liste RSS.")

    if st.session_state.news_rss_candidates:
        if st.button("🧭 Scrapper les articles", use_container_width=True, key="news_scrape_articles"):
            if not selected_urls:
                st.error("Sélectionne au moins un article.")
            else:
                job.set_buffer_text("")
                job.json_preview_text = ""
                job.json_items = []
                st.session_state.news_show_json_state = False
                st.session_state.news_json_ready = False
                config = JobConfig(
                    entry_url="https://www.tradingsat.com/actualites/",
                    mode="today" if mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(hours_window),
                    max_articles_total=int(max_articles_total),
                    max_articles_per_bulletin=int(max_articles_per_bulletin),
                    scroll_min_px=int(scroll_min_px),
                    scroll_max_px=int(scroll_max_px),
                    min_page_time=int(min_page_time),
                    max_page_time=int(max_page_time),
                    wait_min_action=float(wait_min_action),
                    wait_max_action=float(wait_max_action),
                    shuffle_urls=bool(shuffle_urls),
                    dry_run=bool(dry_run),
                    max_consecutive_errors=int(max_consecutive_errors),
                    global_timeout_minutes=int(global_timeout_minutes),
                    pause_on_captcha=bool(pause_on_captcha),
                    remove_buffer_after_success=bool(remove_buffer),
                    headless=bool(headless),
                    use_rss=bool(use_rss),
                    rss_feed_url=rss_feed_url,
                    rss_ignore_time_filter=bool(rss_ignore_time_filter),
                    rss_use_dom_fallback=bool(rss_use_dom_fallback),
                    use_firecrawl=bool(use_firecrawl),
                    urls_override=selected_urls,
                )
                job.start(config)
                st.success("Scraping lancé.")
    if launch:
        if use_rss:
            job.set_buffer_text("")
            job.json_preview_text = ""
            job.json_items = []
            st.session_state.news_show_json_state = False
            st.session_state.news_json_ready = False
            rss_items = fetch_rss_items(
                feed_url=rss_feed_url,
                max_items=int(max_articles_total),
                mode="today" if mode == "Aujourd’hui" else "last_hours",
                hours_window=int(hours_window),
                ignore_time_filter=bool(rss_ignore_time_filter),
            )
            if rss_use_dom_fallback:
                dom_items = fetch_dom_items(
                    page_url="https://www.tradingsat.com/actualites/",
                    max_items=int(max_articles_total),
                    mode="today" if mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(hours_window),
                )
                st.session_state.news_rss_candidates = merge_article_items(
                    dom_items,
                    rss_items,
                    int(max_articles_total),
                )
            else:
                st.session_state.news_rss_candidates = rss_items
            job.status_log.append("🔎 URLs RSS chargées")
            st.rerun()
        else:
            st.warning("Mode RSS désactivé : active-le pour charger les URLs.")

    if clear_job:
        job.clear()
        st.session_state.news_rss_candidates = []
        st.session_state.news_show_json_state = False
        st.session_state.news_json_ready = False
        st.rerun()

    status = job.get_status()
    st.divider()
    st.caption(f"État : {status.get('state')}")
    total = int(status.get("total") or 0)
    processed = int(status.get("processed", 0))
    skipped = int(status.get("skipped", 0))
    started_at = status.get("started_at")
    last_log = status.get("last_log") or ""
    if total > 0:
        progress_value = min(max((processed + skipped) / total, 0.0), 1.0)
        st.progress(progress_value)
        st.caption(f"Progression : {processed + skipped}/{total}")
    st.caption(f"Traités : {processed} · Skipped : {skipped}")
    if started_at and (processed + skipped) > 0:
        elapsed = max(time.time() - float(started_at), 1.0)
        avg_per_item = elapsed / max(processed + skipped, 1)
        remaining = max(total - (processed + skipped), 0)
        eta_seconds = int(remaining * avg_per_item)
        st.caption(f"ETA estimée : ~{eta_seconds // 60}m {eta_seconds % 60}s")
    if last_log:
        st.caption(f"Dernier statut : {last_log}")
    if status.get("buffer_path"):
        st.caption(f"Buffer : {status.get('buffer_path')}")
    if status.get("state") in ("running", "paused"):
        st.info("Job en cours — rafraîchissement automatique activé.")
        time.sleep(2)
        st.rerun()

    # Statut compact (une seule ligne)
    if last_log:
        st.caption(f"Statut : {last_log}")
    if status.get("errors"):
        st.markdown("**Erreurs :**")
        for err in status.get("errors")[-3:]:
            st.write(f"⚠️ {err}")

    if status.get("buffer_text"):
        st.divider()
        st.markdown("**Preview concaténée (buffer)**")
        edited_buffer = st.text_area(
            label="",
            value=status.get("buffer_text", ""),
            height=320,
            key="news_buffer_editor"
        )
        col_json, col_clear_buf = st.columns(2)
        with col_json:
            if st.button("✅ Dédoublonner + JSON", use_container_width=True, key="news_finalize"):
                job.set_buffer_text(edited_buffer)
                result = job.finalize_buffer()
                if result.get("status") == "success":
                    st.success(f"{len(result.get('items', []))} items générés")
                    st.session_state.news_json_ready = True
                    st.session_state.news_show_json_state = False
                    status = job.get_status()
                else:
                    st.error(result.get("message", "Erreur JSON"))
        with col_clear_buf:
            if st.button("🧹 Clear buffer", use_container_width=True, key="news_clear_buffer"):
                job.set_buffer_text("")
                st.rerun()

    if st.session_state.news_json_ready and status.get("json_preview_text") and not st.session_state.news_show_json_state:
        if st.button("🧾 Afficher preview JSON", use_container_width=True, key="news_show_json_btn"):
            st.session_state.news_show_json_state = True
            st.rerun()

    if status.get("json_preview_text") and st.session_state.news_show_json_state:
        st.markdown("**Preview JSON**")
        edited_json = st.text_area(
            label="",
            value=status.get("json_preview_text", ""),
            height=350,
            key="news_json_editor"
        )
        col_send, col_clear_json = st.columns(2)
        with col_send:
            if st.button("✅ Envoyer en DB", use_container_width=True, key="news_send_db"):
                result = job.send_to_db()
                if result.get("status") == "success":
                    st.success(f"{result.get('inserted', 0)} items insérés en base")
                else:
                    st.error(result.get("message", "Erreur DB"))
        with col_clear_json:
            if st.button("🧹 Clear JSON", use_container_width=True, key="news_clear_json"):
                job.json_preview_text = ""
                job.json_items = []
                st.session_state.news_show_json_state = False
                st.session_state.news_json_ready = False
                st.rerun()

    st.divider()

# =========================
# JOB — BEINCRYPTO
# =========================
with st.expander("▸ Job — BeInCrypto", expanded=False):
    bein_job = get_beincrypto_job()
    col_open, col_launch, col_clear = st.columns([2, 1, 1])

    with col_open:
        st.link_button("🔗 Ouvrir l’URL", "https://fr.beincrypto.com/")
    with col_launch:
        bein_launch = st.button("▶️ Lancer", use_container_width=True, key="bein_launch")
    with col_clear:
        bein_clear = st.button("🧹 Clear", use_container_width=True, key="bein_clear")

    with st.expander("Fenêtre temporelle", expanded=True):
        bein_mode = st.radio(
            "Mode",
            options=["Aujourd’hui", "Dernières X heures"],
            horizontal=True,
            index=1,
            key="bein_mode",
        )
        bein_hours_window = st.slider(
            "Dernières X heures",
            min_value=1,
            max_value=24,
            value=6,
            step=1,
            key="bein_hours_window",
        )

    with st.expander("Settings", expanded=False):
        st.markdown("**Limites**")
        col_max_total, col_max_per = st.columns(2)
        with col_max_total:
            bein_max_articles_total = st.number_input(
                "Max articles total",
                min_value=1,
                max_value=100,
                value=20,
                step=1,
                key="bein_max_total",
            )
        with col_max_per:
            bein_max_articles_per = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=20,
                value=20,
                step=1,
                key="bein_max_per",
            )

        st.markdown("**Timing**")
        col_wait_min, col_wait_max = st.columns(2)
        with col_wait_min:
            bein_wait_min_action = st.number_input(
                "Wait min action (s)",
                min_value=0.1,
                max_value=5.0,
                value=0.6,
                step=0.1,
                key="bein_wait_min",
            )
        with col_wait_max:
            bein_wait_max_action = st.number_input(
                "Wait max action (s)",
                min_value=0.2,
                max_value=8.0,
                value=2.5,
                step=0.1,
                key="bein_wait_max",
            )

        bein_shuffle_urls = st.checkbox("Shuffle URLs", value=True, key="bein_shuffle")
        bein_dry_run = st.checkbox("DRY RUN", value=False, key="bein_dry_run")

        st.markdown("**Safety**")
        col_err, col_timeout = st.columns(2)
        with col_err:
            bein_max_consecutive_errors = st.number_input(
                "Max erreurs consécutives",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                key="bein_max_errors",
            )
        with col_timeout:
            bein_global_timeout_minutes = st.number_input(
                "Timeout global job (min)",
                min_value=1,
                max_value=60,
                value=15,
                step=1,
                key="bein_timeout",
            )

        bein_remove_buffer = st.checkbox(
            "Supprimer buffer après succès",
            value=True,
            key="bein_remove_buffer",
        )

        st.markdown("**Source URLs**")
        bein_rss_feed_url = st.text_input(
            "RSS feed",
            value="https://fr.beincrypto.com/feed/",
            key="bein_rss_feed",
        )
        bein_use_rss = st.checkbox("Mode RSS/DOM", value=True, key="bein_use_rss")
        bein_use_firecrawl = st.checkbox("Scraper articles via Firecrawl", value=True, key="bein_use_firecrawl")
        bein_rss_ignore_time_filter = st.checkbox(
            "Ignorer filtre temporel RSS",
            value=False,
            key="bein_rss_ignore_time",
        )
        bein_rss_use_dom_fallback = st.checkbox(
            "Compléter via DOM (bloc gauche)",
            value=True,
            key="bein_rss_dom_fallback",
        )

    bein_selected_urls = []
    if bein_use_rss:
        col_clear, col_uncheck = st.columns(2)
        with col_clear:
            if st.button("🧹 Clear liste", use_container_width=True, key="bein_rss_clear"):
                st.session_state.bein_rss_candidates = []
                st.rerun()
        with col_uncheck:
            if st.button("☐ Décocher tout", use_container_width=True, key="bein_rss_uncheck_all"):
                for idx in range(len(st.session_state.bein_rss_candidates)):
                    st.session_state[f"bein_rss_pick_{idx}"] = False
                st.rerun()

        if st.session_state.bein_rss_candidates:
            st.caption("Sélectionne les articles à traiter :")
            for idx, item in enumerate(st.session_state.bein_rss_candidates):
                label = f"{item.get('title','')}".strip() or item.get("url", "")
                key = f"bein_rss_pick_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = True
                checked = st.checkbox(label, key=key)
                if checked:
                    bein_selected_urls.append(item)
            st.caption(f"{len(bein_selected_urls)} article(s) sélectionné(s)")
        else:
            st.caption("Clique sur Lancer pour charger la liste.")

    if st.session_state.bein_rss_candidates:
        if st.button("🧭 Scrapper les articles", use_container_width=True, key="bein_scrape_articles"):
            if not bein_selected_urls:
                st.error("Sélectionne au moins un article.")
            else:
                bein_job.set_buffer_text("")
                bein_job.json_preview_text = ""
                bein_job.json_items = []
                st.session_state.bein_show_json_state = False
                st.session_state.bein_json_ready = False
                config = BeInJobConfig(
                    entry_url="https://fr.beincrypto.com/",
                    mode="today" if bein_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(bein_hours_window),
                    max_articles_total=int(bein_max_articles_total),
                    max_articles_per_bulletin=int(bein_max_articles_per),
                    wait_min_action=float(bein_wait_min_action),
                    wait_max_action=float(bein_wait_max_action),
                    shuffle_urls=bool(bein_shuffle_urls),
                    dry_run=bool(bein_dry_run),
                    max_consecutive_errors=int(bein_max_consecutive_errors),
                    global_timeout_minutes=int(bein_global_timeout_minutes),
                    remove_buffer_after_success=bool(bein_remove_buffer),
                    use_rss=bool(bein_use_rss),
                    rss_feed_url=bein_rss_feed_url,
                    rss_ignore_time_filter=bool(bein_rss_ignore_time_filter),
                    rss_use_dom_fallback=bool(bein_rss_use_dom_fallback),
                    use_firecrawl=bool(bein_use_firecrawl),
                    urls_override=bein_selected_urls,
                )
                bein_job.start(config)
                st.success("Scraping lancé.")

    if bein_launch:
        if bein_use_rss:
            bein_job.set_buffer_text("")
            bein_job.json_preview_text = ""
            bein_job.json_items = []
            st.session_state.bein_show_json_state = False
            st.session_state.bein_json_ready = False
            rss_items = fetch_rss_items(
                feed_url=bein_rss_feed_url,
                max_items=int(bein_max_articles_total),
                mode="today" if bein_mode == "Aujourd’hui" else "last_hours",
                hours_window=int(bein_hours_window),
                ignore_time_filter=bool(bein_rss_ignore_time_filter),
            )
            if bein_rss_use_dom_fallback:
                dom_items = fetch_beincrypto_dom_items(
                    page_url="https://fr.beincrypto.com/",
                    max_items=int(bein_max_articles_total),
                    mode="today" if bein_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(bein_hours_window),
                )
                st.session_state.bein_rss_candidates = merge_article_items(
                    dom_items,
                    rss_items,
                    int(bein_max_articles_total),
                )
            else:
                st.session_state.bein_rss_candidates = rss_items
            bein_job.status_log.append("🔎 URLs chargées")
            st.rerun()
        else:
            st.warning("Mode RSS/DOM désactivé : active-le pour charger les URLs.")

    if bein_clear:
        bein_job.clear()
        st.session_state.bein_rss_candidates = []
        st.session_state.bein_show_json_state = False
        st.session_state.bein_json_ready = False
        st.rerun()

    bein_status = bein_job.get_status()
    st.divider()
    st.caption(f"État : {bein_status.get('state')}")
    bein_total = int(bein_status.get("total") or 0)
    bein_processed = int(bein_status.get("processed", 0))
    bein_skipped = int(bein_status.get("skipped", 0))
    bein_started_at = bein_status.get("started_at")
    bein_last_log = bein_status.get("last_log") or ""
    if bein_total > 0:
        progress_value = min(max((bein_processed + bein_skipped) / bein_total, 0.0), 1.0)
        st.progress(progress_value)
        st.caption(f"Progression : {bein_processed + bein_skipped}/{bein_total}")
    st.caption(f"Traités : {bein_processed} · Skipped : {bein_skipped}")
    if bein_started_at and (bein_processed + bein_skipped) > 0:
        elapsed = max(time.time() - float(bein_started_at), 1.0)
        avg_per_item = elapsed / max(bein_processed + bein_skipped, 1)
        remaining = max(bein_total - (bein_processed + bein_skipped), 0)
        eta_seconds = int(remaining * avg_per_item)
        st.caption(f"ETA estimée : ~{eta_seconds // 60}m {eta_seconds % 60}s")
    if bein_last_log:
        st.caption(f"Dernier statut : {bein_last_log}")
    if bein_status.get("buffer_path"):
        st.caption(f"Buffer : {bein_status.get('buffer_path')}")
    if bein_status.get("state") in ("running", "paused"):
        st.info("Job en cours — rafraîchissement automatique activé.")
        time.sleep(2)
        st.rerun()

    if bein_last_log:
        st.caption(f"Statut : {bein_last_log}")
    if bein_status.get("errors"):
        st.markdown("**Erreurs :**")
        for err in bein_status.get("errors")[-3:]:
            st.write(f"⚠️ {err}")

    if bein_status.get("buffer_text"):
        st.divider()
        st.markdown("**Preview concaténée (buffer)**")
        bein_edited_buffer = st.text_area(
            label="",
            value=bein_status.get("buffer_text", ""),
            height=320,
            key="bein_buffer_editor",
        )
        col_json, col_clear_buf = st.columns(2)
        with col_json:
            if st.button("✅ Dédoublonner + JSON", use_container_width=True, key="bein_finalize"):
                bein_job.set_buffer_text(bein_edited_buffer)
                result = bein_job.finalize_buffer()
                if result.get("status") == "success":
                    st.success(f"{len(result.get('items', []))} items générés")
                    st.session_state.bein_json_ready = True
                    st.session_state.bein_show_json_state = False
                    bein_status = bein_job.get_status()
                else:
                    st.error(result.get("message", "Erreur JSON"))
        with col_clear_buf:
            if st.button("🧹 Clear buffer", use_container_width=True, key="bein_clear_buffer"):
                bein_job.set_buffer_text("")
                st.rerun()

    if st.session_state.bein_json_ready and bein_status.get("json_preview_text") and not st.session_state.bein_show_json_state:
        if st.button("🧾 Afficher preview JSON", use_container_width=True, key="bein_show_json_btn"):
            st.session_state.bein_show_json_state = True
            st.rerun()

    if bein_status.get("json_preview_text") and st.session_state.bein_show_json_state:
        st.markdown("**Preview JSON**")
        bein_edited_json = st.text_area(
            label="",
            value=bein_status.get("json_preview_text", ""),
            height=350,
            key="bein_json_editor",
        )
        col_send, col_clear_json = st.columns(2)
        with col_send:
            if st.button("✅ Envoyer en DB", use_container_width=True, key="bein_send_db"):
                result = bein_job.send_to_db()
                if result.get("status") == "success":
                    st.success(f"{result.get('inserted', 0)} items insérés en base")
                else:
                    st.error(result.get("message", "Erreur DB"))
        with col_clear_json:
            if st.button("🧹 Clear JSON", use_container_width=True, key="bein_clear_json"):
                bein_job.json_preview_text = ""
                bein_job.json_items = []
                st.session_state.bein_show_json_state = False
                st.session_state.bein_json_ready = False
                st.rerun()

# =========================
# JOB — BOURSE DIRECT
# =========================

with st.expander("▸ Job — Bourse Direct", expanded=False):
    boursedirect_job = get_boursedirect_job()
    col_open, col_launch, col_clear = st.columns([2, 1, 1])

    with col_open:
        st.link_button("🔗 Ouvrir l’URL", "https://www.boursedirect.fr/fr/actualites/categorie/marches")
    with col_launch:
        boursedirect_launch = st.button("▶️ Lancer", use_container_width=True, key="boursedirect_launch")
    with col_clear:
        boursedirect_clear = st.button("🧹 Clear", use_container_width=True, key="boursedirect_clear")

    with st.expander("Fenêtre temporelle", expanded=True):
        boursedirect_mode = st.radio(
            "Mode",
            options=["Aujourd’hui", "Dernières X heures"],
            horizontal=True,
            index=1,
            key="boursedirect_mode",
        )
        boursedirect_hours_window = st.slider(
            "Dernières X heures",
            min_value=1,
            max_value=24,
            value=6,
            step=1,
            key="boursedirect_hours_window",
        )

    with st.expander("Settings", expanded=False):
        st.markdown("**Limites**")
        col_max_total, col_max_per = st.columns(2)
        with col_max_total:
            boursedirect_max_articles_total = st.number_input(
                "Max articles total",
                min_value=1,
                max_value=100,
                value=20,
                step=1,
                key="boursedirect_max_total",
            )
        with col_max_per:
            boursedirect_max_articles_per = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=20,
                value=20,
                step=1,
                key="boursedirect_max_per",
            )

        st.markdown("**Timing**")
        col_wait_min, col_wait_max = st.columns(2)
        with col_wait_min:
            boursedirect_wait_min_action = st.number_input(
                "Wait min action (s)",
                min_value=0.1,
                max_value=5.0,
                value=0.6,
                step=0.1,
                key="boursedirect_wait_min",
            )
        with col_wait_max:
            boursedirect_wait_max_action = st.number_input(
                "Wait max action (s)",
                min_value=0.2,
                max_value=8.0,
                value=2.5,
                step=0.1,
                key="boursedirect_wait_max",
            )

        boursedirect_shuffle_urls = st.checkbox("Shuffle URLs", value=True, key="boursedirect_shuffle")
        boursedirect_dry_run = st.checkbox("DRY RUN", value=False, key="boursedirect_dry_run")

        st.markdown("**Safety**")
        col_err, col_timeout = st.columns(2)
        with col_err:
            boursedirect_max_consecutive_errors = st.number_input(
                "Max erreurs consécutives",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                key="boursedirect_max_errors",
            )
        with col_timeout:
            boursedirect_global_timeout_minutes = st.number_input(
                "Timeout global job (min)",
                min_value=1,
                max_value=60,
                value=15,
                step=1,
                key="boursedirect_timeout",
            )

        boursedirect_remove_buffer = st.checkbox(
            "Supprimer buffer après succès",
            value=True,
            key="boursedirect_remove_buffer",
        )

        st.markdown("**Source URLs**")
        boursedirect_rss_feed_url = st.text_input(
            "RSS feed",
            value="https://www.boursedirect.fr/fr/actualites/categorie/marches",
            key="boursedirect_rss_feed",
        )
        boursedirect_use_rss = st.checkbox("Mode RSS/DOM", value=True, key="boursedirect_use_rss")
        boursedirect_use_firecrawl = st.checkbox(
            "Scraper articles via Firecrawl",
            value=True,
            key="boursedirect_use_firecrawl",
        )
        boursedirect_rss_ignore_time_filter = st.checkbox(
            "Ignorer filtre temporel RSS",
            value=False,
            key="boursedirect_rss_ignore_time",
        )
        boursedirect_rss_use_dom_fallback = st.checkbox(
            "Compléter via DOM (Marchés)",
            value=True,
            key="boursedirect_rss_dom_fallback",
        )

    boursedirect_selected_urls = []
    if boursedirect_use_rss:
        col_clear, col_uncheck = st.columns(2)
        with col_clear:
            if st.button("🧹 Clear liste", use_container_width=True, key="boursedirect_rss_clear"):
                st.session_state.boursedirect_rss_candidates = []
                st.rerun()
        with col_uncheck:
            if st.button("☐ Décocher tout", use_container_width=True, key="boursedirect_rss_uncheck_all"):
                for idx in range(len(st.session_state.boursedirect_rss_candidates)):
                    st.session_state[f"boursedirect_rss_pick_{idx}"] = False
                st.rerun()

        if st.session_state.boursedirect_rss_candidates:
            st.caption("Sélectionne les articles à traiter :")
            for idx, item in enumerate(st.session_state.boursedirect_rss_candidates):
                label = f"{item.get('title','')}".strip() or item.get("url", "")
                key = f"boursedirect_rss_pick_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = True
                checked = st.checkbox(label, key=key)
                if checked:
                    boursedirect_selected_urls.append(item)
            st.caption(f"{len(boursedirect_selected_urls)} article(s) sélectionné(s)")
        else:
            st.caption("Clique sur Lancer pour charger la liste.")

    if st.session_state.boursedirect_rss_candidates:
        if st.button("🧭 Scrapper les articles", use_container_width=True, key="boursedirect_scrape_articles"):
            if not boursedirect_selected_urls:
                st.error("Sélectionne au moins un article.")
            else:
                boursedirect_job.set_buffer_text("")
                boursedirect_job.json_preview_text = ""
                boursedirect_job.json_items = []
                st.session_state.boursedirect_show_json_state = False
                st.session_state.boursedirect_json_ready = False
                config = BourseDirectJobConfig(
                    entry_url="https://www.boursedirect.fr/fr/actualites/categorie/marches",
                    mode="today" if boursedirect_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(boursedirect_hours_window),
                    max_articles_total=int(boursedirect_max_articles_total),
                    max_articles_per_bulletin=int(boursedirect_max_articles_per),
                    wait_min_action=float(boursedirect_wait_min_action),
                    wait_max_action=float(boursedirect_wait_max_action),
                    shuffle_urls=bool(boursedirect_shuffle_urls),
                    dry_run=bool(boursedirect_dry_run),
                    max_consecutive_errors=int(boursedirect_max_consecutive_errors),
                    global_timeout_minutes=int(boursedirect_global_timeout_minutes),
                    remove_buffer_after_success=bool(boursedirect_remove_buffer),
                    use_rss=bool(boursedirect_use_rss),
                    rss_feed_url=boursedirect_rss_feed_url,
                    rss_ignore_time_filter=bool(boursedirect_rss_ignore_time_filter),
                    rss_use_dom_fallback=bool(boursedirect_rss_use_dom_fallback),
                    use_firecrawl=bool(boursedirect_use_firecrawl),
                    urls_override=boursedirect_selected_urls,
                )
                boursedirect_job.start(config)
                st.success("Scraping lancé.")

    if boursedirect_launch:
        if boursedirect_use_rss:
            boursedirect_job.set_buffer_text("")
            boursedirect_job.json_preview_text = ""
            boursedirect_job.json_items = []
            st.session_state.boursedirect_show_json_state = False
            st.session_state.boursedirect_json_ready = False
            rss_items = fetch_rss_items(
                feed_url=boursedirect_rss_feed_url,
                max_items=int(boursedirect_max_articles_total),
                mode="today" if boursedirect_mode == "Aujourd’hui" else "last_hours",
                hours_window=int(boursedirect_hours_window),
                ignore_time_filter=bool(boursedirect_rss_ignore_time_filter),
            )
            if boursedirect_rss_use_dom_fallback:
                dom_items = fetch_boursedirect_dom_items(
                    page_url="https://www.boursedirect.fr/fr/actualites/categorie/marches",
                    max_items=int(boursedirect_max_articles_total),
                    mode="today" if boursedirect_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(boursedirect_hours_window),
                )
                st.session_state.boursedirect_rss_candidates = merge_article_items(
                    dom_items,
                    rss_items,
                    int(boursedirect_max_articles_total),
                )
            else:
                st.session_state.boursedirect_rss_candidates = rss_items
            boursedirect_job.status_log.append("🔎 URLs chargées")
            if not st.session_state.boursedirect_rss_candidates:
                st.warning("Aucune URL détectée. DOM vide ou bloqué ; active Firecrawl ou un RSS valide.")
            st.rerun()

    if boursedirect_clear:
        boursedirect_job.clear()
        st.session_state.boursedirect_rss_candidates = []
        st.session_state.boursedirect_show_json_state = False
        st.session_state.boursedirect_json_ready = False
        for key in list(st.session_state.keys()):
            if key.startswith("boursedirect_rss_pick_"):
                st.session_state.pop(key, None)
        st.success("Job réinitialisé.")
        st.rerun()

    boursedirect_status = boursedirect_job.get_status()
    boursedirect_state = boursedirect_status.get("state")
    boursedirect_total = boursedirect_status.get("total", 0)
    boursedirect_processed = boursedirect_status.get("processed", 0)
    boursedirect_skipped = boursedirect_status.get("skipped", 0)
    boursedirect_started_at = boursedirect_status.get("started_at")
    boursedirect_last_log = boursedirect_status.get("last_log", "")

    st.progress(boursedirect_processed / max(boursedirect_total, 1))
    status_parts = [f"{boursedirect_processed}/{boursedirect_total} traités", f"{boursedirect_skipped} ignorés"]
    if boursedirect_state:
        status_parts.append(f"état: {boursedirect_state}")
    if boursedirect_started_at:
        elapsed = int(time.time() - boursedirect_started_at)
        status_parts.append(f"{elapsed}s")
    st.caption(" · ".join(status_parts))
    if boursedirect_last_log:
        st.caption(f"Statut : {boursedirect_last_log}")
    if boursedirect_status.get("errors"):
        st.markdown("**Erreurs :**")
        for err in boursedirect_status.get("errors")[-3:]:
            st.write(f"⚠️ {err}")
    if boursedirect_state in ("running", "paused"):
        st.info("Job en cours — rafraîchissement automatique activé.")
        time.sleep(2)
        st.rerun()

    if boursedirect_status.get("buffer_text"):
        st.divider()
        st.markdown("**Preview concaténée (buffer)**")
        boursedirect_edited_buffer = st.text_area(
            label="",
            value=boursedirect_status.get("buffer_text", ""),
            height=320,
            key="boursedirect_buffer_editor",
        )
        col_json, col_clear_buf = st.columns(2)
        with col_json:
            if st.button("✅ Dédoublonner + JSON", use_container_width=True, key="boursedirect_finalize"):
                boursedirect_job.set_buffer_text(boursedirect_edited_buffer)
                result = boursedirect_job.finalize_buffer()
                if result.get("status") == "success":
                    st.success(f"{len(result.get('items', []))} items générés")
                    st.session_state.boursedirect_json_ready = True
                    st.session_state.boursedirect_show_json_state = False
                    boursedirect_status = boursedirect_job.get_status()
                else:
                    st.error(result.get("message", "Erreur JSON"))
        with col_clear_buf:
            if st.button("🧹 Clear buffer", use_container_width=True, key="boursedirect_clear_buffer"):
                boursedirect_job.set_buffer_text("")
                st.rerun()

    if (
        st.session_state.boursedirect_json_ready
        and boursedirect_status.get("json_preview_text")
        and not st.session_state.boursedirect_show_json_state
    ):
        if st.button("🧾 Afficher preview JSON", use_container_width=True, key="boursedirect_show_json_btn"):
            st.session_state.boursedirect_show_json_state = True
            st.rerun()

    if boursedirect_status.get("json_preview_text") and st.session_state.boursedirect_show_json_state:
        st.markdown("**Preview JSON**")
        boursedirect_edited_json = st.text_area(
            label="",
            value=boursedirect_status.get("json_preview_text", ""),
            height=350,
            key="boursedirect_json_editor",
        )
        col_send, col_clear_json = st.columns(2)
        with col_send:
            if st.button("✅ Envoyer en DB", use_container_width=True, key="boursedirect_send_db"):
                result = boursedirect_job.send_to_db()
                if result.get("status") == "success":
                    st.success(f"{result.get('inserted', 0)} items insérés en base")
                else:
                    st.error(result.get("message", "Erreur DB"))
        with col_clear_json:
            if st.button("🧹 Clear JSON", use_container_width=True, key="boursedirect_clear_json"):
                boursedirect_job.json_preview_text = ""
                boursedirect_job.json_items = []
                st.session_state.boursedirect_show_json_state = False
                st.session_state.boursedirect_json_ready = False
                st.rerun()

with st.expander("▸ Job — Bourse Direct Indices", expanded=False):
    boursedirect_indices_job = get_boursedirect_indices_job()
    col_open, col_launch, col_clear = st.columns([2, 1, 1])

    with col_open:
        st.link_button("🔗 Ouvrir l’URL", "https://www.boursedirect.fr/fr/actualites/categorie/indices")
    with col_launch:
        boursedirect_indices_launch = st.button("▶️ Lancer", use_container_width=True, key="boursedirect_indices_launch")
    with col_clear:
        boursedirect_indices_clear = st.button("🧹 Clear", use_container_width=True, key="boursedirect_indices_clear")

    with st.expander("Fenêtre temporelle", expanded=True):
        boursedirect_indices_mode = st.radio(
            "Mode",
            options=["Aujourd’hui", "Dernières X heures"],
            horizontal=True,
            index=1,
            key="boursedirect_indices_mode",
        )
        boursedirect_indices_hours_window = st.slider(
            "Dernières X heures",
            min_value=1,
            max_value=24,
            value=6,
            step=1,
            key="boursedirect_indices_hours_window",
        )

    with st.expander("Settings", expanded=False):
        st.markdown("**Limites**")
        col_max_total, col_max_per = st.columns(2)
        with col_max_total:
            boursedirect_indices_max_articles_total = st.number_input(
                "Max articles total",
                min_value=1,
                max_value=100,
                value=20,
                step=1,
                key="boursedirect_indices_max_total",
            )
        with col_max_per:
            boursedirect_indices_max_articles_per = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=20,
                value=20,
                step=1,
                key="boursedirect_indices_max_per",
            )

        st.markdown("**Timing**")
        col_wait_min, col_wait_max = st.columns(2)
        with col_wait_min:
            boursedirect_indices_wait_min_action = st.number_input(
                "Wait min action (s)",
                min_value=0.1,
                max_value=5.0,
                value=0.6,
                step=0.1,
                key="boursedirect_indices_wait_min",
            )
        with col_wait_max:
            boursedirect_indices_wait_max_action = st.number_input(
                "Wait max action (s)",
                min_value=0.2,
                max_value=8.0,
                value=2.5,
                step=0.1,
                key="boursedirect_indices_wait_max",
            )

        boursedirect_indices_shuffle_urls = st.checkbox(
            "Shuffle URLs",
            value=True,
            key="boursedirect_indices_shuffle",
        )
        boursedirect_indices_dry_run = st.checkbox(
            "DRY RUN",
            value=False,
            key="boursedirect_indices_dry_run",
        )

        st.markdown("**Safety**")
        col_err, col_timeout = st.columns(2)
        with col_err:
            boursedirect_indices_max_consecutive_errors = st.number_input(
                "Max erreurs consécutives",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                key="boursedirect_indices_max_errors",
            )
        with col_timeout:
            boursedirect_indices_global_timeout_minutes = st.number_input(
                "Timeout global job (min)",
                min_value=1,
                max_value=60,
                value=15,
                step=1,
                key="boursedirect_indices_timeout",
            )

        boursedirect_indices_remove_buffer = st.checkbox(
            "Supprimer buffer après succès",
            value=True,
            key="boursedirect_indices_remove_buffer",
        )

        st.markdown("**Source URLs**")
        boursedirect_indices_rss_feed_url = st.text_input(
            "RSS feed",
            value="https://www.boursedirect.fr/fr/actualites/categorie/indices",
            key="boursedirect_indices_rss_feed",
        )
        boursedirect_indices_use_rss = st.checkbox(
            "Mode RSS/DOM",
            value=True,
            key="boursedirect_indices_use_rss",
        )
        boursedirect_indices_use_firecrawl = st.checkbox(
            "Scraper articles via Firecrawl",
            value=True,
            key="boursedirect_indices_use_firecrawl",
        )
        boursedirect_indices_rss_ignore_time_filter = st.checkbox(
            "Ignorer filtre temporel RSS",
            value=False,
            key="boursedirect_indices_rss_ignore_time",
        )
        boursedirect_indices_rss_use_dom_fallback = st.checkbox(
            "Compléter via DOM (Indices)",
            value=True,
            key="boursedirect_indices_rss_dom_fallback",
        )

    boursedirect_indices_selected_urls = []
    if boursedirect_indices_use_rss:
        col_clear, col_uncheck = st.columns(2)
        with col_clear:
            if st.button("🧹 Clear liste", use_container_width=True, key="boursedirect_indices_rss_clear"):
                st.session_state.boursedirect_indices_rss_candidates = []
                st.rerun()
        with col_uncheck:
            if st.button("☐ Décocher tout", use_container_width=True, key="boursedirect_indices_rss_uncheck_all"):
                for idx in range(len(st.session_state.boursedirect_indices_rss_candidates)):
                    st.session_state[f"boursedirect_indices_rss_pick_{idx}"] = False
                st.rerun()

        if st.session_state.boursedirect_indices_rss_candidates:
            st.caption("Sélectionne les articles à traiter :")
            for idx, item in enumerate(st.session_state.boursedirect_indices_rss_candidates):
                label = f"{item.get('title','')}".strip() or item.get("url", "")
                key = f"boursedirect_indices_rss_pick_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = True
                checked = st.checkbox(label, key=key)
                if checked:
                    boursedirect_indices_selected_urls.append(item)
            st.caption(f"{len(boursedirect_indices_selected_urls)} article(s) sélectionné(s)")
        else:
            st.caption("Clique sur Lancer pour charger la liste.")

    if st.session_state.boursedirect_indices_rss_candidates:
        if st.button("🧭 Scrapper les articles", use_container_width=True, key="boursedirect_indices_scrape_articles"):
            if not boursedirect_indices_selected_urls:
                st.error("Sélectionne au moins un article.")
            else:
                boursedirect_indices_job.set_buffer_text("")
                boursedirect_indices_job.json_preview_text = ""
                boursedirect_indices_job.json_items = []
                st.session_state.boursedirect_indices_show_json_state = False
                st.session_state.boursedirect_indices_json_ready = False
                config = BourseDirectIndicesJobConfig(
                    entry_url="https://www.boursedirect.fr/fr/actualites/categorie/indices",
                    mode="today" if boursedirect_indices_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(boursedirect_indices_hours_window),
                    max_articles_total=int(boursedirect_indices_max_articles_total),
                    max_articles_per_bulletin=int(boursedirect_indices_max_articles_per),
                    wait_min_action=float(boursedirect_indices_wait_min_action),
                    wait_max_action=float(boursedirect_indices_wait_max_action),
                    shuffle_urls=bool(boursedirect_indices_shuffle_urls),
                    dry_run=bool(boursedirect_indices_dry_run),
                    max_consecutive_errors=int(boursedirect_indices_max_consecutive_errors),
                    global_timeout_minutes=int(boursedirect_indices_global_timeout_minutes),
                    remove_buffer_after_success=bool(boursedirect_indices_remove_buffer),
                    use_rss=bool(boursedirect_indices_use_rss),
                    rss_feed_url=boursedirect_indices_rss_feed_url,
                    rss_ignore_time_filter=bool(boursedirect_indices_rss_ignore_time_filter),
                    rss_use_dom_fallback=bool(boursedirect_indices_rss_use_dom_fallback),
                    use_firecrawl=bool(boursedirect_indices_use_firecrawl),
                    urls_override=boursedirect_indices_selected_urls,
                )
                boursedirect_indices_job.start(config)
                st.success("Scraping lancé.")

    if boursedirect_indices_launch:
        if boursedirect_indices_use_rss:
            boursedirect_indices_job.set_buffer_text("")
            boursedirect_indices_job.json_preview_text = ""
            boursedirect_indices_job.json_items = []
            st.session_state.boursedirect_indices_show_json_state = False
            st.session_state.boursedirect_indices_json_ready = False
            rss_items = fetch_rss_items(
                feed_url=boursedirect_indices_rss_feed_url,
                max_items=int(boursedirect_indices_max_articles_total),
                mode="today" if boursedirect_indices_mode == "Aujourd’hui" else "last_hours",
                hours_window=int(boursedirect_indices_hours_window),
                ignore_time_filter=bool(boursedirect_indices_rss_ignore_time_filter),
            )
            if boursedirect_indices_rss_use_dom_fallback:
                dom_items = fetch_boursedirect_dom_items(
                    page_url="https://www.boursedirect.fr/fr/actualites/categorie/indices",
                    max_items=int(boursedirect_indices_max_articles_total),
                    mode="today" if boursedirect_indices_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(boursedirect_indices_hours_window),
                )
                st.session_state.boursedirect_indices_rss_candidates = merge_article_items(
                    dom_items,
                    rss_items,
                    int(boursedirect_indices_max_articles_total),
                )
            else:
                st.session_state.boursedirect_indices_rss_candidates = rss_items
            boursedirect_indices_job.status_log.append("🔎 URLs chargées")
            if not st.session_state.boursedirect_indices_rss_candidates:
                st.warning("Aucune URL détectée. DOM vide ou bloqué ; active Firecrawl ou un RSS valide.")
            st.rerun()

    if boursedirect_indices_clear:
        boursedirect_indices_job.clear()
        st.session_state.boursedirect_indices_rss_candidates = []
        st.session_state.boursedirect_indices_show_json_state = False
        st.session_state.boursedirect_indices_json_ready = False
        for key in list(st.session_state.keys()):
            if key.startswith("boursedirect_indices_rss_pick_"):
                st.session_state.pop(key, None)
        st.success("Job réinitialisé.")
        st.rerun()

    boursedirect_indices_status = boursedirect_indices_job.get_status()
    boursedirect_indices_state = boursedirect_indices_status.get("state")
    boursedirect_indices_total = boursedirect_indices_status.get("total", 0)
    boursedirect_indices_processed = boursedirect_indices_status.get("processed", 0)
    boursedirect_indices_skipped = boursedirect_indices_status.get("skipped", 0)
    boursedirect_indices_started_at = boursedirect_indices_status.get("started_at")
    boursedirect_indices_last_log = boursedirect_indices_status.get("last_log", "")

    st.progress(boursedirect_indices_processed / max(boursedirect_indices_total, 1))
    status_parts = [
        f"{boursedirect_indices_processed}/{boursedirect_indices_total} traités",
        f"{boursedirect_indices_skipped} ignorés",
    ]
    if boursedirect_indices_state:
        status_parts.append(f"état: {boursedirect_indices_state}")
    if boursedirect_indices_started_at:
        elapsed = int(time.time() - boursedirect_indices_started_at)
        status_parts.append(f"{elapsed}s")
    st.caption(" · ".join(status_parts))
    if boursedirect_indices_last_log:
        st.caption(f"Statut : {boursedirect_indices_last_log}")
    if boursedirect_indices_status.get("errors"):
        st.markdown("**Erreurs :**")
        for err in boursedirect_indices_status.get("errors")[-3:]:
            st.write(f"⚠️ {err}")
    if boursedirect_indices_state in ("running", "paused"):
        st.info("Job en cours — rafraîchissement automatique activé.")
        time.sleep(2)
        st.rerun()

    if boursedirect_indices_status.get("buffer_text"):
        st.divider()
        st.markdown("**Preview concaténée (buffer)**")
        boursedirect_indices_edited_buffer = st.text_area(
            label="",
            value=boursedirect_indices_status.get("buffer_text", ""),
            height=320,
            key="boursedirect_indices_buffer_editor",
        )
        col_json, col_clear_buf = st.columns(2)
        with col_json:
            if st.button("✅ Dédoublonner + JSON", use_container_width=True, key="boursedirect_indices_finalize"):
                boursedirect_indices_job.set_buffer_text(boursedirect_indices_edited_buffer)
                result = boursedirect_indices_job.finalize_buffer()
                if result.get("status") == "success":
                    st.success(f"{len(result.get('items', []))} items générés")
                    st.session_state.boursedirect_indices_json_ready = True
                    st.session_state.boursedirect_indices_show_json_state = False
                    boursedirect_indices_status = boursedirect_indices_job.get_status()
                else:
                    st.error(result.get("message", "Erreur JSON"))
        with col_clear_buf:
            if st.button("🧹 Clear buffer", use_container_width=True, key="boursedirect_indices_clear_buffer"):
                boursedirect_indices_job.set_buffer_text("")
                st.rerun()

    if (
        st.session_state.boursedirect_indices_json_ready
        and boursedirect_indices_status.get("json_preview_text")
        and not st.session_state.boursedirect_indices_show_json_state
    ):
        if st.button("🧾 Afficher preview JSON", use_container_width=True, key="boursedirect_indices_show_json_btn"):
            st.session_state.boursedirect_indices_show_json_state = True
            st.rerun()

    if boursedirect_indices_status.get("json_preview_text") and st.session_state.boursedirect_indices_show_json_state:
        st.markdown("**Preview JSON**")
        boursedirect_indices_edited_json = st.text_area(
            label="",
            value=boursedirect_indices_status.get("json_preview_text", ""),
            height=350,
            key="boursedirect_indices_json_editor",
        )
        col_send, col_clear_json = st.columns(2)
        with col_send:
            if st.button("✅ Envoyer en DB", use_container_width=True, key="boursedirect_indices_send_db"):
                result = boursedirect_indices_job.send_to_db()
                if result.get("status") == "success":
                    st.success(f"{result.get('inserted', 0)} items insérés en base")
                else:
                    st.error(result.get("message", "Erreur DB"))
        with col_clear_json:
            if st.button("🧹 Clear JSON", use_container_width=True, key="boursedirect_indices_clear_json"):
                boursedirect_indices_job.json_preview_text = ""
                boursedirect_indices_job.json_items = []
                st.session_state.boursedirect_indices_show_json_state = False
                st.session_state.boursedirect_indices_json_ready = False
                st.rerun()

with st.expander("▸ Job — Boursier Economie", expanded=False):
    boursier_economie_job = get_boursier_economie_job()
    col_open, col_launch, col_clear = st.columns([2, 1, 1])

    with col_open:
        st.link_button("🔗 Ouvrir l’URL", "https://www.boursier.com/actualites/economie")
    with col_launch:
        boursier_economie_launch = st.button("▶️ Lancer", use_container_width=True, key="boursier_economie_launch")
    with col_clear:
        boursier_economie_clear = st.button("🧹 Clear", use_container_width=True, key="boursier_economie_clear")

    with st.expander("Fenêtre temporelle", expanded=True):
        boursier_economie_mode = st.radio(
            "Mode",
            options=["Aujourd’hui", "Dernières X heures"],
            horizontal=True,
            index=1,
            key="boursier_economie_mode",
        )
        boursier_economie_hours_window = st.slider(
            "Dernières X heures",
            min_value=1,
            max_value=24,
            value=6,
            step=1,
            key="boursier_economie_hours_window",
        )

    with st.expander("Settings", expanded=False):
        st.markdown("**Limites**")
        col_max_total, col_max_per = st.columns(2)
        with col_max_total:
            boursier_economie_max_articles_total = st.number_input(
                "Max articles total",
                min_value=1,
                max_value=100,
                value=20,
                step=1,
                key="boursier_economie_max_total",
            )
        with col_max_per:
            boursier_economie_max_articles_per = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=20,
                value=20,
                step=1,
                key="boursier_economie_max_per",
            )

        st.markdown("**Timing**")
        col_wait_min, col_wait_max = st.columns(2)
        with col_wait_min:
            boursier_economie_wait_min_action = st.number_input(
                "Wait min action (s)",
                min_value=0.1,
                max_value=5.0,
                value=0.6,
                step=0.1,
                key="boursier_economie_wait_min",
            )
        with col_wait_max:
            boursier_economie_wait_max_action = st.number_input(
                "Wait max action (s)",
                min_value=0.2,
                max_value=8.0,
                value=2.5,
                step=0.1,
                key="boursier_economie_wait_max",
            )

        boursier_economie_shuffle_urls = st.checkbox(
            "Shuffle URLs",
            value=True,
            key="boursier_economie_shuffle",
        )
        boursier_economie_dry_run = st.checkbox(
            "DRY RUN",
            value=False,
            key="boursier_economie_dry_run",
        )

        st.markdown("**Safety**")
        col_err, col_timeout = st.columns(2)
        with col_err:
            boursier_economie_max_consecutive_errors = st.number_input(
                "Max erreurs consécutives",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                key="boursier_economie_max_errors",
            )
        with col_timeout:
            boursier_economie_global_timeout_minutes = st.number_input(
                "Timeout global job (min)",
                min_value=1,
                max_value=60,
                value=15,
                step=1,
                key="boursier_economie_timeout",
            )

        boursier_economie_remove_buffer = st.checkbox(
            "Supprimer buffer après succès",
            value=True,
            key="boursier_economie_remove_buffer",
        )

        st.markdown("**Source URLs**")
        boursier_economie_rss_feed_url = st.text_input(
            "RSS feed",
            value="https://www.boursier.com/actualites/economie",
            key="boursier_economie_rss_feed",
        )
        boursier_economie_use_rss = st.checkbox(
            "Mode RSS/DOM",
            value=True,
            key="boursier_economie_use_rss",
        )
        boursier_economie_use_firecrawl = st.checkbox(
            "Scraper articles via Firecrawl",
            value=True,
            key="boursier_economie_use_firecrawl",
        )
        boursier_economie_rss_ignore_time_filter = st.checkbox(
            "Ignorer filtre temporel RSS",
            value=False,
            key="boursier_economie_rss_ignore_time",
        )
        boursier_economie_rss_use_dom_fallback = st.checkbox(
            "Compléter via DOM (Economie)",
            value=True,
            key="boursier_economie_rss_dom_fallback",
        )

    boursier_economie_selected_urls = []
    if boursier_economie_use_rss:
        col_clear, col_uncheck = st.columns(2)
        with col_clear:
            if st.button("🧹 Clear liste", use_container_width=True, key="boursier_economie_rss_clear"):
                st.session_state.boursier_economie_rss_candidates = []
                st.rerun()
        with col_uncheck:
            if st.button("☐ Décocher tout", use_container_width=True, key="boursier_economie_rss_uncheck_all"):
                for idx in range(len(st.session_state.boursier_economie_rss_candidates)):
                    st.session_state[f"boursier_economie_rss_pick_{idx}"] = False
                st.rerun()

        if st.session_state.boursier_economie_rss_candidates:
            st.caption("Sélectionne les articles à traiter :")
            for idx, item in enumerate(st.session_state.boursier_economie_rss_candidates):
                label = f"{item.get('title','')}".strip() or item.get("url", "")
                key = f"boursier_economie_rss_pick_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = True
                checked = st.checkbox(label, key=key)
                if checked:
                    boursier_economie_selected_urls.append(item)
            st.caption(f"{len(boursier_economie_selected_urls)} article(s) sélectionné(s)")
        else:
            st.caption("Clique sur Lancer pour charger la liste.")

    if st.session_state.boursier_economie_rss_candidates:
        if st.button("🧭 Scrapper les articles", use_container_width=True, key="boursier_economie_scrape_articles"):
            if not boursier_economie_selected_urls:
                st.error("Sélectionne au moins un article.")
            else:
                boursier_economie_job.set_buffer_text("")
                boursier_economie_job.json_preview_text = ""
                boursier_economie_job.json_items = []
                st.session_state.boursier_economie_show_json_state = False
                st.session_state.boursier_economie_json_ready = False
                config = BoursierEconomieJobConfig(
                    entry_url="https://www.boursier.com/actualites/economie",
                    mode="today" if boursier_economie_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(boursier_economie_hours_window),
                    max_articles_total=int(boursier_economie_max_articles_total),
                    max_articles_per_bulletin=int(boursier_economie_max_articles_per),
                    wait_min_action=float(boursier_economie_wait_min_action),
                    wait_max_action=float(boursier_economie_wait_max_action),
                    shuffle_urls=bool(boursier_economie_shuffle_urls),
                    dry_run=bool(boursier_economie_dry_run),
                    max_consecutive_errors=int(boursier_economie_max_consecutive_errors),
                    global_timeout_minutes=int(boursier_economie_global_timeout_minutes),
                    remove_buffer_after_success=bool(boursier_economie_remove_buffer),
                    use_rss=bool(boursier_economie_use_rss),
                    rss_feed_url=boursier_economie_rss_feed_url,
                    rss_ignore_time_filter=bool(boursier_economie_rss_ignore_time_filter),
                    rss_use_dom_fallback=bool(boursier_economie_rss_use_dom_fallback),
                    use_firecrawl=bool(boursier_economie_use_firecrawl),
                    urls_override=boursier_economie_selected_urls,
                )
                boursier_economie_job.start(config)
                st.success("Scraping lancé.")

    if boursier_economie_launch:
        if boursier_economie_use_rss:
            boursier_economie_job.set_buffer_text("")
            boursier_economie_job.json_preview_text = ""
            boursier_economie_job.json_items = []
            st.session_state.boursier_economie_show_json_state = False
            st.session_state.boursier_economie_json_ready = False
            rss_items = fetch_rss_items(
                feed_url=boursier_economie_rss_feed_url,
                max_items=int(boursier_economie_max_articles_total),
                mode="today" if boursier_economie_mode == "Aujourd’hui" else "last_hours",
                hours_window=int(boursier_economie_hours_window),
                ignore_time_filter=bool(boursier_economie_rss_ignore_time_filter),
            )
            if boursier_economie_rss_use_dom_fallback:
                dom_items = fetch_boursier_dom_items(
                    page_url="https://www.boursier.com/actualites/economie",
                    max_items=int(boursier_economie_max_articles_total),
                    mode="today" if boursier_economie_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(boursier_economie_hours_window),
                    use_firecrawl_fallback=bool(boursier_economie_use_firecrawl),
                )
                st.session_state.boursier_economie_rss_candidates = merge_article_items(
                    dom_items,
                    rss_items,
                    int(boursier_economie_max_articles_total),
                )
            else:
                st.session_state.boursier_economie_rss_candidates = rss_items
            boursier_economie_job.status_log.append("🔎 URLs chargées")
            if not st.session_state.boursier_economie_rss_candidates:
                st.warning("Aucune URL détectée. DOM vide ou bloqué ; active Firecrawl ou un RSS valide.")
            st.rerun()

    if boursier_economie_clear:
        boursier_economie_job.clear()
        st.session_state.boursier_economie_rss_candidates = []
        st.session_state.boursier_economie_show_json_state = False
        st.session_state.boursier_economie_json_ready = False
        for key in list(st.session_state.keys()):
            if key.startswith("boursier_economie_rss_pick_"):
                st.session_state.pop(key, None)
        st.success("Job réinitialisé.")
        st.rerun()

    boursier_economie_status = boursier_economie_job.get_status()
    boursier_economie_state = boursier_economie_status.get("state")
    boursier_economie_total = boursier_economie_status.get("total", 0)
    boursier_economie_processed = boursier_economie_status.get("processed", 0)
    boursier_economie_skipped = boursier_economie_status.get("skipped", 0)
    boursier_economie_started_at = boursier_economie_status.get("started_at")
    boursier_economie_last_log = boursier_economie_status.get("last_log", "")

    st.progress(boursier_economie_processed / max(boursier_economie_total, 1))
    status_parts = [
        f"{boursier_economie_processed}/{boursier_economie_total} traités",
        f"{boursier_economie_skipped} ignorés",
    ]
    if boursier_economie_state:
        status_parts.append(f"état: {boursier_economie_state}")
    if boursier_economie_started_at:
        elapsed = int(time.time() - boursier_economie_started_at)
        status_parts.append(f"{elapsed}s")
    st.caption(" · ".join(status_parts))
    if boursier_economie_last_log:
        st.caption(f"Statut : {boursier_economie_last_log}")
    if boursier_economie_status.get("errors"):
        st.markdown("**Erreurs :**")
        for err in boursier_economie_status.get("errors")[-3:]:
            st.write(f"⚠️ {err}")
    if boursier_economie_state in ("running", "paused"):
        st.info("Job en cours — rafraîchissement automatique activé.")
        time.sleep(2)
        st.rerun()

    if boursier_economie_status.get("buffer_text"):
        st.divider()
        st.markdown("**Preview concaténée (buffer)**")
        boursier_economie_edited_buffer = st.text_area(
            label="",
            value=boursier_economie_status.get("buffer_text", ""),
            height=320,
            key="boursier_economie_buffer_editor",
        )
        col_json, col_clear_buf = st.columns(2)
        with col_json:
            if st.button("✅ Dédoublonner + JSON", use_container_width=True, key="boursier_economie_finalize"):
                boursier_economie_job.set_buffer_text(boursier_economie_edited_buffer)
                result = boursier_economie_job.finalize_buffer()
                if result.get("status") == "success":
                    st.success(f"{len(result.get('items', []))} items générés")
                    st.session_state.boursier_economie_json_ready = True
                    st.session_state.boursier_economie_show_json_state = False
                    boursier_economie_status = boursier_economie_job.get_status()
                else:
                    st.error(result.get("message", "Erreur JSON"))
        with col_clear_buf:
            if st.button("🧹 Clear buffer", use_container_width=True, key="boursier_economie_clear_buffer"):
                boursier_economie_job.set_buffer_text("")
                st.rerun()

    if (
        st.session_state.boursier_economie_json_ready
        and boursier_economie_status.get("json_preview_text")
        and not st.session_state.boursier_economie_show_json_state
    ):
        if st.button("🧾 Afficher preview JSON", use_container_width=True, key="boursier_economie_show_json_btn"):
            st.session_state.boursier_economie_show_json_state = True
            st.rerun()

    if boursier_economie_status.get("json_preview_text") and st.session_state.boursier_economie_show_json_state:
        st.markdown("**Preview JSON**")
        boursier_economie_edited_json = st.text_area(
            label="",
            value=boursier_economie_status.get("json_preview_text", ""),
            height=350,
            key="boursier_economie_json_editor",
        )
        col_send, col_clear_json = st.columns(2)
        with col_send:
            if st.button("✅ Envoyer en DB", use_container_width=True, key="boursier_economie_send_db"):
                result = boursier_economie_job.send_to_db()
                if result.get("status") == "success":
                    st.success(f"{result.get('inserted', 0)} items insérés en base")
                else:
                    st.error(result.get("message", "Erreur DB"))
        with col_clear_json:
            if st.button("🧹 Clear JSON", use_container_width=True, key="boursier_economie_clear_json"):
                boursier_economie_job.json_preview_text = ""
                boursier_economie_job.json_items = []
                st.session_state.boursier_economie_show_json_state = False
                st.session_state.boursier_economie_json_ready = False
                st.rerun()

st.divider()
with st.expander("🗄️ Derniers contenus en base", expanded=False):
        raw_items = fetch_raw_news(limit=50)
        if not raw_items:
            st.caption("Aucun contenu en base pour le moment")
        else:
            for item in raw_items:
                st.markdown("---")
                st.caption(f"🕒 {item['processed_at']} · Source : {item['source_type']}")
                st.markdown(f"**{item['title']}**")
                st.write(item['content'])
