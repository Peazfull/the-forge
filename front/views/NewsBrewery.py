"""
🗞️ NEWS Brewery - Version Refactorisée

Cette version utilise des composants réutilisables au lieu de répéter 400 lignes par source.
Résultat : 3252 lignes → ~500 lignes avec le mega job (-85%)
"""

import time
import streamlit as st

# Imports des composants réutilisables
from front.components.news_source import NewsSourceRenderer

# Imports des services
from services.news_brewery.mega_job import MegaJobConfig, get_mega_job
from services.news_brewery.rss_utils import merge_article_items
from services.news_brewery.sources_registry import get_news_sources
from services.raw_storage.raw_news_service import fetch_raw_news


# ============================================================================
# TITRE & INIT
# ============================================================================

st.title("🗞️ NEWS Brewery")
st.divider()


# ============================================================================
# REGISTRE DES SOURCES - Configuration centralisée
# ============================================================================

# Définition de toutes les sources en un seul endroit
# Ajouter une source = ajouter une entrée ici (10 lignes au lieu de 400 !)

SOURCES = get_news_sources()

# Créer un mapping pour accès rapide
SOURCES_MAP = {src.key: src for src in SOURCES}


# ============================================================================
# MEGA JOB - État et fonctions utilitaires
# ============================================================================

# Init state mega job
if "mega_run_candidates" not in st.session_state:
    st.session_state.mega_run_candidates = []
if "mega_run_sources" not in st.session_state:
    st.session_state.mega_run_sources = []
if "mega_run_launched_sources" not in st.session_state:
    st.session_state.mega_run_launched_sources = []
if "mega_run_status" not in st.session_state:
    st.session_state.mega_run_status = []
if "mega_job_show_json_state" not in st.session_state:
    st.session_state.mega_job_show_json_state = False
if "mega_job_json_ready" not in st.session_state:
    st.session_state.mega_job_json_ready = False


def _clear_job_state(prefix: str) -> None:
    """Nettoie le state d'un job"""
    for key in list(st.session_state.keys()):
        if key.startswith(f"{prefix}rss_pick_"):
            st.session_state.pop(key, None)
    for suffix in ("rss_candidates", "show_json_state", "json_ready", "last_params"):
        st.session_state.pop(f"{prefix}{suffix}", None)


def _clear_mega_state() -> None:
    """Nettoie le state du mega job"""
    for key in list(st.session_state.keys()):
        if key.startswith("mega_run_pick_"):
            st.session_state.pop(key, None)
    st.session_state.mega_run_candidates = []
    st.session_state.mega_run_status = []


def clear_all_jobs() -> None:
    """Clear tous les jobs"""
    for source in SOURCES:
        source.job_factory().clear()
        _clear_job_state(f"{source.key}_")
    _clear_mega_state()


def _mode_from_label(label: str) -> str:
    """Convertit le label du mode en clé"""
    return "today" if label == "Aujourd'hui" else "last_hours"


def _get_state(key: str, default):
    """Récupère une valeur du state"""
    return st.session_state.get(key, default)


def _collect_mega_urls(
    source_keys: list[str] | None = None,
    mega_mode: str = "Dernières X heures",
    mega_hours: int = 24
) -> tuple[list[dict], list[dict]]:
    """Collecte les URLs de toutes les sources sélectionnées avec fenêtre temporelle du Mega Job"""
    results: list[dict] = []
    seen = set()
    source_keys = source_keys or []
    status_entries: list[dict] = []

    def _should_run(source_key: str) -> bool:
        return not source_keys or source_key in source_keys

    def _record(source_key: str, source_label: str, status: str, count: int = 0, message: str = "") -> None:
        status_entries.append({
            "source_key": source_key,
            "source_label": source_label,
            "status": status,
            "count": count,
            "message": message,
        })

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

    # Convertir le mode du Mega Job
    mode = _mode_from_label(mega_mode)
    hours = mega_hours

    # Collecter pour chaque source
    for source in SOURCES:
        if not _should_run(source.key):
            continue
            
        use_rss = bool(_get_state(f"{source.key}_use_rss", True))
        if not use_rss:
            _record(source.key, source.label, "skipped", message="RSS désactivé")
            continue
        
        try:
            max_items = int(_get_state(f"{source.key}_max_total", 400))
            rss_feed = _get_state(f"{source.key}_rss_feed", source.rss_feed_url)
            rss_ignore = bool(_get_state(f"{source.key}_rss_ignore_time", False))
            rss_dom = bool(_get_state(f"{source.key}_rss_dom_fallback", True))
            use_firecrawl = bool(_get_state(f"{source.key}_use_firecrawl", True))
            
            # Fetch RSS
            rss_items = source.fetch_rss_items(
                feed_url=rss_feed,
                max_items=max_items,
                mode=mode,
                hours_window=hours,
                ignore_time_filter=rss_ignore,
            )
            
            # Fetch DOM si fallback
            if rss_dom and source.supports_dom_fallback:
                dom_kwargs = {
                    "page_url": source.entry_url,
                    "max_items": max_items,
                    "mode": mode,
                    "hours_window": hours,
                }
                # Ajouter use_firecrawl_fallback seulement si supporté par la fonction
                if source.supports_firecrawl:
                    try:
                        dom_kwargs["use_firecrawl_fallback"] = use_firecrawl
                        dom_items = source.fetch_dom_items(**dom_kwargs)
                    except TypeError:
                        # Si la fonction ne supporte pas le paramètre, essayer sans
                        dom_kwargs.pop("use_firecrawl_fallback", None)
                        dom_items = source.fetch_dom_items(**dom_kwargs)
                else:
                    dom_items = source.fetch_dom_items(**dom_kwargs)
                
                items = merge_article_items(dom_items, rss_items, max_items)
            else:
                items = rss_items
            
            _add(source.key, source.label, items)
            _record(source.key, source.label, "ok", len(items))
        except Exception as exc:
            _record(source.key, source.label, "error", message=str(exc))

    return results, status_entries


# ============================================================================
# CLEAR ALL JOBS
# ============================================================================

if st.button("🧹 Clear all jobs", use_container_width=True, key="news_clear_all"):
    clear_all_jobs()
    st.success("Tous les jobs ont été réinitialisés.")
    st.rerun()


# ============================================================================
# MEGA JOB - Interface (version simplifiée, garde l'essentiel)
# ============================================================================

with st.expander("▸ Mega Job — Run all", expanded=False):
    st.caption("Le Mega Job utilise les paramètres de chaque job.")

    # Fenêtre temporelle Mega Job
    st.markdown("**⏱️ Fenêtre temporelle**")
    
    col_mode, col_hours = st.columns([2, 1])
    with col_mode:
        mega_mode = st.radio(
            "Mode",
            options=["Aujourd'hui", "Dernières X heures"],
            horizontal=True,
            index=1,
            key="mega_time_mode"
        )
    with col_hours:
        mega_hours = st.slider(
            "Heures",
            min_value=1,
            max_value=24,
            value=24,
            step=1,
            key="mega_time_hours"
        )
    
    st.divider()

    # Sélection des sources
    source_labels = [src.label for src in SOURCES]
    if not st.session_state.mega_run_sources:
        st.session_state.mega_run_sources = source_labels
    
    selected_sources = st.multiselect(
        "Sources",
        options=source_labels,
        key="mega_run_sources",
    )
    
    selected_source_keys = [
        src.key for src in SOURCES if src.label in selected_sources
    ]
    
    st.divider()

    # Boutons
    col_load, col_check, col_uncheck = st.columns(3)
    with col_load:
        if st.button("🔎 Charger toutes les URLs", use_container_width=True, key="mega_run_load"):
            _clear_mega_state()
            results, statuses = _collect_mega_urls(
                source_keys=selected_source_keys,
                mega_mode=mega_mode,
                mega_hours=mega_hours
            )
            st.session_state.mega_run_candidates = results
            st.session_state.mega_run_status = statuses
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

    # Statut
    if st.session_state.mega_run_status:
        total_jobs = len(st.session_state.mega_run_status)
        st.caption(f"Jobs {total_jobs}/{total_jobs} listés")
        total_reported = sum(entry.get("count", 0) for entry in st.session_state.mega_run_status)
        total_unique = len(st.session_state.mega_run_candidates)
        duplicates = max(0, total_reported - total_unique)
        st.caption(f"Total brut: {total_reported} · Uniques: {total_unique} · Doublons: {duplicates}")
        
        for entry in st.session_state.mega_run_status:
            status = entry.get("status")
            icon = "✅" if status == "ok" else ("❌" if status == "error" else "⏭️")
            count = entry.get("count", 0)
            message = entry.get("message", "")
            line = f"{icon} {entry.get('source_label', '')} · {count} URL(s)"
            if message:
                line = f"{line} · {message}"
            st.caption(line)

    # Liste des candidats
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
            if st.checkbox(label, key=key):
                mega_selected_urls.append(item)
        
        st.caption(f"{len(mega_selected_urls)} article(s) sélectionné(s)")
        
        # Bouton de lancement Mega Job
        if len(mega_selected_urls) > 0:
            st.divider()
            col_launch, col_stop = st.columns([3, 1])
            
            mega_job = get_mega_job()
            status = mega_job.get_status()
            
            with col_launch:
                if status["state"] != "running":
                    if st.button("🚀 Lancer Mega Job (Pipeline complet automatique)", use_container_width=True, key="mega_launch"):
                        # Configuration
                        config = MegaJobConfig(
                            source_name="Mega Job Multi-Sources",
                            source_link="",
                            remove_buffer_after_success=False,
                            dry_run=False
                        )
                        mega_job.set_config(config)
                        mega_job.start_auto_scraping(mega_selected_urls)
                        st.rerun()
            
            with col_stop:
                if status["state"] == "running":
                    if st.button("⏹️ Stop", use_container_width=True, key="mega_stop"):
                        mega_job.stop()
                        st.rerun()
            
            # Progress bar et statut
            if status["state"] == "running":
                st.divider()
                progress = status["current_index"] / max(status["total"], 1)
                st.progress(progress)
                st.caption(f"📊 Progression : {status['current_index']}/{status['total']} URLs")
                st.caption(f"✅ Traités : {status['processed']} · ⏭️ Ignorés : {status['skipped']}")
                
                # Dernier log
                if status["last_log"]:
                    st.info(status["last_log"])
                
                # Erreurs
                if status["errors"]:
                    with st.expander(f"⚠️ Erreurs ({len(status['errors'])})", expanded=False):
                        for err in status["errors"][-10:]:  # Dernières 10 erreurs
                            st.warning(err)
                
                # Auto-refresh
                time.sleep(1)
                st.rerun()
            
            # État final
            elif status["state"] == "completed":
                st.success(f"✅ Mega Job terminé ! {status['processed']} articles traités")
                if status["errors"]:
                    st.warning(f"⚠️ {len(status['errors'])} erreurs rencontrées")
                    with st.expander("Voir les erreurs", expanded=False):
                        for err in status["errors"]:
                            st.caption(err)
            
            elif status["state"] == "failed":
                st.error("❌ Mega Job échoué")
                if status["errors"]:
                    with st.expander("Voir les erreurs", expanded=True):
                        for err in status["errors"]:
                            st.caption(err)
            
            elif status["state"] == "stopped":
                st.warning("⏹️ Mega Job arrêté")
        
    else:
        st.caption("Clique sur \"Charger toutes les URLs\" pour générer la liste.")


# ============================================================================
# RENDU DES SOURCES - Une boucle au lieu de 2800 lignes !
# ============================================================================

# C'est ici la magie : au lieu de répéter 400 lignes × 7 sources,
# on fait une simple boucle qui utilise le renderer réutilisable

for source_config in SOURCES:
    renderer = NewsSourceRenderer(source_config)
    renderer.render()


# ============================================================================
# AFFICHAGE DES DERNIERS CONTENUS EN BASE
# ============================================================================

st.divider()
with st.expander("🗄️ Derniers contenus en base", expanded=False):
    raw_items = fetch_raw_news(limit=50)
    if not raw_items:
        st.caption("Aucun contenu en base pour le moment")
    else:
        for item in raw_items:
            st.markdown("---")
            
            # Afficher source avec lien si disponible
            source_info = f"🕒 {item['processed_at']} · Source : {item['source_type']}"
            if item.get('source_name'):
                source_info += f" · {item['source_name']}"
            st.caption(source_info)
            
            # Titre avec lien vers l'article source si disponible
            if item.get('source_link'):
                st.markdown(f"**[{item['title']}]({item['source_link']})**")
            else:
                st.markdown(f"**{item['title']}**")
            
            st.write(item['content'])


# ============================================================================
# FIN - Version refactorisée
# ============================================================================

# Comparaison :
# AVANT : 3252 lignes avec 2800 lignes de duplication
# APRÈS : ~500 lignes (incluant mega job) + 600 lignes de composants réutilisables
# GAIN : -65% de code, maintenance facilitée, cohérence garantie
