# AI_CONTEXT — The Forge

Ce fichier sert de **contexte minimal** à fournir à une IA quand elle n’a pas l’historique du projet.
Objectif: permettre de contribuer vite (bugfix / feature) sans “tourisme” dans le repo.

## TL;DR (pitch)
**The Forge** est une app **Streamlit** qui orchestre des pipelines de **collecte/curation** (news, newsletters, marché), stocke des items dans **Supabase**, puis exécute une chaîne **enrichissement → scoring → génération de contenus** (carrousels, stories, breaking, doss) incluant **génération d’images**.

## Démarrage (local)
- **Entrypoint Streamlit**: `app.py` (à la racine).
- **Commande recommandée**:

```bash
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

- **Note**: `run.sh` bascule dans `front/` puis lance `streamlit run app.py`. Or `front/app.py` n’existe pas (structure actuelle). Si tu utilises `run.sh`, il est probablement à mettre à jour.

## Dépendances & services externes
- **Supabase**: DB principale (tables ci-dessous). Client dans `db/supabase_client.py` et aussi `services/raw_storage/raw_news_service.py`.
- **LLM texte**: OpenAI (souvent `gpt-4o-mini`) pour structuration / JSON / captions / rewriting.
- **Scraping**: Firecrawl (utilisé par la “brewery” pour transformer des URLs en texte).
- **Données de marché**: Yahoo Finance via `yfinance`.
- **Images**:
  - Gemini Image (`gemini-3-pro-image-preview`) via API Google Generative Language (HTTP) et/ou via Vertex (SDK `google-genai`).
  - Fallback OpenAI image: `gpt-image-1.5`.

## Secrets (ne jamais committer)
Les clés sont lues via `st.secrets` (ex: `.streamlit/secrets.toml` en local / secrets Streamlit Cloud).
Clés attendues (au minimum selon les flows):
- **Supabase**: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- **OpenAI**: `OPENAI_API_KEY`
- **Firecrawl**: `FIRECRAWL_API_KEY` (sinon env var `FIRECRAWL_API_KEY`)
- **Gemini API (HTTP)**: `GEMINI_API_KEY`
- **Vertex AI (SDK)**: `GCP_PROJECT_ID`, `VERTEX_AI_LOCATION` (+ parfois `gcp_service_account` en prod Streamlit)

⚠️ Le repo contient un `vertex-ai-key.json` (credential). À traiter comme **secret** (idéalement non versionné).

## Carte du repo (où regarder en premier)
- **UI Streamlit / router**
  - `app.py`: home, stats, control panel, preview/édition, routeur dynamique vers `front/views/*`.
  - `front/layout/sidebar.py`: menu latéral (définit la navigation).
  - `front/views/*.py`: pages (NewsBrewery, NlBrewery, Market, Carrousels, Stories…).
- **Prompts**
  - `prompts/**`: prompts “métier” (caption, textes, image prompts, rewrite…). Exemple: `prompts/doss/generate_doss_caption.py`.
- **Services (logique métier)**
  - `services/news_brewery/**`: sources + jobs, inclut `mega_job.py` (pipeline multi-sources).
  - `services/nl_brewery/**`: IMAP/Gmail + processing newsletters.
  - `services/raw_storage/**`: insertion/lecture des items en DB (table `brew_items`).
  - `services/enrichment/**`: enrichissement (tags/labels/entities/metadata) sur `brew_items`.
  - `services/scoring/**`: scoring + update score sur `brew_items`.
  - `services/marketbrewery/**`: ingestion marché + métriques + écriture en DB.
  - `services/carousel/**`: génération carrousels (textes, captions, images) + écriture en DB (tables `carousel_*`).

## Tables Supabase (observées dans le code)
### Contenu (pipeline editorial)
- **`brew_items`**: table centrale des items (news/newsletters/etc.). Colonnes utilisées dans le code: `id`, `title`, `content`, `tags`, `labels`, `entities`, `zone`, `score_global`, `processed_at`, `flow`, `source_type`, `source_name`, `source_link`, `source_date`, `status`, `batch_date`.
- **`nl_recipients`**: liste d’adresses newsletters (filtre de traitement IMAP).

### Marché (marketbrewery)
- **`assets`**
- **`market_daily_open`**
- **`market_daily_close`**
- **`market_daily_close_daily`**
- **`market_weekly_close`**
- **`market_top_flop`**

### Artist / Carrousels
- **`carousel_eco`**
- **`carousel_bourse`**
- **`carousel_pea`**
- **`carousel_crypto`**

## Pipelines (vue fonctionnelle)
### 1) News Brewery → items en DB
Point d’entrée UI: `front/views/NewsBrewery.py`.
- Collecte d’URLs depuis un registre de sources (`services/news_brewery/sources_registry.py`).
- “Mega Job” (`services/news_brewery/mega_job.py`):
  - Scrape URL → texte (Firecrawl).
  - LLM: **structure** du texte, puis **jsonfy** (et sécurisation JSON).
  - Enrichissement technique + insertion DB via `services/raw_storage/raw_news_service.py` dans `brew_items`.

### 2) NL Brewery (newsletters) → items en DB
Point d’entrée UI: `front/views/NlBrewery.py`.
- IMAP/Gmail: récupère les emails et filtre selon `nl_recipients`.
- Pipeline: clean → structure → JSON → insertion dans `brew_items` avec métadonnées `flow="nl_brewery"`, `source_type="newsletter"`.

### 3) The Ministry (enrich + score) → enrichit `brew_items`
Point d’entrée UI: Home (bouton “Ministry”) + pages:
- `front/views/EnrichBrewery.py` + `services/enrichment/*`
- `front/views/ScoreBrewery.py` + `services/scoring/*`
But: remplir tags/labels/entities/score_global et permettre une **édition manuelle** du score depuis la home.

### 4) The Artist (carrousels / stories / breaking / doss)
Points d’entrée UI: `front/views/Carrousel*.py`, `front/views/Breaking.py`, `front/views/Stories.py`, `front/views/CarrouselDoss.py`.
- Sélectionne des items (souvent depuis `brew_items`) et matérialise un “set” dans `carousel_*`.
- Génère:
  - **textes** (slides),
  - **captions** (Instagram/LinkedIn selon modules),
  - **prompts d’images**,
  - **images** via `services/carousel/image_generation_service.py` (Gemini → fallback OpenAI).

## Conventions / règles utiles pour contribuer
- **Prompts**: chaque format a ses prompts dans `prompts/<module>/…`. Respecter strictement les contraintes de format (souvent “no markdown”, CTA exact, etc.).
- **DB**: `brew_items` est la source de vérité editorial. Les tables `carousel_*` sont des “vues matérialisées” pour la prod graphique.
- **Streamlit**: beaucoup d’état est dans `st.session_state`; éviter les mutations implicites non contrôlées.
- **Parallélisme**: `MegaJob` utilise threads (Firecrawl + structuration). Attention aux clients non thread-safe (il y a déjà un client OpenAI thread-local dans `mega_job.py`).

## “Sharp edges” (à connaître)
- Le routeur dans `app.py` charge des pages via `exec(...)` à partir d’un chemin construit à la volée: les chemins et imports doivent rester cohérents.
- `run.sh` semble décalé vs l’organisation actuelle (voir section démarrage).
- Éviter tout changement qui imprime/affiche des secrets; ne pas versionner de clés.

