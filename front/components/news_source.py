"""
NewsSource Components - Architecture factorisée pour NewsBrewery

Ce module contient les composants réutilisables pour gérer n'importe quelle source de news.
Au lieu de répéter 400 lignes par source, on écrit une seule fois et on réutilise.
"""

import time
from dataclasses import dataclass
from typing import Callable, Optional
import streamlit as st


# ============================================================================
# 1. CONFIGURATION - Définition d'une source
# ============================================================================

@dataclass
class NewsSourceConfig:
    """Configuration complète d'une source de news"""
    
    # Identifiants
    key: str                    # Ex: "bfm", "beincrypto"
    label: str                  # Ex: "BFM Bourse", "BeInCrypto"
    
    # URLs
    entry_url: str              # Page d'entrée
    rss_feed_url: str           # URL du flux RSS
    
    # Fonctions de scraping (injection de dépendances)
    fetch_dom_items: Callable   # Fonction pour scraper le DOM
    fetch_rss_items: Callable   # Fonction pour scraper le RSS
    job_factory: Callable       # Factory pour obtenir le job singleton
    job_config_class: type      # Classe de config du job
    
    # Paramètres par défaut
    default_max_total: int = 400
    default_max_per: int = 400
    default_hours: int = 24
    
    # Capacités spécifiques (feature flags)
    supports_firecrawl: bool = True
    supports_dom_fallback: bool = True
    supports_scroll: bool = False
    supports_headless: bool = False
    supports_captcha_pause: bool = False
    
    # Métadonnées
    icon: str = "📰"


# ============================================================================
# 2. STATE MANAGER - Gestion du session state
# ============================================================================

class NewsSourceStateManager:
    """Gère le state Streamlit pour une source de manière générique"""
    
    def __init__(self, source_key: str):
        self.prefix = f"{source_key}_"
    
    def init_state(self):
        """Initialise tous les états nécessaires pour cette source"""
        defaults = {
            f"{self.prefix}rss_candidates": [],
            f"{self.prefix}show_json_state": False,
            f"{self.prefix}json_ready": False,
            f"{self.prefix}last_params": None,
        }
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def get(self, key: str, default=None):
        """Récupère une valeur du state"""
        return st.session_state.get(f"{self.prefix}{key}", default)
    
    def set(self, key: str, value):
        """Définit une valeur dans le state"""
        st.session_state[f"{self.prefix}{key}"] = value
    
    def clear_candidates(self):
        """Nettoie la liste des candidats et leurs checkboxes"""
        self.set("rss_candidates", [])
        # Supprimer toutes les checkboxes associées
        for key in list(st.session_state.keys()):
            if key.startswith(f"{self.prefix}rss_pick_"):
                st.session_state.pop(key, None)
    
    def clear_all(self):
        """Nettoie tout le state de cette source"""
        for key in list(st.session_state.keys()):
            if key.startswith(self.prefix):
                st.session_state.pop(key, None)
        self.init_state()


# ============================================================================
# 3. RENDERER - Composant UI réutilisable
# ============================================================================

class NewsSourceRenderer:
    """Rend l'interface Streamlit pour n'importe quelle source de news"""
    
    def __init__(self, config: NewsSourceConfig):
        self.config = config
        self.state = NewsSourceStateManager(config.key)
        self.job = config.job_factory()
        
    def render(self):
        """Rend l'interface complète de la source"""
        self.state.init_state()
        
        with st.expander(f"{self.config.icon} Job — {self.config.label}", expanded=False):
            # Header avec boutons d'action
            launch_clicked, clear_clicked = self._render_header()
            
            # Configuration temporelle
            params = self._render_temporal_config()
            
            # Settings avancés
            settings = self._render_advanced_settings()
            
            # Détection de changement de params
            self._handle_params_change(params)
            
            # Gestion des actions
            if launch_clicked:
                self._handle_launch(params, settings)
            if clear_clicked:
                self._handle_clear()
            
            # Liste des candidats avec checkboxes
            selected_urls = self._render_candidates_list()
            
            # Bouton de scraping
            self._handle_scraping_button(selected_urls, params, settings)
            
            # Monitoring du job
            self._render_job_monitoring()
            
            # Buffer preview + JSON
            self._render_buffer_and_json()
    
    def _render_header(self):
        """Rend les boutons d'action en haut"""
        col_open, col_launch, col_clear = st.columns([2, 1, 1])
        
        with col_open:
            st.link_button("🔗 Ouvrir l'URL", self.config.entry_url)
        with col_launch:
            launch = st.button("▶️ Lancer", use_container_width=True, 
                             key=f"{self.config.key}_launch")
        with col_clear:
            clear = st.button("🧹 Clear", use_container_width=True, 
                            key=f"{self.config.key}_clear")
        
        return launch, clear
    
    def _render_temporal_config(self) -> dict:
        """Rend la configuration temporelle"""
        with st.expander("Fenêtre temporelle", expanded=True):
            mode = st.radio(
                "Mode",
                options=["Aujourd'hui", "Dernières X heures"],
                horizontal=True,
                index=1,
                key=f"{self.config.key}_mode"
            )
            hours_window = st.slider(
                "Dernières X heures",
                min_value=1,
                max_value=24,
                value=self.config.default_hours,
                step=1,
                key=f"{self.config.key}_hours_window"
            )
        
        return {"mode": mode, "hours_window": hours_window}
    
    def _render_advanced_settings(self) -> dict:
        """Rend les settings avancés (s'adaptent aux capacités)"""
        settings = {}
        
        with st.expander("Settings", expanded=False):
            # Limites
            st.markdown("**Limites**")
            col1, col2 = st.columns(2)
            with col1:
                settings["max_total"] = st.number_input(
                    "Max articles total",
                    min_value=1,
                    max_value=1000,
                    value=self.config.default_max_total,
                    step=1,
                    key=f"{self.config.key}_max_total"
                )
            with col2:
                settings["max_per"] = st.number_input(
                    "Max articles par bulletin",
                    min_value=1,
                    max_value=1000,
                    value=self.config.default_max_per,
                    step=1,
                    key=f"{self.config.key}_max_per"
                )
            
            # Human behavior (si scroll supporté)
            if self.config.supports_scroll:
                st.markdown("**Human behavior**")
                col1, col2 = st.columns(2)
                with col1:
                    settings["scroll_min"] = st.number_input(
                        "Scroll min px", 100, 2000, 400, 50,
                        key=f"{self.config.key}_scroll_min"
                    )
                with col2:
                    settings["scroll_max"] = st.number_input(
                        "Scroll max px", 200, 4000, 1200, 50,
                        key=f"{self.config.key}_scroll_max"
                    )
                
                col1, col2 = st.columns(2)
                with col1:
                    settings["page_min"] = st.number_input(
                        "Temps min page (s)", 1, 120, 10,
                        key=f"{self.config.key}_page_min"
                    )
                with col2:
                    settings["page_max"] = st.number_input(
                        "Temps max page (s)", 2, 180, 45,
                        key=f"{self.config.key}_page_max"
                    )
            
            # Timing
            st.markdown("**Timing**")
            col1, col2 = st.columns(2)
            with col1:
                settings["wait_min"] = st.number_input(
                    "Wait min action (s)", 0.1, 5.0, 0.6, 0.1,
                    key=f"{self.config.key}_wait_min"
                )
            with col2:
                settings["wait_max"] = st.number_input(
                    "Wait max action (s)", 0.2, 8.0, 2.5, 0.1,
                    key=f"{self.config.key}_wait_max"
                )
            
            # Safety
            st.markdown("**Safety**")
            col1, col2 = st.columns(2)
            with col1:
                settings["max_errors"] = st.number_input(
                    "Max erreurs consécutives", 1, 10, 3,
                    key=f"{self.config.key}_max_errors"
                )
            with col2:
                settings["timeout"] = st.number_input(
                    "Timeout global (min)", 1, 60, 15,
                    key=f"{self.config.key}_timeout"
                )
            
            # Options booléennes
            settings["shuffle"] = st.checkbox(
                "Shuffle URLs", True, 
                key=f"{self.config.key}_shuffle"
            )
            settings["dry_run"] = st.checkbox(
                "DRY RUN", False, 
                key=f"{self.config.key}_dry_run"
            )
            settings["remove_buffer"] = st.checkbox(
                "Supprimer buffer après succès", True,
                key=f"{self.config.key}_remove_buffer"
            )
            
            # Captcha pause (si supporté)
            if self.config.supports_captcha_pause:
                settings["pause_captcha"] = st.checkbox(
                    "Pause en cas de captcha", True,
                    key=f"{self.config.key}_pause_captcha"
                )
            
            # Headless (si supporté)
            if self.config.supports_headless:
                settings["headless"] = st.checkbox(
                    "Headless (prod)", True,
                    key=f"{self.config.key}_headless"
                )
            
            # Sources
            st.markdown("**Sources**")
            settings["rss_feed"] = st.text_input(
                "RSS feed", 
                self.config.rss_feed_url,
                key=f"{self.config.key}_rss_feed"
            )
            settings["use_rss"] = st.checkbox(
                "Mode RSS", True, 
                key=f"{self.config.key}_use_rss"
            )
            
            if self.config.supports_firecrawl:
                settings["use_firecrawl"] = st.checkbox(
                    "Scraper via Firecrawl", True,
                    key=f"{self.config.key}_use_firecrawl"
                )
            
            settings["rss_ignore_time"] = st.checkbox(
                "Ignorer filtre temporel RSS", False,
                key=f"{self.config.key}_rss_ignore_time"
            )
            
            if self.config.supports_dom_fallback:
                settings["rss_dom_fallback"] = st.checkbox(
                    "Compléter via DOM", True,
                    key=f"{self.config.key}_rss_dom_fallback"
                )
        
        return settings
    
    def _handle_params_change(self, params: dict):
        """Détecte changement de params et clear les candidats"""
        current_params = (params["mode"], params["hours_window"])
        last_params = self.state.get("last_params")
        
        if last_params != current_params:
            self.state.clear_candidates()
            self.state.set("last_params", current_params)
    
    def _render_candidates_list(self) -> list:
        """Rend la liste des candidats avec checkboxes"""
        selected_urls = []
        candidates = self.state.get("rss_candidates", [])
        
        if not candidates:
            st.caption("Clique sur Lancer pour charger la liste.")
            return []
        
        # Boutons de gestion
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Clear liste", use_container_width=True, 
                        key=f"{self.config.key}_clear_list"):
                self.state.clear_candidates()
                st.rerun()
        with col2:
            if st.button("☐ Décocher tout", use_container_width=True,
                        key=f"{self.config.key}_uncheck_all"):
                for idx in range(len(candidates)):
                    st.session_state[f"{self.config.key}_rss_pick_{idx}"] = False
                st.rerun()
        
        # Liste des checkboxes
        st.caption("Sélectionne les articles à traiter :")
        for idx, item in enumerate(candidates):
            label = f"{item.get('title', '')}".strip() or item.get("url", "")
            key = f"{self.config.key}_rss_pick_{idx}"
            
            if key not in st.session_state:
                st.session_state[key] = True
            
            if st.checkbox(label, key=key):
                selected_urls.append(item)
        
        st.caption(f"{len(selected_urls)} article(s) sélectionné(s)")
        return selected_urls
    
    def _handle_scraping_button(self, selected_urls: list, params: dict, settings: dict):
        """Gère le bouton de scraping"""
        if not selected_urls:
            return
        
        if st.button("🧭 Scrapper les articles", use_container_width=True,
                    key=f"{self.config.key}_scrape"):
            if not selected_urls:
                st.error("Sélectionne au moins un article.")
                return
            
            # Reset job state
            self.job.set_buffer_text("")
            self.job.json_preview_text = ""
            self.job.json_items = []
            self.state.set("show_json_state", False)
            self.state.set("json_ready", False)
            
            # Build config dynamiquement
            config_params = {
                "entry_url": self.config.entry_url,
                "mode": "today" if params["mode"] == "Aujourd'hui" else "last_hours",
                "hours_window": int(params["hours_window"]),
                "max_articles_total": int(settings["max_total"]),
                "max_articles_per_bulletin": int(settings["max_per"]),
                "wait_min_action": float(settings["wait_min"]),
                "wait_max_action": float(settings["wait_max"]),
                "shuffle_urls": bool(settings["shuffle"]),
                "dry_run": bool(settings["dry_run"]),
                "max_consecutive_errors": int(settings["max_errors"]),
                "global_timeout_minutes": int(settings["timeout"]),
                "remove_buffer_after_success": bool(settings["remove_buffer"]),
                "use_rss": bool(settings["use_rss"]),
                "rss_feed_url": settings["rss_feed"],
                "rss_ignore_time_filter": bool(settings["rss_ignore_time"]),
                "urls_override": selected_urls,
            }
            
            # Paramètres conditionnels
            if self.config.supports_scroll:
                config_params["scroll_min_px"] = int(settings.get("scroll_min", 400))
                config_params["scroll_max_px"] = int(settings.get("scroll_max", 1200))
                config_params["min_page_time"] = int(settings.get("page_min", 10))
                config_params["max_page_time"] = int(settings.get("page_max", 45))
            
            if self.config.supports_headless:
                config_params["headless"] = bool(settings.get("headless", True))
            
            if self.config.supports_captcha_pause:
                config_params["pause_on_captcha"] = bool(settings.get("pause_captcha", True))
            
            if self.config.supports_firecrawl:
                config_params["use_firecrawl"] = bool(settings.get("use_firecrawl", True))
            
            if self.config.supports_dom_fallback:
                config_params["rss_use_dom_fallback"] = bool(settings.get("rss_dom_fallback", True))
            
            # Créer et lancer le job
            job_config = self.config.job_config_class(**config_params)
            self.job.start(job_config)
            st.success("Scraping lancé.")
    
    def _handle_launch(self, params: dict, settings: dict):
        """Gère le clic sur Lancer (charge les URLs)"""
        use_rss = settings.get("use_rss", True)
        
        if not use_rss:
            st.warning("Mode RSS désactivé.")
            return
        
        # Reset
        self.job.set_buffer_text("")
        self.job.json_preview_text = ""
        self.job.json_items = []
        self.state.set("show_json_state", False)
        self.state.set("json_ready", False)
        
        # Paramètres
        mode_str = "today" if params["mode"] == "Aujourd'hui" else "last_hours"
        hours = int(params["hours_window"])
        max_total = int(settings["max_total"])
        rss_feed = settings["rss_feed"]
        ignore_time = bool(settings["rss_ignore_time"])
        dom_fallback = bool(settings.get("rss_dom_fallback", True))
        use_firecrawl = bool(settings.get("use_firecrawl", True))
        
        # Fetch RSS
        from services.news_brewery.rss_utils import merge_article_items
        
        rss_items = self.config.fetch_rss_items(
            feed_url=rss_feed,
            max_items=max_total,
            mode=mode_str,
            hours_window=hours,
            ignore_time_filter=ignore_time,
        )
        
        # Fetch DOM (si fallback activé)
        if dom_fallback and self.config.supports_dom_fallback:
            dom_kwargs = {
                "page_url": self.config.entry_url,
                "max_items": max_total,
                "mode": mode_str,
                "hours_window": hours,
            }
            if self.config.supports_firecrawl:
                dom_kwargs["use_firecrawl_fallback"] = use_firecrawl
            
            dom_items = self.config.fetch_dom_items(**dom_kwargs)
            candidates = merge_article_items(dom_items, rss_items, max_total)
        else:
            candidates = rss_items
        
        self.state.set("rss_candidates", candidates)
        self.job.status_log.append("🔎 URLs chargées")
        
        if not candidates:
            st.warning("Aucune URL détectée.")
        
        st.rerun()
    
    def _handle_clear(self):
        """Gère le clic sur Clear"""
        self.job.clear()
        self.state.clear_all()
        st.success("Job réinitialisé.")
        st.rerun()
    
    def _render_job_monitoring(self):
        """Rend le monitoring du job en cours"""
        status = self.job.get_status()
        state = status.get("state", "idle")
        total = status.get("total", 0)
        processed = status.get("processed", 0)
        skipped = status.get("skipped", 0)
        started_at = status.get("started_at")
        last_log = status.get("last_log", "")
        
        st.divider()
        st.caption(f"État : {state}")
        
        if total > 0:
            progress = min(max((processed + skipped) / total, 0.0), 1.0)
            st.progress(progress)
            st.caption(f"Progression : {processed + skipped}/{total}")
        
        st.caption(f"Traités : {processed} · Ignorés : {skipped}")
        
        # ETA
        if started_at and (processed + skipped) > 0:
            elapsed = max(time.time() - float(started_at), 1.0)
            avg_per_item = elapsed / max(processed + skipped, 1)
            remaining = max(total - (processed + skipped), 0)
            eta_seconds = int(remaining * avg_per_item)
            st.caption(f"ETA : ~{eta_seconds // 60}m {eta_seconds % 60}s")
        
        if last_log:
            st.caption(f"Statut : {last_log}")
        
        # Erreurs
        if status.get("errors"):
            st.markdown("**Erreurs :**")
            for err in status.get("errors")[-3:]:
                st.write(f"⚠️ {err}")
        
        # Auto-refresh si en cours
        if state in ("running", "paused"):
            st.info("Job en cours — rafraîchissement automatique.")
            time.sleep(2)
            st.rerun()
    
    def _render_buffer_and_json(self):
        """Rend le buffer et le JSON"""
        status = self.job.get_status()
        
        # Buffer
        if status.get("buffer_text"):
            st.divider()
            st.markdown("**Preview concaténée (buffer)**")
            edited_buffer = st.text_area(
                label="",
                value=status.get("buffer_text", ""),
                height=320,
                key=f"{self.config.key}_buffer_editor"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Dédoublonner + JSON", use_container_width=True,
                           key=f"{self.config.key}_finalize"):
                    self.job.set_buffer_text(edited_buffer)
                    result = self.job.finalize_buffer()
                    if result.get("status") == "success":
                        st.success(f"{len(result.get('items', []))} items générés")
                        self.state.set("json_ready", True)
                        self.state.set("show_json_state", False)
                    else:
                        st.error(result.get("message", "Erreur JSON"))
            
            with col2:
                if st.button("🧹 Clear buffer", use_container_width=True,
                           key=f"{self.config.key}_clear_buffer"):
                    self.job.set_buffer_text("")
                    st.rerun()
        
        # Bouton pour afficher JSON
        if (self.state.get("json_ready", False) 
            and status.get("json_preview_text") 
            and not self.state.get("show_json_state", False)):
            if st.button("🧾 Afficher preview JSON", use_container_width=True,
                        key=f"{self.config.key}_show_json"):
                self.state.set("show_json_state", True)
                st.rerun()
        
        # JSON editor
        if status.get("json_preview_text") and self.state.get("show_json_state", False):
            st.markdown("**Preview JSON**")
            edited_json = st.text_area(
                label="",
                value=status.get("json_preview_text", ""),
                height=350,
                key=f"{self.config.key}_json_editor"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Envoyer en DB", use_container_width=True,
                           key=f"{self.config.key}_send_db"):
                    result = self.job.send_to_db()
                    if result.get("status") == "success":
                        st.success(f"{result.get('inserted', 0)} items insérés")
                    else:
                        st.error(result.get("message", "Erreur DB"))
            
            with col2:
                if st.button("🧹 Clear JSON", use_container_width=True,
                           key=f"{self.config.key}_clear_json"):
                    self.job.json_preview_text = ""
                    self.job.json_items = []
                    self.state.set("show_json_state", False)
                    self.state.set("json_ready", False)
                    st.rerun()
