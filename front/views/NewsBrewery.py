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
from services.news_brewery.boursier_macroeconomie_job import (
    JobConfig as BoursierMacroeconomieJobConfig,
    get_boursier_macroeconomie_job,
)
from services.news_brewery.boursier_france_job import (
    JobConfig as BoursierFranceJobConfig,
    get_boursier_france_job,
)
from services.news_brewery.rss_utils import (
    fetch_beincrypto_dom_items,
    fetch_boursedirect_dom_items,
    fetch_boursier_dom_items,
    fetch_boursier_macroeconomie_dom_items,
    fetch_boursier_france_dom_items,
    fetch_dom_items,
    fetch_rss_items,
    merge_article_items,
)
from services.raw_storage.raw_news_service import fetch_raw_news


st.title("🗞️ NEWS Brewery")
st.divider()

if "mega_run_candidates" not in st.session_state:
    st.session_state.mega_run_candidates = []
if "mega_run_sources" not in st.session_state:
    st.session_state.mega_run_sources = []

def _clear_job_state(prefix: str) -> None:
    for key in list(st.session_state.keys()):
        if key.startswith(f"{prefix}rss_pick_"):
            st.session_state.pop(key, None)
    for suffix in ("rss_candidates", "show_json_state", "json_ready", "last_params"):
        st.session_state.pop(f"{prefix}{suffix}", None)


def _clear_mega_state() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("mega_run_pick_"):
            st.session_state.pop(key, None)
    st.session_state.mega_run_candidates = []


def clear_all_jobs() -> None:
    get_bfm_job().clear()
    get_beincrypto_job().clear()
    get_boursedirect_job().clear()
    get_boursedirect_indices_job().clear()
    get_boursier_economie_job().clear()
    get_boursier_macroeconomie_job().clear()
    get_boursier_france_job().clear()
    for prefix in (
        "news_",
        "bein_",
        "boursedirect_",
        "boursedirect_indices_",
        "boursier_economie_",
        "boursier_macroeconomie_",
        "boursier_france_",
    ):
        _clear_job_state(prefix)
    _clear_mega_state()


def _mode_from_label(label: str) -> str:
    return "today" if label == "Aujourd’hui" else "last_hours"


def _get_state(key: str, default):
    return st.session_state.get(key, default)


def _collect_mega_urls(source_keys: list[str] | None = None) -> list[dict]:
    results: list[dict] = []
    seen = set()
    source_keys = source_keys or []

    def _add(source_key: str, source_label: str, items: list[dict]) -> None:
        if source_keys and source_key not in source_keys:
            return
        for item in items:
            url = item.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            results.append({
                "source_key": source_key,
                "source_label": source_label,
                "url": url,
                "title": item.get("title", ""),
                "label_dt": item.get("label_dt", ""),
            })

    bfm_use_rss = bool(_get_state("news_use_rss", True))
    if bfm_use_rss:
        bfm_mode = _mode_from_label(_get_state("news_mode", "Dernières X heures"))
        bfm_hours = int(_get_state("news_hours_window", 24))
        bfm_max = int(_get_state("news_max_total", 400))
        bfm_rss_feed = _get_state("news_rss_feed", "https://www.tradingsat.com/rssfeed.php")
        bfm_rss_ignore = bool(_get_state("news_rss_ignore_time", False))
        bfm_rss_dom = bool(_get_state("news_rss_dom_fallback", True))
        bfm_dom_items = fetch_dom_items(
            page_url="https://www.tradingsat.com/actualites/",
            max_items=bfm_max,
            mode=bfm_mode,
            hours_window=bfm_hours,
        )
        bfm_rss_items = fetch_rss_items(
            feed_url=bfm_rss_feed,
            max_items=bfm_max,
            mode=bfm_mode,
            hours_window=bfm_hours,
            ignore_time_filter=bfm_rss_ignore,
        )
        bfm_items = merge_article_items(bfm_dom_items, bfm_rss_items, bfm_max) if bfm_rss_dom else bfm_rss_items
        _add("bfm", "BFM Bourse", bfm_items)

    bein_use_rss = bool(_get_state("bein_use_rss", True))
    if bein_use_rss:
        bein_mode = _mode_from_label(_get_state("bein_mode", "Dernières X heures"))
        bein_hours = int(_get_state("bein_hours_window", 24))
        bein_max = int(_get_state("bein_max_total", 400))
        bein_rss_feed = _get_state("bein_rss_feed", "https://fr.beincrypto.com/feed/")
        bein_rss_ignore = bool(_get_state("bein_rss_ignore_time", False))
        bein_rss_dom = bool(_get_state("bein_rss_dom_fallback", True))
        bein_use_firecrawl = bool(_get_state("bein_use_firecrawl", True))
        bein_rss_items = fetch_rss_items(
            feed_url=bein_rss_feed,
            max_items=bein_max,
            mode=bein_mode,
            hours_window=bein_hours,
            ignore_time_filter=bein_rss_ignore,
        )
        bein_dom_items = fetch_beincrypto_dom_items(
            page_url="https://fr.beincrypto.com/",
            max_items=bein_max,
            mode=bein_mode,
            hours_window=bein_hours,
            use_firecrawl_fallback=bein_use_firecrawl,
        )
        bein_items = merge_article_items(bein_dom_items, bein_rss_items, bein_max) if bein_rss_dom else bein_rss_items
        _add("beincrypto", "BeInCrypto", bein_items)

    bd_use_rss = bool(_get_state("boursedirect_use_rss", True))
    if bd_use_rss:
        bd_mode = _mode_from_label(_get_state("boursedirect_mode", "Dernières X heures"))
        bd_hours = int(_get_state("boursedirect_hours_window", 24))
        bd_max = int(_get_state("boursedirect_max_total", 400))
        bd_rss_feed = _get_state("boursedirect_rss_feed", "https://www.boursedirect.fr/fr/actualites/categorie/marches")
        bd_rss_ignore = bool(_get_state("boursedirect_rss_ignore_time", False))
        bd_rss_dom = bool(_get_state("boursedirect_rss_dom_fallback", True))
        bd_rss_items = fetch_rss_items(
            feed_url=bd_rss_feed,
            max_items=bd_max,
            mode=bd_mode,
            hours_window=bd_hours,
            ignore_time_filter=bd_rss_ignore,
        )
        bd_dom_items = fetch_boursedirect_dom_items(
            page_url="https://www.boursedirect.fr/fr/actualites/categorie/marches",
            max_items=bd_max,
            mode=bd_mode,
            hours_window=bd_hours,
        )
        bd_items = merge_article_items(bd_dom_items, bd_rss_items, bd_max) if bd_rss_dom else bd_rss_items
        _add("boursedirect", "Bourse Direct", bd_items)

    bdi_use_rss = bool(_get_state("boursedirect_indices_use_rss", True))
    if bdi_use_rss:
        bdi_mode = _mode_from_label(_get_state("boursedirect_indices_mode", "Dernières X heures"))
        bdi_hours = int(_get_state("boursedirect_indices_hours_window", 24))
        bdi_max = int(_get_state("boursedirect_indices_max_total", 400))
        bdi_rss_feed = _get_state("boursedirect_indices_rss_feed", "https://www.boursedirect.fr/fr/actualites/categorie/indices")
        bdi_rss_ignore = bool(_get_state("boursedirect_indices_rss_ignore_time", False))
        bdi_rss_dom = bool(_get_state("boursedirect_indices_rss_dom_fallback", True))
        bdi_rss_items = fetch_rss_items(
            feed_url=bdi_rss_feed,
            max_items=bdi_max,
            mode=bdi_mode,
            hours_window=bdi_hours,
            ignore_time_filter=bdi_rss_ignore,
        )
        bdi_dom_items = fetch_boursedirect_dom_items(
            page_url="https://www.boursedirect.fr/fr/actualites/categorie/indices",
            max_items=bdi_max,
            mode=bdi_mode,
            hours_window=bdi_hours,
        )
        bdi_items = merge_article_items(bdi_dom_items, bdi_rss_items, bdi_max) if bdi_rss_dom else bdi_rss_items
        _add("boursedirect_indices", "Bourse Direct Indices", bdi_items)

    be_use_rss = bool(_get_state("boursier_economie_use_rss", True))
    if be_use_rss:
        be_mode = _mode_from_label(_get_state("boursier_economie_mode", "Dernières X heures"))
        be_hours = int(_get_state("boursier_economie_hours_window", 24))
        be_max = int(_get_state("boursier_economie_max_total", 400))
        be_rss_feed = _get_state("boursier_economie_rss_feed", "https://www.boursier.com/actualites/economie")
        be_rss_ignore = bool(_get_state("boursier_economie_rss_ignore_time", False))
        be_rss_dom = bool(_get_state("boursier_economie_rss_dom_fallback", True))
        be_use_firecrawl = bool(_get_state("boursier_economie_use_firecrawl", True))
        be_rss_items = fetch_rss_items(
            feed_url=be_rss_feed,
            max_items=be_max,
            mode=be_mode,
            hours_window=be_hours,
            ignore_time_filter=be_rss_ignore,
        )
        be_dom_items = fetch_boursier_dom_items(
            page_url="https://www.boursier.com/actualites/economie",
            max_items=be_max,
            mode=be_mode,
            hours_window=be_hours,
            use_firecrawl_fallback=be_use_firecrawl,
        )
        be_items = merge_article_items(be_dom_items, be_rss_items, be_max) if be_rss_dom else be_rss_items
        _add("boursier_economie", "Boursier Économie", be_items)

    bm_use_rss = bool(_get_state("boursier_macroeconomie_use_rss", True))
    if bm_use_rss:
        bm_mode = _mode_from_label(_get_state("boursier_macroeconomie_mode", "Dernières X heures"))
        bm_hours = int(_get_state("boursier_macroeconomie_hours_window", 24))
        bm_max = int(_get_state("boursier_macroeconomie_max_total", 400))
        bm_rss_feed = _get_state("boursier_macroeconomie_rss_feed", "https://www.boursier.com/actualites/macroeconomie")
        bm_rss_ignore = bool(_get_state("boursier_macroeconomie_rss_ignore_time", False))
        bm_rss_dom = bool(_get_state("boursier_macroeconomie_rss_dom_fallback", True))
        bm_use_firecrawl = bool(_get_state("boursier_macroeconomie_use_firecrawl", True))
        bm_rss_items = fetch_rss_items(
            feed_url=bm_rss_feed,
            max_items=bm_max,
            mode=bm_mode,
            hours_window=bm_hours,
            ignore_time_filter=bm_rss_ignore,
        )
        bm_dom_items = fetch_boursier_macroeconomie_dom_items(
            page_url="https://www.boursier.com/actualites/macroeconomie",
            max_items=bm_max,
            mode=bm_mode,
            hours_window=bm_hours,
            use_firecrawl_fallback=bm_use_firecrawl,
        )
        bm_items = merge_article_items(bm_dom_items, bm_rss_items, bm_max) if bm_rss_dom else bm_rss_items
        _add("boursier_macroeconomie", "Boursier Macroeconomie", bm_items)

    bf_use_rss = bool(_get_state("boursier_france_use_rss", True))
    if bf_use_rss:
        bf_mode = _mode_from_label(_get_state("boursier_france_mode", "Dernières X heures"))
        bf_hours = int(_get_state("boursier_france_hours_window", 24))
        bf_max = int(_get_state("boursier_france_max_total", 400))
        bf_rss_feed = _get_state("boursier_france_rss_feed", "https://www.boursier.com/actualites/france")
        bf_rss_ignore = bool(_get_state("boursier_france_rss_ignore_time", False))
        bf_rss_dom = bool(_get_state("boursier_france_rss_dom_fallback", True))
        bf_use_firecrawl = bool(_get_state("boursier_france_use_firecrawl", True))
        bf_rss_items = fetch_rss_items(
            feed_url=bf_rss_feed,
            max_items=bf_max,
            mode=bf_mode,
            hours_window=bf_hours,
            ignore_time_filter=bf_rss_ignore,
        )
        bf_dom_items = fetch_boursier_france_dom_items(
            page_url="https://www.boursier.com/actualites/france",
            max_items=bf_max,
            mode=bf_mode,
            hours_window=bf_hours,
            use_firecrawl_fallback=bf_use_firecrawl,
        )
        bf_items = merge_article_items(bf_dom_items, bf_rss_items, bf_max) if bf_rss_dom else bf_rss_items
        _add("boursier_france", "Boursier France", bf_items)

    return results


def _render_mega_job_previews(job, prefix: str, label: str) -> None:
    show_key = f"mega_{prefix}_show_json_state"
    ready_key = f"mega_{prefix}_json_ready"
    if show_key not in st.session_state:
        st.session_state[show_key] = False
    if ready_key not in st.session_state:
        st.session_state[ready_key] = False

    status = job.get_status()
    if status.get("buffer_text"):
        st.divider()
        st.markdown(f"**{label} — Preview concaténée (buffer)**")
        edited_buffer = st.text_area(
            label="",
            value=status.get("buffer_text", ""),
            height=260,
            key=f"mega_{prefix}_buffer_editor",
        )
        col_json, col_clear_buf = st.columns(2)
        with col_json:
            if st.button("✅ Dédoublonner + JSON", use_container_width=True, key=f"mega_{prefix}_finalize"):
                job.set_buffer_text(edited_buffer)
                result = job.finalize_buffer()
                if result.get("status") == "success":
                    st.success(f"{len(result.get('items', []))} items générés")
                    st.session_state[ready_key] = True
                    st.session_state[show_key] = False
                else:
                    st.error(result.get("message", "Erreur JSON"))
        with col_clear_buf:
            if st.button("🧹 Clear buffer", use_container_width=True, key=f"mega_{prefix}_clear_buffer"):
                job.set_buffer_text("")
                st.rerun()

    if (
        st.session_state[ready_key]
        and status.get("json_preview_text")
        and not st.session_state[show_key]
    ):
        if st.button("🧾 Afficher preview JSON", use_container_width=True, key=f"mega_{prefix}_show_json_btn"):
            st.session_state[show_key] = True
            st.rerun()

    if status.get("json_preview_text") and st.session_state[show_key]:
        st.markdown(f"**{label} — Preview JSON**")
        edited_json = st.text_area(
            label="",
            value=status.get("json_preview_text", ""),
            height=320,
            key=f"mega_{prefix}_json_editor",
        )
        col_send, col_clear_json = st.columns(2)
        with col_send:
            if st.button("✅ Envoyer en DB", use_container_width=True, key=f"mega_{prefix}_send_db"):
                result = job.send_to_db()
                if result.get("status") == "success":
                    st.success(f"{result.get('inserted', 0)} items insérés en base")
                else:
                    st.error(result.get("message", "Erreur DB"))
        with col_clear_json:
            if st.button("🧹 Clear JSON", use_container_width=True, key=f"mega_{prefix}_clear_json"):
                job.json_preview_text = ""
                job.json_items = []
                st.session_state[show_key] = False
                st.session_state[ready_key] = False
                st.rerun()


if st.button("🧹 Clear all jobs", use_container_width=True, key="news_clear_all"):
    clear_all_jobs()
    st.success("Tous les jobs ont été réinitialisés.")
    st.rerun()

with st.expander("▸ Mega Job — Run all", expanded=False):
    st.caption("Le Mega Job utilise les paramètres de chaque job (fenêtre temporelle, limites, RSS/DOM, Firecrawl).")

    all_sources = [
        ("bfm", "BFM Bourse"),
        ("beincrypto", "BeInCrypto"),
        ("boursedirect", "Bourse Direct"),
        ("boursedirect_indices", "Bourse Direct Indices"),
        ("boursier_economie", "Boursier Économie"),
        ("boursier_macroeconomie", "Boursier Macroeconomie"),
        ("boursier_france", "Boursier France"),
    ]
    source_labels = [label for _, label in all_sources]
    if not st.session_state.mega_run_sources:
        st.session_state.mega_run_sources = source_labels
    selected_sources = st.multiselect(
        "Sources",
        options=source_labels,
        key="mega_run_sources",
    )
    selected_source_keys = [
        key for key, label in all_sources if label in selected_sources
    ]

    col_load, col_check, col_uncheck = st.columns(3)
    with col_load:
        if st.button("🔎 Charger toutes les URLs", use_container_width=True, key="mega_run_load"):
            _clear_mega_state()
            st.session_state.mega_run_candidates = _collect_mega_urls(
                source_keys=selected_source_keys,
            )
            st.rerun()
    with col_check:
        if st.button("☑️ Cocher tout", use_container_width=True, key="mega_run_check_all"):
            for idx, item in enumerate(st.session_state.mega_run_candidates):
                if item.get("source_label") in st.session_state.get("mega_run_sources", []):
                    st.session_state[f"mega_run_pick_{idx}"] = True
            st.rerun()
    with col_uncheck:
        if st.button("☐ Décocher tout", use_container_width=True, key="mega_run_uncheck_all"):
            for idx, item in enumerate(st.session_state.mega_run_candidates):
                if item.get("source_label") in st.session_state.get("mega_run_sources", []):
                    st.session_state[f"mega_run_pick_{idx}"] = False
            st.rerun()

    mega_selected_urls = []
    if st.session_state.mega_run_candidates:
        filtered_candidates = [
            item for item in st.session_state.mega_run_candidates
            if item.get("source_label") in selected_sources
        ]
        st.caption(f"{len(filtered_candidates)} URL(s) détectée(s)")
        for idx, item in enumerate(st.session_state.mega_run_candidates):
            if item.get("source_label") not in selected_sources:
                continue
            label = f"[{item.get('source_label','')}] {item.get('title','')}".strip()
            if not label or label == "[]":
                label = item.get("url", "")
            key = f"mega_run_pick_{idx}"
            if key not in st.session_state:
                st.session_state[key] = True
            checked = st.checkbox(label, key=key)
            if checked:
                mega_selected_urls.append(item)
        st.caption(f"{len(mega_selected_urls)} article(s) sélectionné(s)")
    else:
        st.caption("Clique sur “Charger toutes les URLs” pour générer la liste.")

    if st.session_state.mega_run_candidates:
        if st.button("🚀 Lancer sélection", use_container_width=True, key="mega_run_launch"):
            if not mega_selected_urls:
                st.error("Sélectionne au moins un article.")
            else:
                grouped: dict[str, list[dict]] = {}
                for item in mega_selected_urls:
                    grouped.setdefault(item["source_key"], []).append({
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "label_dt": item.get("label_dt", ""),
                    })

                if "bfm" in grouped:
                    bfm_mode = _mode_from_label(_get_state("news_mode", "Dernières X heures"))
                    bfm_hours = int(_get_state("news_hours_window", 24))
                    bfm_max_per = int(_get_state("news_max_per", 400))
                    bfm_config = JobConfig(
                        entry_url="https://www.tradingsat.com/actualites/",
                        mode=bfm_mode,
                        hours_window=bfm_hours,
                        max_articles_total=len(grouped["bfm"]),
                        max_articles_per_bulletin=bfm_max_per,
                        scroll_min_px=int(_get_state("news_scroll_min", 400)),
                        scroll_max_px=int(_get_state("news_scroll_max", 1200)),
                        min_page_time=int(_get_state("news_page_min", 10)),
                        max_page_time=int(_get_state("news_page_max", 45)),
                        wait_min_action=float(_get_state("news_wait_min", 0.6)),
                        wait_max_action=float(_get_state("news_wait_max", 2.5)),
                        shuffle_urls=bool(_get_state("news_shuffle", True)),
                        dry_run=bool(_get_state("news_dry_run", False)),
                        max_consecutive_errors=int(_get_state("news_max_errors", 3)),
                        global_timeout_minutes=int(_get_state("news_timeout", 15)),
                        pause_on_captcha=bool(_get_state("news_pause_captcha", True)),
                        remove_buffer_after_success=bool(_get_state("news_remove_buffer", True)),
                        headless=bool(_get_state("news_headless", True)),
                        use_rss=bool(_get_state("news_use_rss", True)),
                        rss_feed_url=_get_state("news_rss_feed", "https://www.tradingsat.com/rssfeed.php"),
                        rss_ignore_time_filter=bool(_get_state("news_rss_ignore_time", False)),
                        rss_use_dom_fallback=bool(_get_state("news_rss_dom_fallback", True)),
                        use_firecrawl=bool(_get_state("news_use_firecrawl", True)),
                        urls_override=grouped["bfm"],
                    )
                    get_bfm_job().start(bfm_config)

                if "beincrypto" in grouped:
                    bein_mode = _mode_from_label(_get_state("bein_mode", "Dernières X heures"))
                    bein_hours = int(_get_state("bein_hours_window", 24))
                    bein_max_per = int(_get_state("bein_max_per", 400))
                    bein_config = BeInJobConfig(
                        entry_url="https://fr.beincrypto.com/",
                        mode=bein_mode,
                        hours_window=bein_hours,
                        max_articles_total=len(grouped["beincrypto"]),
                        max_articles_per_bulletin=bein_max_per,
                        wait_min_action=float(_get_state("bein_wait_min", 0.6)),
                        wait_max_action=float(_get_state("bein_wait_max", 2.5)),
                        shuffle_urls=bool(_get_state("bein_shuffle", True)),
                        dry_run=bool(_get_state("bein_dry_run", False)),
                        max_consecutive_errors=int(_get_state("bein_max_errors", 3)),
                        global_timeout_minutes=int(_get_state("bein_timeout", 15)),
                        remove_buffer_after_success=bool(_get_state("bein_remove_buffer", True)),
                        use_rss=bool(_get_state("bein_use_rss", True)),
                        rss_feed_url=_get_state("bein_rss_feed", "https://fr.beincrypto.com/feed/"),
                        rss_ignore_time_filter=bool(_get_state("bein_rss_ignore_time", False)),
                        rss_use_dom_fallback=bool(_get_state("bein_rss_dom_fallback", True)),
                        use_firecrawl=bool(_get_state("bein_use_firecrawl", True)),
                        urls_override=grouped["beincrypto"],
                    )
                    get_beincrypto_job().start(bein_config)

                if "boursedirect" in grouped:
                    bd_mode = _mode_from_label(_get_state("boursedirect_mode", "Dernières X heures"))
                    bd_hours = int(_get_state("boursedirect_hours_window", 24))
                    bd_max_per = int(_get_state("boursedirect_max_per", 400))
                    bd_config = BourseDirectJobConfig(
                        entry_url="https://www.boursedirect.fr/fr/actualites/categorie/marches",
                        mode=bd_mode,
                        hours_window=bd_hours,
                        max_articles_total=len(grouped["boursedirect"]),
                        max_articles_per_bulletin=bd_max_per,
                        wait_min_action=float(_get_state("boursedirect_wait_min", 0.6)),
                        wait_max_action=float(_get_state("boursedirect_wait_max", 2.5)),
                        shuffle_urls=bool(_get_state("boursedirect_shuffle", True)),
                        dry_run=bool(_get_state("boursedirect_dry_run", False)),
                        max_consecutive_errors=int(_get_state("boursedirect_max_errors", 3)),
                        global_timeout_minutes=int(_get_state("boursedirect_timeout", 15)),
                        remove_buffer_after_success=bool(_get_state("boursedirect_remove_buffer", True)),
                        use_rss=bool(_get_state("boursedirect_use_rss", True)),
                        rss_feed_url=_get_state("boursedirect_rss_feed", "https://www.boursedirect.fr/fr/actualites/categorie/marches"),
                        rss_ignore_time_filter=bool(_get_state("boursedirect_rss_ignore_time", False)),
                        rss_use_dom_fallback=bool(_get_state("boursedirect_rss_dom_fallback", True)),
                        use_firecrawl=bool(_get_state("boursedirect_use_firecrawl", True)),
                        urls_override=grouped["boursedirect"],
                    )
                    get_boursedirect_job().start(bd_config)

                if "boursedirect_indices" in grouped:
                    bdi_mode = _mode_from_label(_get_state("boursedirect_indices_mode", "Dernières X heures"))
                    bdi_hours = int(_get_state("boursedirect_indices_hours_window", 24))
                    bdi_max_per = int(_get_state("boursedirect_indices_max_per", 400))
                    bdi_config = BourseDirectIndicesJobConfig(
                        entry_url="https://www.boursedirect.fr/fr/actualites/categorie/indices",
                        mode=bdi_mode,
                        hours_window=bdi_hours,
                        max_articles_total=len(grouped["boursedirect_indices"]),
                        max_articles_per_bulletin=bdi_max_per,
                        wait_min_action=float(_get_state("boursedirect_indices_wait_min", 0.6)),
                        wait_max_action=float(_get_state("boursedirect_indices_wait_max", 2.5)),
                        shuffle_urls=bool(_get_state("boursedirect_indices_shuffle", True)),
                        dry_run=bool(_get_state("boursedirect_indices_dry_run", False)),
                        max_consecutive_errors=int(_get_state("boursedirect_indices_max_errors", 3)),
                        global_timeout_minutes=int(_get_state("boursedirect_indices_timeout", 15)),
                        remove_buffer_after_success=bool(_get_state("boursedirect_indices_remove_buffer", True)),
                        use_rss=bool(_get_state("boursedirect_indices_use_rss", True)),
                        rss_feed_url=_get_state("boursedirect_indices_rss_feed", "https://www.boursedirect.fr/fr/actualites/categorie/indices"),
                        rss_ignore_time_filter=bool(_get_state("boursedirect_indices_rss_ignore_time", False)),
                        rss_use_dom_fallback=bool(_get_state("boursedirect_indices_rss_dom_fallback", True)),
                        use_firecrawl=bool(_get_state("boursedirect_indices_use_firecrawl", True)),
                        urls_override=grouped["boursedirect_indices"],
                    )
                    get_boursedirect_indices_job().start(bdi_config)

                if "boursier_economie" in grouped:
                    be_mode = _mode_from_label(_get_state("boursier_economie_mode", "Dernières X heures"))
                    be_hours = int(_get_state("boursier_economie_hours_window", 24))
                    be_max_per = int(_get_state("boursier_economie_max_per", 400))
                    be_config = BoursierEconomieJobConfig(
                        entry_url="https://www.boursier.com/actualites/economie",
                        mode=be_mode,
                        hours_window=be_hours,
                        max_articles_total=len(grouped["boursier_economie"]),
                        max_articles_per_bulletin=be_max_per,
                        wait_min_action=float(_get_state("boursier_economie_wait_min", 0.6)),
                        wait_max_action=float(_get_state("boursier_economie_wait_max", 2.5)),
                        shuffle_urls=bool(_get_state("boursier_economie_shuffle", True)),
                        dry_run=bool(_get_state("boursier_economie_dry_run", False)),
                        max_consecutive_errors=int(_get_state("boursier_economie_max_errors", 3)),
                        global_timeout_minutes=int(_get_state("boursier_economie_timeout", 15)),
                        remove_buffer_after_success=bool(_get_state("boursier_economie_remove_buffer", True)),
                        use_rss=bool(_get_state("boursier_economie_use_rss", True)),
                        rss_feed_url=_get_state("boursier_economie_rss_feed", "https://www.boursier.com/actualites/economie"),
                        rss_ignore_time_filter=bool(_get_state("boursier_economie_rss_ignore_time", False)),
                        rss_use_dom_fallback=bool(_get_state("boursier_economie_rss_dom_fallback", True)),
                        use_firecrawl=bool(_get_state("boursier_economie_use_firecrawl", True)),
                        urls_override=grouped["boursier_economie"],
                    )
                    get_boursier_economie_job().start(be_config)

                if "boursier_macroeconomie" in grouped:
                    bm_mode = _mode_from_label(_get_state("boursier_macroeconomie_mode", "Dernières X heures"))
                    bm_hours = int(_get_state("boursier_macroeconomie_hours_window", 24))
                    bm_max_per = int(_get_state("boursier_macroeconomie_max_per", 400))
                    bm_config = BoursierMacroeconomieJobConfig(
                        entry_url="https://www.boursier.com/actualites/macroeconomie",
                        mode=bm_mode,
                        hours_window=bm_hours,
                        max_articles_total=len(grouped["boursier_macroeconomie"]),
                        max_articles_per_bulletin=bm_max_per,
                        wait_min_action=float(_get_state("boursier_macroeconomie_wait_min", 0.6)),
                        wait_max_action=float(_get_state("boursier_macroeconomie_wait_max", 2.5)),
                        shuffle_urls=bool(_get_state("boursier_macroeconomie_shuffle", True)),
                        dry_run=bool(_get_state("boursier_macroeconomie_dry_run", False)),
                        max_consecutive_errors=int(_get_state("boursier_macroeconomie_max_errors", 3)),
                        global_timeout_minutes=int(_get_state("boursier_macroeconomie_timeout", 15)),
                        remove_buffer_after_success=bool(_get_state("boursier_macroeconomie_remove_buffer", True)),
                        use_rss=bool(_get_state("boursier_macroeconomie_use_rss", True)),
                        rss_feed_url=_get_state("boursier_macroeconomie_rss_feed", "https://www.boursier.com/actualites/macroeconomie"),
                        rss_ignore_time_filter=bool(_get_state("boursier_macroeconomie_rss_ignore_time", False)),
                        rss_use_dom_fallback=bool(_get_state("boursier_macroeconomie_rss_dom_fallback", True)),
                        use_firecrawl=bool(_get_state("boursier_macroeconomie_use_firecrawl", True)),
                        urls_override=grouped["boursier_macroeconomie"],
                    )
                    get_boursier_macroeconomie_job().start(bm_config)

                if "boursier_france" in grouped:
                    bf_mode = _mode_from_label(_get_state("boursier_france_mode", "Dernières X heures"))
                    bf_hours = int(_get_state("boursier_france_hours_window", 24))
                    bf_max_per = int(_get_state("boursier_france_max_per", 400))
                    bf_config = BoursierFranceJobConfig(
                        entry_url="https://www.boursier.com/actualites/france",
                        mode=bf_mode,
                        hours_window=bf_hours,
                        max_articles_total=len(grouped["boursier_france"]),
                        max_articles_per_bulletin=bf_max_per,
                        wait_min_action=float(_get_state("boursier_france_wait_min", 0.6)),
                        wait_max_action=float(_get_state("boursier_france_wait_max", 2.5)),
                        shuffle_urls=bool(_get_state("boursier_france_shuffle", True)),
                        dry_run=bool(_get_state("boursier_france_dry_run", False)),
                        max_consecutive_errors=int(_get_state("boursier_france_max_errors", 3)),
                        global_timeout_minutes=int(_get_state("boursier_france_timeout", 15)),
                        remove_buffer_after_success=bool(_get_state("boursier_france_remove_buffer", True)),
                        use_rss=bool(_get_state("boursier_france_use_rss", True)),
                        rss_feed_url=_get_state("boursier_france_rss_feed", "https://www.boursier.com/actualites/france"),
                        rss_ignore_time_filter=bool(_get_state("boursier_france_rss_ignore_time", False)),
                        rss_use_dom_fallback=bool(_get_state("boursier_france_rss_dom_fallback", True)),
                        use_firecrawl=bool(_get_state("boursier_france_use_firecrawl", True)),
                        urls_override=grouped["boursier_france"],
                    )
                    get_boursier_france_job().start(bf_config)

                st.success("Mega job lancé.")
                st.rerun()

    # Aggregate progress/status
    job_statuses = [
        ("BFM Bourse", get_bfm_job().get_status()),
        ("BeInCrypto", get_beincrypto_job().get_status()),
        ("Bourse Direct", get_boursedirect_job().get_status()),
        ("Bourse Direct Indices", get_boursedirect_indices_job().get_status()),
        ("Boursier Économie", get_boursier_economie_job().get_status()),
        ("Boursier Macroeconomie", get_boursier_macroeconomie_job().get_status()),
        ("Boursier France", get_boursier_france_job().get_status()),
    ]
    total_all = sum(status.get("total", 0) for _, status in job_statuses)
    processed_all = sum(status.get("processed", 0) for _, status in job_statuses)
    skipped_all = sum(status.get("skipped", 0) for _, status in job_statuses)
    st.progress(processed_all / max(total_all, 1))
    st.caption(f"{processed_all}/{total_all} traités · {skipped_all} ignorés")
    for label, status in job_statuses:
        last_log = status.get("last_log")
        state = status.get("state")
        if last_log:
            st.caption(f"{label} — {state} — {last_log}")

    _render_mega_job_previews(get_boursier_economie_job(), "boursier_economie", "Boursier Économie")
    _render_mega_job_previews(get_boursier_france_job(), "boursier_france", "Boursier France")
    _render_mega_job_previews(get_boursier_macroeconomie_job(), "boursier_macroeconomie", "Boursier Macroeconomie")
    _render_mega_job_previews(get_boursedirect_job(), "boursedirect", "Bourse Direct")
    _render_mega_job_previews(get_boursedirect_indices_job(), "boursedirect_indices", "Bourse Direct Indices")
    _render_mega_job_previews(get_beincrypto_job(), "beincrypto", "BeInCrypto")
    _render_mega_job_previews(get_bfm_job(), "bfm_bourse", "BFM Bourse")

    if any(status.get("state") in ("running", "paused") for _, status in job_statuses):
        st.info("Mega job en cours — rafraîchissement automatique activé.")
        time.sleep(2)
        st.rerun()

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
if "boursier_macroeconomie_rss_candidates" not in st.session_state:
    st.session_state.boursier_macroeconomie_rss_candidates = []
if "boursier_macroeconomie_show_json_state" not in st.session_state:
    st.session_state.boursier_macroeconomie_show_json_state = False
if "boursier_macroeconomie_json_ready" not in st.session_state:
    st.session_state.boursier_macroeconomie_json_ready = False
if "boursier_france_rss_candidates" not in st.session_state:
    st.session_state.boursier_france_rss_candidates = []
if "boursier_france_show_json_state" not in st.session_state:
    st.session_state.boursier_france_show_json_state = False
if "boursier_france_json_ready" not in st.session_state:
    st.session_state.boursier_france_json_ready = False
if "boursier_france_last_params" not in st.session_state:
    st.session_state.boursier_france_last_params = None
if "mega_run_candidates" not in st.session_state:
    st.session_state.mega_run_candidates = []
if "mega_run_sources" not in st.session_state:
    st.session_state.mega_run_sources = []

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
            value=24,
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
                max_value=1000,
                value=400,
                step=1,
                key="news_max_total"
            )
        with col_max_per:
            max_articles_per_bulletin = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=1000,
                value=400,
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
            value=24,
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
                max_value=1000,
                value=400,
                step=1,
                key="bein_max_total",
            )
        with col_max_per:
            bein_max_articles_per = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=1000,
                value=400,
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
                    use_firecrawl_fallback=bool(bein_use_firecrawl),
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
            value=24,
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
                max_value=1000,
                value=400,
                step=1,
                key="boursedirect_max_total",
            )
        with col_max_per:
            boursedirect_max_articles_per = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=1000,
                value=400,
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
            value=24,
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
                max_value=1000,
                value=400,
                step=1,
                key="boursedirect_indices_max_total",
            )
        with col_max_per:
            boursedirect_indices_max_articles_per = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=1000,
                value=400,
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
            value=24,
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
                max_value=1000,
                value=400,
                step=1,
                key="boursier_economie_max_total",
            )
        with col_max_per:
            boursier_economie_max_articles_per = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=1000,
                value=400,
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

with st.expander("▸ Job — Boursier Macroeconomie", expanded=False):
    boursier_macroeconomie_job = get_boursier_macroeconomie_job()
    col_open, col_launch, col_clear = st.columns([2, 1, 1])

    with col_open:
        st.link_button("🔗 Ouvrir l’URL", "https://www.boursier.com/actualites/macroeconomie")
    with col_launch:
        boursier_macroeconomie_launch = st.button("▶️ Lancer", use_container_width=True, key="boursier_macroeconomie_launch")
    with col_clear:
        boursier_macroeconomie_clear = st.button("🧹 Clear", use_container_width=True, key="boursier_macroeconomie_clear")

    with st.expander("Fenêtre temporelle", expanded=True):
        boursier_macroeconomie_mode = st.radio(
            "Mode",
            options=["Aujourd’hui", "Dernières X heures"],
            horizontal=True,
            index=1,
            key="boursier_macroeconomie_mode",
        )
        boursier_macroeconomie_hours_window = st.slider(
            "Dernières X heures",
            min_value=1,
            max_value=24,
            value=24,
            step=1,
            key="boursier_macroeconomie_hours_window",
        )

    with st.expander("Settings", expanded=False):
        st.markdown("**Limites**")
        col_max_total, col_max_per = st.columns(2)
        with col_max_total:
            boursier_macroeconomie_max_articles_total = st.number_input(
                "Max articles total",
                min_value=1,
                max_value=1000,
                value=400,
                step=1,
                key="boursier_macroeconomie_max_total",
            )
        with col_max_per:
            boursier_macroeconomie_max_articles_per = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=1000,
                value=400,
                step=1,
                key="boursier_macroeconomie_max_per",
            )

        st.markdown("**Timing**")
        col_wait_min, col_wait_max = st.columns(2)
        with col_wait_min:
            boursier_macroeconomie_wait_min_action = st.number_input(
                "Wait min action (s)",
                min_value=0.1,
                max_value=5.0,
                value=0.6,
                step=0.1,
                key="boursier_macroeconomie_wait_min",
            )
        with col_wait_max:
            boursier_macroeconomie_wait_max_action = st.number_input(
                "Wait max action (s)",
                min_value=0.2,
                max_value=8.0,
                value=2.5,
                step=0.1,
                key="boursier_macroeconomie_wait_max",
            )

        boursier_macroeconomie_shuffle_urls = st.checkbox(
            "Shuffle URLs",
            value=True,
            key="boursier_macroeconomie_shuffle",
        )
        boursier_macroeconomie_dry_run = st.checkbox(
            "DRY RUN",
            value=False,
            key="boursier_macroeconomie_dry_run",
        )

        st.markdown("**Safety**")
        col_err, col_timeout = st.columns(2)
        with col_err:
            boursier_macroeconomie_max_consecutive_errors = st.number_input(
                "Max erreurs consécutives",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                key="boursier_macroeconomie_max_errors",
            )
        with col_timeout:
            boursier_macroeconomie_global_timeout_minutes = st.number_input(
                "Timeout global job (min)",
                min_value=1,
                max_value=60,
                value=15,
                step=1,
                key="boursier_macroeconomie_timeout",
            )

        boursier_macroeconomie_remove_buffer = st.checkbox(
            "Supprimer buffer après succès",
            value=True,
            key="boursier_macroeconomie_remove_buffer",
        )

        st.markdown("**Source URLs**")
        boursier_macroeconomie_rss_feed_url = st.text_input(
            "RSS feed",
            value="https://www.boursier.com/actualites/macroeconomie",
            key="boursier_macroeconomie_rss_feed",
        )
        boursier_macroeconomie_use_rss = st.checkbox(
            "Mode RSS/DOM",
            value=True,
            key="boursier_macroeconomie_use_rss",
        )
        boursier_macroeconomie_use_firecrawl = st.checkbox(
            "Scraper articles via Firecrawl",
            value=True,
            key="boursier_macroeconomie_use_firecrawl",
        )
        boursier_macroeconomie_rss_ignore_time_filter = st.checkbox(
            "Ignorer filtre temporel RSS",
            value=False,
            key="boursier_macroeconomie_rss_ignore_time",
        )
        boursier_macroeconomie_rss_use_dom_fallback = st.checkbox(
            "Compléter via DOM (Macroeconomie)",
            value=True,
            key="boursier_macroeconomie_rss_dom_fallback",
        )

    boursier_macroeconomie_selected_urls = []
    if boursier_macroeconomie_use_rss:
        col_clear, col_uncheck = st.columns(2)
        with col_clear:
            if st.button("🧹 Clear liste", use_container_width=True, key="boursier_macroeconomie_rss_clear"):
                st.session_state.boursier_macroeconomie_rss_candidates = []
                st.rerun()
        with col_uncheck:
            if st.button("☐ Décocher tout", use_container_width=True, key="boursier_macroeconomie_rss_uncheck_all"):
                for idx in range(len(st.session_state.boursier_macroeconomie_rss_candidates)):
                    st.session_state[f"boursier_macroeconomie_rss_pick_{idx}"] = False
                st.rerun()

        if st.session_state.boursier_macroeconomie_rss_candidates:
            st.caption("Sélectionne les articles à traiter :")
            for idx, item in enumerate(st.session_state.boursier_macroeconomie_rss_candidates):
                label = f"{item.get('title','')}".strip() or item.get("url", "")
                key = f"boursier_macroeconomie_rss_pick_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = True
                checked = st.checkbox(label, key=key)
                if checked:
                    boursier_macroeconomie_selected_urls.append(item)
            st.caption(f"{len(boursier_macroeconomie_selected_urls)} article(s) sélectionné(s)")
        else:
            st.caption("Clique sur Lancer pour charger la liste.")

    if st.session_state.boursier_macroeconomie_rss_candidates:
        if st.button("🧭 Scrapper les articles", use_container_width=True, key="boursier_macroeconomie_scrape_articles"):
            if not boursier_macroeconomie_selected_urls:
                st.error("Sélectionne au moins un article.")
            else:
                boursier_macroeconomie_job.set_buffer_text("")
                boursier_macroeconomie_job.json_preview_text = ""
                boursier_macroeconomie_job.json_items = []
                st.session_state.boursier_macroeconomie_show_json_state = False
                st.session_state.boursier_macroeconomie_json_ready = False
                config = BoursierMacroeconomieJobConfig(
                    entry_url="https://www.boursier.com/actualites/macroeconomie",
                    mode="today" if boursier_macroeconomie_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(boursier_macroeconomie_hours_window),
                    max_articles_total=int(boursier_macroeconomie_max_articles_total),
                    max_articles_per_bulletin=int(boursier_macroeconomie_max_articles_per),
                    wait_min_action=float(boursier_macroeconomie_wait_min_action),
                    wait_max_action=float(boursier_macroeconomie_wait_max_action),
                    shuffle_urls=bool(boursier_macroeconomie_shuffle_urls),
                    dry_run=bool(boursier_macroeconomie_dry_run),
                    max_consecutive_errors=int(boursier_macroeconomie_max_consecutive_errors),
                    global_timeout_minutes=int(boursier_macroeconomie_global_timeout_minutes),
                    remove_buffer_after_success=bool(boursier_macroeconomie_remove_buffer),
                    use_rss=bool(boursier_macroeconomie_use_rss),
                    rss_feed_url=boursier_macroeconomie_rss_feed_url,
                    rss_ignore_time_filter=bool(boursier_macroeconomie_rss_ignore_time_filter),
                    rss_use_dom_fallback=bool(boursier_macroeconomie_rss_use_dom_fallback),
                    use_firecrawl=bool(boursier_macroeconomie_use_firecrawl),
                    urls_override=boursier_macroeconomie_selected_urls,
                )
                boursier_macroeconomie_job.start(config)
                st.success("Scraping lancé.")

    if boursier_macroeconomie_launch:
        if boursier_macroeconomie_use_rss:
            boursier_macroeconomie_job.set_buffer_text("")
            boursier_macroeconomie_job.json_preview_text = ""
            boursier_macroeconomie_job.json_items = []
            st.session_state.boursier_macroeconomie_show_json_state = False
            st.session_state.boursier_macroeconomie_json_ready = False
            rss_items = fetch_rss_items(
                feed_url=boursier_macroeconomie_rss_feed_url,
                max_items=int(boursier_macroeconomie_max_articles_total),
                mode="today" if boursier_macroeconomie_mode == "Aujourd’hui" else "last_hours",
                hours_window=int(boursier_macroeconomie_hours_window),
                ignore_time_filter=bool(boursier_macroeconomie_rss_ignore_time_filter),
            )
            if boursier_macroeconomie_rss_use_dom_fallback:
                dom_items = fetch_boursier_macroeconomie_dom_items(
                    page_url="https://www.boursier.com/actualites/macroeconomie",
                    max_items=int(boursier_macroeconomie_max_articles_total),
                    mode="today" if boursier_macroeconomie_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(boursier_macroeconomie_hours_window),
                    use_firecrawl_fallback=bool(boursier_macroeconomie_use_firecrawl),
                )
                st.session_state.boursier_macroeconomie_rss_candidates = merge_article_items(
                    dom_items,
                    rss_items,
                    int(boursier_macroeconomie_max_articles_total),
                )
            else:
                st.session_state.boursier_macroeconomie_rss_candidates = rss_items
            boursier_macroeconomie_job.status_log.append("🔎 URLs chargées")
            if not st.session_state.boursier_macroeconomie_rss_candidates:
                st.warning("Aucune URL détectée. DOM vide ou bloqué ; active Firecrawl ou un RSS valide.")
            st.rerun()

    if boursier_macroeconomie_clear:
        boursier_macroeconomie_job.clear()
        st.session_state.boursier_macroeconomie_rss_candidates = []
        st.session_state.boursier_macroeconomie_show_json_state = False
        st.session_state.boursier_macroeconomie_json_ready = False
        for key in list(st.session_state.keys()):
            if key.startswith("boursier_macroeconomie_rss_pick_"):
                st.session_state.pop(key, None)
        st.success("Job réinitialisé.")
        st.rerun()

    boursier_macroeconomie_status = boursier_macroeconomie_job.get_status()
    boursier_macroeconomie_state = boursier_macroeconomie_status.get("state")
    boursier_macroeconomie_total = boursier_macroeconomie_status.get("total", 0)
    boursier_macroeconomie_processed = boursier_macroeconomie_status.get("processed", 0)
    boursier_macroeconomie_skipped = boursier_macroeconomie_status.get("skipped", 0)
    boursier_macroeconomie_started_at = boursier_macroeconomie_status.get("started_at")
    boursier_macroeconomie_last_log = boursier_macroeconomie_status.get("last_log", "")

    st.progress(boursier_macroeconomie_processed / max(boursier_macroeconomie_total, 1))
    status_parts = [
        f"{boursier_macroeconomie_processed}/{boursier_macroeconomie_total} traités",
        f"{boursier_macroeconomie_skipped} ignorés",
    ]
    if boursier_macroeconomie_state:
        status_parts.append(f"état: {boursier_macroeconomie_state}")
    if boursier_macroeconomie_started_at:
        elapsed = int(time.time() - boursier_macroeconomie_started_at)
        status_parts.append(f"{elapsed}s")
    st.caption(" · ".join(status_parts))
    if boursier_macroeconomie_last_log:
        st.caption(f"Statut : {boursier_macroeconomie_last_log}")
    if boursier_macroeconomie_status.get("errors"):
        st.markdown("**Erreurs :**")
        for err in boursier_macroeconomie_status.get("errors")[-3:]:
            st.write(f"⚠️ {err}")
    if boursier_macroeconomie_state in ("running", "paused"):
        st.info("Job en cours — rafraîchissement automatique activé.")
        time.sleep(2)
        st.rerun()

    if boursier_macroeconomie_status.get("buffer_text"):
        st.divider()
        st.markdown("**Preview concaténée (buffer)**")
        boursier_macroeconomie_edited_buffer = st.text_area(
            label="",
            value=boursier_macroeconomie_status.get("buffer_text", ""),
            height=320,
            key="boursier_macroeconomie_buffer_editor",
        )
        col_json, col_clear_buf = st.columns(2)
        with col_json:
            if st.button("✅ Dédoublonner + JSON", use_container_width=True, key="boursier_macroeconomie_finalize"):
                boursier_macroeconomie_job.set_buffer_text(boursier_macroeconomie_edited_buffer)
                result = boursier_macroeconomie_job.finalize_buffer()
                if result.get("status") == "success":
                    st.success(f"{len(result.get('items', []))} items générés")
                    st.session_state.boursier_macroeconomie_json_ready = True
                    st.session_state.boursier_macroeconomie_show_json_state = False
                    boursier_macroeconomie_status = boursier_macroeconomie_job.get_status()
                else:
                    st.error(result.get("message", "Erreur JSON"))
        with col_clear_buf:
            if st.button("🧹 Clear buffer", use_container_width=True, key="boursier_macroeconomie_clear_buffer"):
                boursier_macroeconomie_job.set_buffer_text("")
                st.rerun()

    if (
        st.session_state.boursier_macroeconomie_json_ready
        and boursier_macroeconomie_status.get("json_preview_text")
        and not st.session_state.boursier_macroeconomie_show_json_state
    ):
        if st.button("🧾 Afficher preview JSON", use_container_width=True, key="boursier_macroeconomie_show_json_btn"):
            st.session_state.boursier_macroeconomie_show_json_state = True
            st.rerun()

    if boursier_macroeconomie_status.get("json_preview_text") and st.session_state.boursier_macroeconomie_show_json_state:
        st.markdown("**Preview JSON**")
        boursier_macroeconomie_edited_json = st.text_area(
            label="",
            value=boursier_macroeconomie_status.get("json_preview_text", ""),
            height=350,
            key="boursier_macroeconomie_json_editor",
        )
        col_send, col_clear_json = st.columns(2)
        with col_send:
            if st.button("✅ Envoyer en DB", use_container_width=True, key="boursier_macroeconomie_send_db"):
                result = boursier_macroeconomie_job.send_to_db()
                if result.get("status") == "success":
                    st.success(f"{result.get('inserted', 0)} items insérés en base")
                else:
                    st.error(result.get("message", "Erreur DB"))
        with col_clear_json:
            if st.button("🧹 Clear JSON", use_container_width=True, key="boursier_macroeconomie_clear_json"):
                boursier_macroeconomie_job.json_preview_text = ""
                boursier_macroeconomie_job.json_items = []
                st.session_state.boursier_macroeconomie_show_json_state = False
                st.session_state.boursier_macroeconomie_json_ready = False
                st.rerun()

with st.expander("▸ Job — Boursier France", expanded=False):
    boursier_france_job = get_boursier_france_job()
    col_open, col_launch, col_clear = st.columns([2, 1, 1])

    with col_open:
        st.link_button("🔗 Ouvrir l’URL", "https://www.boursier.com/actualites/france/")
    with col_launch:
        boursier_france_launch = st.button("▶️ Lancer", use_container_width=True, key="boursier_france_launch")
    with col_clear:
        boursier_france_clear = st.button("🧹 Clear", use_container_width=True, key="boursier_france_clear")

    with st.expander("Fenêtre temporelle", expanded=True):
        boursier_france_mode = st.radio(
            "Mode",
            options=["Aujourd’hui", "Dernières X heures"],
            horizontal=True,
            index=1,
            key="boursier_france_mode",
        )
        boursier_france_hours_window = st.slider(
            "Dernières X heures",
            min_value=1,
            max_value=24,
            value=24,
            step=1,
            key="boursier_france_hours_window",
        )

    with st.expander("Settings", expanded=False):
        st.markdown("**Limites**")
        col_max_total, col_max_per = st.columns(2)
        with col_max_total:
            boursier_france_max_articles_total = st.number_input(
                "Max articles total",
                min_value=1,
                max_value=1000,
                value=400,
                step=1,
                key="boursier_france_max_total",
            )
        with col_max_per:
            boursier_france_max_articles_per = st.number_input(
                "Max articles par bulletin",
                min_value=1,
                max_value=1000,
                value=400,
                step=1,
                key="boursier_france_max_per",
            )

        st.markdown("**Timing**")
        col_wait_min, col_wait_max = st.columns(2)
        with col_wait_min:
            boursier_france_wait_min_action = st.number_input(
                "Wait min action (s)",
                min_value=0.1,
                max_value=5.0,
                value=0.6,
                step=0.1,
                key="boursier_france_wait_min",
            )
        with col_wait_max:
            boursier_france_wait_max_action = st.number_input(
                "Wait max action (s)",
                min_value=0.2,
                max_value=8.0,
                value=2.5,
                step=0.1,
                key="boursier_france_wait_max",
            )

        boursier_france_shuffle_urls = st.checkbox(
            "Shuffle URLs",
            value=True,
            key="boursier_france_shuffle",
        )
        boursier_france_dry_run = st.checkbox(
            "DRY RUN",
            value=False,
            key="boursier_france_dry_run",
        )

        st.markdown("**Safety**")
        col_err, col_timeout = st.columns(2)
        with col_err:
            boursier_france_max_consecutive_errors = st.number_input(
                "Max erreurs consécutives",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                key="boursier_france_max_errors",
            )
        with col_timeout:
            boursier_france_global_timeout_minutes = st.number_input(
                "Timeout global job (min)",
                min_value=1,
                max_value=60,
                value=15,
                step=1,
                key="boursier_france_timeout",
            )

        boursier_france_remove_buffer = st.checkbox(
            "Supprimer buffer après succès",
            value=True,
            key="boursier_france_remove_buffer",
        )

        st.markdown("**Source URLs**")
        boursier_france_rss_feed_url = st.text_input(
            "RSS feed",
            value="https://www.boursier.com/actualites/france",
            key="boursier_france_rss_feed",
        )
        boursier_france_use_rss = st.checkbox(
            "Mode RSS/DOM",
            value=True,
            key="boursier_france_use_rss",
        )
        boursier_france_use_firecrawl = st.checkbox(
            "Scraper articles via Firecrawl",
            value=True,
            key="boursier_france_use_firecrawl",
        )
        boursier_france_rss_ignore_time_filter = st.checkbox(
            "Ignorer filtre temporel RSS",
            value=False,
            key="boursier_france_rss_ignore_time",
        )
        boursier_france_rss_use_dom_fallback = st.checkbox(
            "Compléter via DOM (France)",
            value=True,
            key="boursier_france_rss_dom_fallback",
        )

    boursier_france_params = (
        boursier_france_mode,
        int(boursier_france_hours_window),
        int(boursier_france_max_articles_total),
        bool(boursier_france_rss_ignore_time_filter),
        bool(boursier_france_rss_use_dom_fallback),
        boursier_france_rss_feed_url,
    )
    if st.session_state.boursier_france_last_params != boursier_france_params:
        st.session_state.boursier_france_rss_candidates = []
        for key in list(st.session_state.keys()):
            if key.startswith("boursier_france_rss_pick_"):
                st.session_state.pop(key, None)
        st.session_state.boursier_france_last_params = boursier_france_params

    boursier_france_selected_urls = []
    if boursier_france_use_rss:
        col_clear, col_uncheck = st.columns(2)
        with col_clear:
            if st.button("🧹 Clear liste", use_container_width=True, key="boursier_france_rss_clear"):
                st.session_state.boursier_france_rss_candidates = []
                st.rerun()
        with col_uncheck:
            if st.button("☐ Décocher tout", use_container_width=True, key="boursier_france_rss_uncheck_all"):
                for idx in range(len(st.session_state.boursier_france_rss_candidates)):
                    st.session_state[f"boursier_france_rss_pick_{idx}"] = False
                st.rerun()

        if st.session_state.boursier_france_rss_candidates:
            st.caption("Sélectionne les articles à traiter :")
            for idx, item in enumerate(st.session_state.boursier_france_rss_candidates):
                label = f"{item.get('title','')}".strip() or item.get("url", "")
                key = f"boursier_france_rss_pick_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = True
                checked = st.checkbox(label, key=key)
                if checked:
                    boursier_france_selected_urls.append(item)
            st.caption(f"{len(boursier_france_selected_urls)} article(s) sélectionné(s)")
        else:
            st.caption("Clique sur Lancer pour charger la liste.")

    if st.session_state.boursier_france_rss_candidates:
        if st.button("🧭 Scrapper les articles", use_container_width=True, key="boursier_france_scrape_articles"):
            if not boursier_france_selected_urls:
                st.error("Sélectionne au moins un article.")
            else:
                boursier_france_job.set_buffer_text("")
                boursier_france_job.json_preview_text = ""
                boursier_france_job.json_items = []
                st.session_state.boursier_france_show_json_state = False
                st.session_state.boursier_france_json_ready = False
                config = BoursierFranceJobConfig(
                    entry_url="https://www.boursier.com/actualites/france",
                    mode="today" if boursier_france_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(boursier_france_hours_window),
                    max_articles_total=int(boursier_france_max_articles_total),
                    max_articles_per_bulletin=int(boursier_france_max_articles_per),
                    wait_min_action=float(boursier_france_wait_min_action),
                    wait_max_action=float(boursier_france_wait_max_action),
                    shuffle_urls=bool(boursier_france_shuffle_urls),
                    dry_run=bool(boursier_france_dry_run),
                    max_consecutive_errors=int(boursier_france_max_consecutive_errors),
                    global_timeout_minutes=int(boursier_france_global_timeout_minutes),
                    remove_buffer_after_success=bool(boursier_france_remove_buffer),
                    use_rss=bool(boursier_france_use_rss),
                    rss_feed_url=boursier_france_rss_feed_url,
                    rss_ignore_time_filter=bool(boursier_france_rss_ignore_time_filter),
                    rss_use_dom_fallback=bool(boursier_france_rss_use_dom_fallback),
                    use_firecrawl=bool(boursier_france_use_firecrawl),
                    urls_override=boursier_france_selected_urls,
                )
                boursier_france_job.start(config)
                st.success("Scraping lancé.")

    if boursier_france_launch:
        if boursier_france_use_rss:
            boursier_france_job.set_buffer_text("")
            boursier_france_job.json_preview_text = ""
            boursier_france_job.json_items = []
            st.session_state.boursier_france_show_json_state = False
            st.session_state.boursier_france_json_ready = False
            rss_items = fetch_rss_items(
                feed_url=boursier_france_rss_feed_url,
                max_items=int(boursier_france_max_articles_total),
                mode="today" if boursier_france_mode == "Aujourd’hui" else "last_hours",
                hours_window=int(boursier_france_hours_window),
                ignore_time_filter=bool(boursier_france_rss_ignore_time_filter),
            )
            if boursier_france_rss_use_dom_fallback:
                dom_items = fetch_boursier_france_dom_items(
                    page_url="https://www.boursier.com/actualites/france",
                    max_items=int(boursier_france_max_articles_total),
                    mode="today" if boursier_france_mode == "Aujourd’hui" else "last_hours",
                    hours_window=int(boursier_france_hours_window),
                    use_firecrawl_fallback=bool(boursier_france_use_firecrawl),
                )
                st.session_state.boursier_france_rss_candidates = merge_article_items(
                    dom_items,
                    rss_items,
                    int(boursier_france_max_articles_total),
                )
            else:
                st.session_state.boursier_france_rss_candidates = rss_items
            boursier_france_job.status_log.append("🔎 URLs chargées")
            if not st.session_state.boursier_france_rss_candidates:
                st.warning("Aucune URL détectée. DOM vide ou bloqué ; active Firecrawl ou un RSS valide.")
            st.rerun()

    if boursier_france_clear:
        boursier_france_job.clear()
        st.session_state.boursier_france_rss_candidates = []
        st.session_state.boursier_france_show_json_state = False
        st.session_state.boursier_france_json_ready = False
        st.session_state.boursier_france_last_params = None
        for key in list(st.session_state.keys()):
            if key.startswith("boursier_france_rss_pick_"):
                st.session_state.pop(key, None)
        st.success("Job réinitialisé.")
        st.rerun()

    boursier_france_status = boursier_france_job.get_status()
    boursier_france_state = boursier_france_status.get("state")
    boursier_france_total = boursier_france_status.get("total", 0)
    boursier_france_processed = boursier_france_status.get("processed", 0)
    boursier_france_skipped = boursier_france_status.get("skipped", 0)
    boursier_france_started_at = boursier_france_status.get("started_at")
    boursier_france_last_log = boursier_france_status.get("last_log", "")

    st.progress(boursier_france_processed / max(boursier_france_total, 1))
    status_parts = [
        f"{boursier_france_processed}/{boursier_france_total} traités",
        f"{boursier_france_skipped} ignorés",
    ]
    if boursier_france_state:
        status_parts.append(f"état: {boursier_france_state}")
    if boursier_france_started_at:
        elapsed = int(time.time() - boursier_france_started_at)
        status_parts.append(f"{elapsed}s")
    st.caption(" · ".join(status_parts))
    if boursier_france_last_log:
        st.caption(f"Statut : {boursier_france_last_log}")
    if boursier_france_status.get("errors"):
        st.markdown("**Erreurs :**")
        for err in boursier_france_status.get("errors")[-3:]:
            st.write(f"⚠️ {err}")
    if boursier_france_state in ("running", "paused"):
        st.info("Job en cours — rafraîchissement automatique activé.")
        time.sleep(2)
        st.rerun()

    if boursier_france_status.get("buffer_text"):
        st.divider()
        st.markdown("**Preview concaténée (buffer)**")
        boursier_france_edited_buffer = st.text_area(
            label="",
            value=boursier_france_status.get("buffer_text", ""),
            height=320,
            key="boursier_france_buffer_editor",
        )
        col_json, col_clear_buf = st.columns(2)
        with col_json:
            if st.button("✅ Dédoublonner + JSON", use_container_width=True, key="boursier_france_finalize"):
                boursier_france_job.set_buffer_text(boursier_france_edited_buffer)
                result = boursier_france_job.finalize_buffer()
                if result.get("status") == "success":
                    st.success(f"{len(result.get('items', []))} items générés")
                    st.session_state.boursier_france_json_ready = True
                    st.session_state.boursier_france_show_json_state = False
                    boursier_france_status = boursier_france_job.get_status()
                else:
                    st.error(result.get("message", "Erreur JSON"))
        with col_clear_buf:
            if st.button("🧹 Clear buffer", use_container_width=True, key="boursier_france_clear_buffer"):
                boursier_france_job.set_buffer_text("")
                st.rerun()

    if (
        st.session_state.boursier_france_json_ready
        and boursier_france_status.get("json_preview_text")
        and not st.session_state.boursier_france_show_json_state
    ):
        if st.button("🧾 Afficher preview JSON", use_container_width=True, key="boursier_france_show_json_btn"):
            st.session_state.boursier_france_show_json_state = True
            st.rerun()

    if boursier_france_status.get("json_preview_text") and st.session_state.boursier_france_show_json_state:
        st.markdown("**Preview JSON**")
        boursier_france_edited_json = st.text_area(
            label="",
            value=boursier_france_status.get("json_preview_text", ""),
            height=350,
            key="boursier_france_json_editor",
        )
        col_send, col_clear_json = st.columns(2)
        with col_send:
            if st.button("✅ Envoyer en DB", use_container_width=True, key="boursier_france_send_db"):
                result = boursier_france_job.send_to_db()
                if result.get("status") == "success":
                    st.success(f"{result.get('inserted', 0)} items insérés en base")
                else:
                    st.error(result.get("message", "Erreur DB"))
        with col_clear_json:
            if st.button("🧹 Clear JSON", use_container_width=True, key="boursier_france_clear_json"):
                boursier_france_job.json_preview_text = ""
                boursier_france_job.json_items = []
                st.session_state.boursier_france_show_json_state = False
                st.session_state.boursier_france_json_ready = False
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
