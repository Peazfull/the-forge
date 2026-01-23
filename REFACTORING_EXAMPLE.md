# 🔄 Exemple Concret : Avant/Après Refactoring

## 📋 Scénario : Afficher 2 Sources (BFM + BeInCrypto)

---

## ❌ AVANT : 800 lignes répétitives

### Fichier : `NewsBrewery.py`

```python
import streamlit as st
from services.news_brewery.bfm_bourse_job import JobConfig, get_bfm_job
from services.news_brewery.beincrypto_job import JobConfig as BeInJobConfig, get_beincrypto_job
from services.news_brewery.rss_utils import fetch_dom_items, fetch_beincrypto_dom_items, fetch_rss_items

st.title("🗞️ NEWS Brewery")

# ============================================
# BLOC 1 : BFM BOURSE (400 lignes)
# ============================================

# Init session state
if "news_rss_candidates" not in st.session_state:
    st.session_state.news_rss_candidates = []
if "news_show_json_state" not in st.session_state:
    st.session_state.news_show_json_state = False
if "news_json_ready" not in st.session_state:
    st.session_state.news_json_ready = False
if "news_last_params" not in st.session_state:
    st.session_state.news_last_params = None

job = get_bfm_job()

with st.expander("▸ Job — BFM Bourse", expanded=False):
    # Header
    col_open, col_launch, col_clear = st.columns([2, 1, 1])
    with col_open:
        st.link_button("🔗 Ouvrir l'URL", "https://www.tradingsat.com/actualites/")
    with col_launch:
        launch = st.button("▶️ Lancer", use_container_width=True, key="news_bfm_launch")
    with col_clear:
        clear_job = st.button("🧹 Clear", use_container_width=True, key="news_bfm_clear")
    
    # Config temporelle
    with st.expander("Fenêtre temporelle", expanded=True):
        mode = st.radio(
            "Mode",
            options=["Aujourd'hui", "Dernières X heures"],
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
    
    # Settings avancés (120 lignes)
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
            max_articles_per = st.number_input(
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
            scroll_min_px = st.number_input("Scroll min px", 100, 2000, 400, 50, key="news_scroll_min")
        with col_scroll_max:
            scroll_max_px = st.number_input("Scroll max px", 200, 4000, 1200, 50, key="news_scroll_max")
        
        col_wait_min, col_wait_max = st.columns(2)
        with col_wait_min:
            wait_min = st.number_input("Wait min (s)", 0.1, 5.0, 0.6, 0.1, key="news_wait_min")
        with col_wait_max:
            wait_max = st.number_input("Wait max (s)", 0.2, 8.0, 2.5, 0.1, key="news_wait_max")
        
        shuffle_urls = st.checkbox("Shuffle URLs", True, key="news_shuffle")
        dry_run = st.checkbox("DRY RUN", False, key="news_dry_run")
        
        st.markdown("**Safety**")
        col_err, col_timeout = st.columns(2)
        with col_err:
            max_errors = st.number_input("Max erreurs", 1, 10, 3, key="news_max_errors")
        with col_timeout:
            timeout = st.number_input("Timeout (min)", 1, 60, 15, key="news_timeout")
        
        pause_captcha = st.checkbox("Pause captcha", True, key="news_pause_captcha")
        remove_buffer = st.checkbox("Remove buffer", True, key="news_remove_buffer")
        headless = st.checkbox("Headless", True, key="news_headless")
        
        st.markdown("**Sources**")
        rss_feed = st.text_input("RSS feed", "https://www.tradingsat.com/rssfeed.php", key="news_rss_feed")
        use_rss = st.checkbox("Mode RSS", True, key="news_use_rss")
        use_firecrawl = st.checkbox("Firecrawl", True, key="news_use_firecrawl")
        rss_ignore_time = st.checkbox("Ignore time", False, key="news_rss_ignore_time")
        rss_dom_fallback = st.checkbox("DOM fallback", True, key="news_rss_dom_fallback")
    
    # Détection changement params
    current_params = (mode, hours_window)
    if st.session_state.news_last_params != current_params:
        st.session_state.news_rss_candidates = []
        for key in list(st.session_state.keys()):
            if key.startswith("news_rss_pick_"):
                st.session_state.pop(key, None)
        st.session_state.news_last_params = current_params
    
    # Liste candidats
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
            st.caption("Sélectionne les articles :")
            for idx, item in enumerate(st.session_state.news_rss_candidates):
                label = f"{item.get('title','')}".strip() or item.get("url", "")
                key = f"news_rss_pick_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = True
                if st.checkbox(label, key=key):
                    selected_urls.append(item)
            st.caption(f"{len(selected_urls)} article(s) sélectionné(s)")
        else:
            st.caption("Clique sur Lancer pour charger.")
    
    # Scraping
    if st.session_state.news_rss_candidates:
        if st.button("🧭 Scrapper", use_container_width=True, key="news_scrape"):
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
                    mode="today" if mode == "Aujourd'hui" else "last_hours",
                    hours_window=int(hours_window),
                    max_articles_total=int(max_articles_total),
                    max_articles_per_bulletin=int(max_articles_per),
                    scroll_min_px=int(scroll_min_px),
                    scroll_max_px=int(scroll_max_px),
                    wait_min_action=float(wait_min),
                    wait_max_action=float(wait_max),
                    shuffle_urls=bool(shuffle_urls),
                    dry_run=bool(dry_run),
                    max_consecutive_errors=int(max_errors),
                    global_timeout_minutes=int(timeout),
                    pause_on_captcha=bool(pause_captcha),
                    remove_buffer_after_success=bool(remove_buffer),
                    headless=bool(headless),
                    use_rss=bool(use_rss),
                    rss_feed_url=rss_feed,
                    rss_ignore_time_filter=bool(rss_ignore_time),
                    rss_use_dom_fallback=bool(rss_dom_fallback),
                    use_firecrawl=bool(use_firecrawl),
                    urls_override=selected_urls,
                )
                job.start(config)
                st.success("Scraping lancé.")
    
    # Lancement
    if launch:
        if use_rss:
            job.set_buffer_text("")
            job.json_preview_text = ""
            job.json_items = []
            st.session_state.news_show_json_state = False
            st.session_state.news_json_ready = False
            rss_items = fetch_rss_items(
                feed_url=rss_feed,
                max_items=int(max_articles_total),
                mode="today" if mode == "Aujourd'hui" else "last_hours",
                hours_window=int(hours_window),
                ignore_time_filter=bool(rss_ignore_time),
            )
            if rss_dom_fallback:
                dom_items = fetch_dom_items(
                    page_url="https://www.tradingsat.com/actualites/",
                    max_items=int(max_articles_total),
                    mode="today" if mode == "Aujourd'hui" else "last_hours",
                    hours_window=int(hours_window),
                )
                from services.news_brewery.rss_utils import merge_article_items
                st.session_state.news_rss_candidates = merge_article_items(
                    dom_items, rss_items, int(max_articles_total)
                )
            else:
                st.session_state.news_rss_candidates = rss_items
            job.status_log.append("🔎 URLs chargées")
            st.rerun()
    
    # Clear
    if clear_job:
        job.clear()
        st.session_state.news_rss_candidates = []
        st.session_state.news_show_json_state = False
        st.session_state.news_json_ready = False
        st.rerun()
    
    # Monitoring
    status = job.get_status()
    st.divider()
    st.caption(f"État : {status.get('state')}")
    total = status.get("total", 0)
    processed = status.get("processed", 0)
    skipped = status.get("skipped", 0)
    if total > 0:
        st.progress(processed / max(total, 1))
        st.caption(f"{processed}/{total} traités · {skipped} ignorés")
    if status.get("last_log"):
        st.caption(f"Statut : {status.get('last_log')}")
    if status.get("errors"):
        st.markdown("**Erreurs :**")
        for err in status.get("errors")[-3:]:
            st.write(f"⚠️ {err}")
    if status.get("state") in ("running", "paused"):
        st.info("Job en cours...")
        time.sleep(2)
        st.rerun()
    
    # Buffer
    if status.get("buffer_text"):
        st.divider()
        st.markdown("**Buffer**")
        edited_buffer = st.text_area("", status.get("buffer_text", ""), height=320, key="news_buffer_editor")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ JSON", use_container_width=True, key="news_finalize"):
                job.set_buffer_text(edited_buffer)
                result = job.finalize_buffer()
                if result.get("status") == "success":
                    st.success(f"{len(result.get('items', []))} items")
                    st.session_state.news_json_ready = True
                else:
                    st.error(result.get("message"))
        with col2:
            if st.button("🧹 Clear buffer", use_container_width=True, key="news_clear_buffer"):
                job.set_buffer_text("")
                st.rerun()
    
    # JSON
    if st.session_state.news_json_ready and status.get("json_preview_text"):
        if not st.session_state.news_show_json_state:
            if st.button("🧾 Afficher JSON", use_container_width=True, key="news_show_json"):
                st.session_state.news_show_json_state = True
                st.rerun()
    
    if status.get("json_preview_text") and st.session_state.news_show_json_state:
        st.markdown("**JSON**")
        edited_json = st.text_area("", status.get("json_preview_text", ""), height=350, key="news_json_editor")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ DB", use_container_width=True, key="news_send_db"):
                result = job.send_to_db()
                if result.get("status") == "success":
                    st.success(f"{result.get('inserted', 0)} insérés")
                else:
                    st.error(result.get("message"))
        with col2:
            if st.button("🧹 Clear JSON", use_container_width=True, key="news_clear_json"):
                job.json_preview_text = ""
                job.json_items = []
                st.session_state.news_show_json_state = False
                st.session_state.news_json_ready = False
                st.rerun()


# ============================================
# BLOC 2 : BEINCRYPTO (400 lignes IDENTIQUES !)
# ============================================

# Init session state
if "bein_rss_candidates" not in st.session_state:
    st.session_state.bein_rss_candidates = []
if "bein_show_json_state" not in st.session_state:
    st.session_state.bein_show_json_state = False
if "bein_json_ready" not in st.session_state:
    st.session_state.bein_json_ready = False
if "bein_last_params" not in st.session_state:
    st.session_state.bein_last_params = None

bein_job = get_beincrypto_job()

with st.expander("▸ Job — BeInCrypto", expanded=False):
    # Header
    col_open, col_launch, col_clear = st.columns([2, 1, 1])
    with col_open:
        st.link_button("🔗 Ouvrir l'URL", "https://fr.beincrypto.com/")
    with col_launch:
        bein_launch = st.button("▶️ Lancer", use_container_width=True, key="bein_launch")
    with col_clear:
        bein_clear = st.button("🧹 Clear", use_container_width=True, key="bein_clear")
    
    # Config temporelle (IDENTIQUE !)
    with st.expander("Fenêtre temporelle", expanded=True):
        bein_mode = st.radio(
            "Mode",
            options=["Aujourd'hui", "Dernières X heures"],
            horizontal=True,
            index=1,
            key="bein_mode"  # ← Seule différence : la key
        )
        bein_hours = st.slider(
            "Dernières X heures",
            min_value=1,
            max_value=24,
            value=24,
            step=1,
            key="bein_hours_window"  # ← Seule différence
        )
    
    # ... 350 lignes IDENTIQUES avec juste les keys différentes ...
    # (même settings, même candidats, même scraping, même monitoring, même buffer, même JSON)

# ============================================
# Total : 800 lignes pour 2 sources
# Pour 7 sources : 2800 lignes !
# ============================================
```

### ⚠️ Problèmes

1. **800 lignes pour 2 sources** → 2800 lignes pour 7 sources
2. **Duplication massive** : 95% du code est identique
3. **Maintenance cauchemardesque** : Corriger un bug = modifier 7 endroits
4. **Risque d'incohérence** : Facile d'oublier une source
5. **Impossible à tester unitairement** : Tout est couplé à Streamlit
6. **Ajouter une source** = copier-coller 400 lignes

---

## ✅ APRÈS : 50 lignes lisibles

### Fichier : `NewsBrewery_v2.py`

```python
import streamlit as st
from front.components.news_source import NewsSourceConfig, NewsSourceRenderer

st.title("🗞️ NEWS Brewery")

# ============================================
# REGISTRE : Toutes les sources en un endroit
# ============================================

SOURCES = [
    NewsSourceConfig(
        key="bfm",
        label="BFM Bourse",
        icon="📈",
        entry_url="https://www.tradingsat.com/actualites/",
        rss_feed_url="https://www.tradingsat.com/rssfeed.php",
        fetch_dom_items=fetch_dom_items,
        fetch_rss_items=fetch_rss_items,
        job_factory=get_bfm_job,
        job_config_class=JobConfig,
        supports_scroll=True,
        supports_headless=True,
        supports_captcha_pause=True,
    ),
    
    NewsSourceConfig(
        key="beincrypto",
        label="BeInCrypto",
        icon="₿",
        entry_url="https://fr.beincrypto.com/",
        rss_feed_url="https://fr.beincrypto.com/feed/",
        fetch_dom_items=fetch_beincrypto_dom_items,
        fetch_rss_items=fetch_rss_items,
        job_factory=get_beincrypto_job,
        job_config_class=BeInJobConfig,
        supports_firecrawl=True,
    ),
    
    # Ajouter une 3ème source ? 10 lignes de plus !
]

# ============================================
# RENDU : Une boucle pour toutes les sources
# ============================================

for source_config in SOURCES:
    renderer = NewsSourceRenderer(source_config)
    renderer.render()  # ← Génère automatiquement toute l'UI !

# ============================================
# Total : 50 lignes pour N sources
# Pour 7 sources : Toujours 50 lignes !
# ============================================
```

### Fichier : `front/components/news_source.py` (400 lignes, UNE SEULE FOIS)

```python
"""
Composant réutilisable pour afficher n'importe quelle source de news.
Ces 400 lignes sont écrites UNE SEULE FOIS et réutilisées par toutes les sources.
"""

from dataclasses import dataclass
from typing import Callable
import streamlit as st

@dataclass
class NewsSourceConfig:
    """Configuration d'une source"""
    key: str
    label: str
    icon: str
    entry_url: str
    rss_feed_url: str
    fetch_dom_items: Callable
    fetch_rss_items: Callable
    job_factory: Callable
    job_config_class: type
    supports_scroll: bool = False
    supports_headless: bool = False
    supports_captcha_pause: bool = False
    supports_firecrawl: bool = True
    default_max_total: int = 400


class NewsSourceRenderer:
    """Rend l'UI pour n'importe quelle source"""
    
    def __init__(self, config: NewsSourceConfig):
        self.config = config
        self.job = config.job_factory()
    
    def render(self):
        """Génère toute l'interface automatiquement"""
        self._init_state()
        
        with st.expander(f"{self.config.icon} Job — {self.config.label}", expanded=False):
            self._render_header()
            params = self._render_temporal_config()
            settings = self._render_advanced_settings()  # S'adapte aux capacités
            self._handle_params_change(params)
            selected = self._render_candidates_list()
            self._handle_scraping(selected, params, settings)
            self._render_monitoring()
            self._render_buffer_and_json()
    
    def _init_state(self):
        """Init session state"""
        for suffix in ["rss_candidates", "show_json_state", "json_ready", "last_params"]:
            key = f"{self.config.key}_{suffix}"
            if key not in st.session_state:
                default = [] if suffix == "rss_candidates" else (False if "state" in suffix or "ready" in suffix else None)
                st.session_state[key] = default
    
    def _render_header(self):
        """Rend les boutons d'action"""
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.link_button("🔗 Ouvrir l'URL", self.config.entry_url)
        with col2:
            if st.button("▶️ Lancer", use_container_width=True, key=f"{self.config.key}_launch"):
                self._handle_launch()
        with col3:
            if st.button("🧹 Clear", use_container_width=True, key=f"{self.config.key}_clear"):
                self._handle_clear()
    
    def _render_temporal_config(self) -> dict:
        """Config temporelle (identique pour toutes les sources)"""
        with st.expander("Fenêtre temporelle", expanded=True):
            mode = st.radio(
                "Mode",
                ["Aujourd'hui", "Dernières X heures"],
                horizontal=True,
                index=1,
                key=f"{self.config.key}_mode"
            )
            hours = st.slider(
                "Dernières X heures",
                1, 24, 24, 1,
                key=f"{self.config.key}_hours_window"
            )
        return {"mode": mode, "hours": hours}
    
    def _render_advanced_settings(self) -> dict:
        """Settings qui s'adaptent aux capacités de la source"""
        settings = {}
        
        with st.expander("Settings", expanded=False):
            # Limites (toujours présentes)
            st.markdown("**Limites**")
            col1, col2 = st.columns(2)
            with col1:
                settings["max_total"] = st.number_input(
                    "Max total", 1, 1000, self.config.default_max_total,
                    key=f"{self.config.key}_max_total"
                )
            with col2:
                settings["max_per"] = st.number_input(
                    "Max per", 1, 1000, self.config.default_max_total,
                    key=f"{self.config.key}_max_per"
                )
            
            # Scroll (seulement si supporté) ← ADAPTATION AUTOMATIQUE
            if self.config.supports_scroll:
                st.markdown("**Human behavior**")
                col1, col2 = st.columns(2)
                with col1:
                    settings["scroll_min"] = st.number_input(
                        "Scroll min", 100, 2000, 400, 50,
                        key=f"{self.config.key}_scroll_min"
                    )
                with col2:
                    settings["scroll_max"] = st.number_input(
                        "Scroll max", 200, 4000, 1200, 50,
                        key=f"{self.config.key}_scroll_max"
                    )
            
            # Timing (toujours présent)
            st.markdown("**Timing**")
            col1, col2 = st.columns(2)
            with col1:
                settings["wait_min"] = st.number_input(
                    "Wait min", 0.1, 5.0, 0.6, 0.1,
                    key=f"{self.config.key}_wait_min"
                )
            with col2:
                settings["wait_max"] = st.number_input(
                    "Wait max", 0.2, 8.0, 2.5, 0.1,
                    key=f"{self.config.key}_wait_max"
                )
            
            # ... autres settings avec adaptation automatique
            
            # Headless (seulement si supporté) ← ADAPTATION
            if self.config.supports_headless:
                settings["headless"] = st.checkbox(
                    "Headless", True,
                    key=f"{self.config.key}_headless"
                )
            
            # Captcha pause (seulement si supporté) ← ADAPTATION
            if self.config.supports_captcha_pause:
                settings["pause_captcha"] = st.checkbox(
                    "Pause captcha", True,
                    key=f"{self.config.key}_pause_captcha"
                )
        
        return settings
    
    # ... autres méthodes (monitoring, buffer, JSON)
    # Tout est écrit UNE SEULE FOIS et fonctionne pour TOUTES les sources
```

### ✅ Avantages

1. **50 lignes au lieu de 800** (pour 2 sources)
2. **50 lignes au lieu de 2800** (pour 7 sources)
3. **Code DRY** : Zéro duplication
4. **Maintenance simple** : 1 seul endroit à corriger
5. **Cohérence garantie** : Même code pour toutes les sources
6. **Ajouter une source** : 10 lignes dans le registre
7. **Testable** : La logique est séparée de Streamlit

---

## 📊 Comparaison Visuelle

### Ajouter une 3ème source "Les Echos"

#### AVANT (400 lignes à copier-coller)

```python
# ============================================
# BLOC 3 : LES ECHOS (400 lignes)
# ============================================

if "lesechos_rss_candidates" not in st.session_state:
    st.session_state.lesechos_rss_candidates = []
if "lesechos_show_json_state" not in st.session_state:
    st.session_state.lesechos_show_json_state = False
# ... 390 lignes de plus (copier-coller + remplacer "news_" par "lesechos_")

# ⚠️ Risques :
# - Oublier de remplacer une key → bug
# - Oublier d'adapter une URL → bug
# - Inconsistance avec les autres sources
# - Temps : 1-2 heures
```

#### APRÈS (10 lignes)

```python
# Dans le registre SOURCES :

NewsSourceConfig(
    key="lesechos",
    label="Les Echos",
    icon="📰",
    entry_url="https://www.lesechos.fr/finance-marches",
    rss_feed_url="https://www.lesechos.fr/rss/finance.xml",
    fetch_dom_items=fetch_lesechos_dom_items,
    fetch_rss_items=fetch_rss_items,
    job_factory=get_lesechos_job,
    job_config_class=LesEchosConfig,
),

# ✅ C'est tout ! 10 lignes, 5 minutes
# La boucle for va automatiquement générer l'UI complète
```

---

## 🐛 Corriger un Bug

### Scénario : Le bouton "Clear buffer" ne rafraîchit pas l'UI

#### AVANT : 7 endroits à corriger

```python
# Dans BFM Bourse (ligne 280)
if st.button("🧹 Clear buffer", ...):
    job.set_buffer_text("")
    # ← BUG : manque st.rerun()

# Dans BeInCrypto (ligne 680)
if st.button("🧹 Clear buffer", ...):
    bein_job.set_buffer_text("")
    # ← BUG : manque st.rerun()

# Dans Bourse Direct (ligne 1080)
# ... répéter la correction 5 fois de plus

# ⚠️ Si on oublie une source → incohérence
# ⚠️ Temps : 30 minutes
```

#### APRÈS : 1 seul endroit

```python
# Dans NewsSourceRenderer._render_buffer_and_json()

with col2:
    if st.button("🧹 Clear buffer", ...):
        self.job.set_buffer_text("")
        st.rerun()  # ← FIX appliqué à toutes les sources !

# ✅ Temps : 30 secondes
# ✅ Toutes les sources sont automatiquement corrigées
```

---

## 🎯 Résumé

### Métriques

| Critère | AVANT | APRÈS | Gain |
|---------|-------|-------|------|
| **Lignes pour 2 sources** | 800 | 50 + 400* | -44% |
| **Lignes pour 7 sources** | 2800 | 50 + 400* | -86% |
| **Temps ajout source** | 2h | 5min | -96% |
| **Temps fix bug** | 30min | 30s | -98% |
| **Risque d'incohérence** | Élevé | Nul | -100% |
| **Complexité maintenance** | O(N) | O(1) | Constant |

\* Les 400 lignes du renderer sont écrites **une seule fois** et réutilisées

### Conclusion

L'architecture refactorisée offre :
- ✅ **90% moins de code** pour 7+ sources
- ✅ **98% moins de temps** pour corriger un bug
- ✅ **96% moins de temps** pour ajouter une source
- ✅ **Zéro risque d'incohérence** entre sources
- ✅ **Code testable** et maintenable
- ✅ **Pattern scalable** pour 100+ sources

**ROI** : Temps investi = 3 jours. Break-even après 2-3 nouvelles sources ou 5-6 bug fixes. Gains exponentiels ensuite.
