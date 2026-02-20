## Specs techniques — Firecrawl batching + parallélisation (News Brewery + Mega Job Home)

### Contexte
Le projet scrape des URLs de sites d’actus, utilise **Firecrawl** pour extraire le contenu (markdown/html), puis passe dans un pipeline **LLM** (ex: `PROMPT_STRUCTURE`, JSONfy) avant insertion en base dans `brew_items`.

Deux chemins principaux existent :
- **News Brewery** (page `front/views/NewsBrewery.py`) : jobs par source (BFM, BeInCrypto, BourseDirect, Boursier…) + UI pour sélectionner des URLs puis lancer le scraping.
- **Mega Job Home** (page `app.py`, boutons “20h” et “6h”) : collecte multi-sources (`collect_mega_urls`) puis job `services/news_brewery/mega_job.py`.

Aujourd’hui :
- Les jobs “source” font Firecrawl **séquentiellement** (1 URL à la fois).
- Le Mega Job Home fait déjà une logique “batch” (taille 5) mais traite les URLs **séquentiellement à l’intérieur** du batch.

### Objectif
Réduire drastiquement le temps de scraping (ex: 200 URLs) en :
- **parallélisant** les appels Firecrawl (et optionnellement le prompt `STRUCTURE`) avec une **limite safe** (concurrency contrôlée),
- traitant en **batches** et en écrivant dans `brew_items` **batch par batch** (“au fil de l’eau”), pour éviter d’attendre la fin du run complet et améliorer la résilience.

### Non-objectifs (pour ce chantier)
- Changer la DA/UX du front (sauf ajouter une config “concurrency / batch size” si nécessaire).
- Refondre entièrement les prompts LLM (on garde les prompts existants).
- Changer le schéma Supabase (sauf ajout minimal optionnel si on veut une vraie idempotence côté DB).

---

## État actuel (audit technique)

### Firecrawl
Fichier : `services/hand_brewery/firecrawl_client.py`
- `fetch_url_text(url)` appelle `FirecrawlApp.scrape(url, formats=["markdown"])`.
- Aucune notion de retry/backoff, ni de pool, ni de timeout explicite côté Firecrawl (dépend SDK).

### Mega Job Home
Fichiers :
- `app.py` : déclenche `collect_mega_urls(mega_hours=6|20)` puis `mega_job.start_auto_scraping(urls)`.
- `services/news_brewery/mega_job.py` :
  - `BATCH_SIZE = 5`
  - boucle URL -> `fetch_url_text` (Firecrawl) -> `_run_text_prompt(PROMPT_STRUCTURE, raw_text)`
  - puis `finalize_buffer()` (JSONfy) + `send_to_db()` (insert dans `brew_items`) **à la fin de chaque batch**

Conclusion : **l’écriture DB batch par batch existe déjà** côté Mega Job, mais le scraping batch reste séquentiel.

### News Brewery (jobs sources)
Exemples (pattern identique) :
- `services/news_brewery/bfm_bourse_job.py`
- `services/news_brewery/beincrypto_job.py`
- `services/news_brewery/boursedirect_job.py`
- etc.

Pattern :
1. Collecte URLs (RSS/DOM).
2. Boucle séquentielle : Firecrawl -> Structure -> append buffer.
3. UI : ensuite “Générer JSON” + “Envoyer en DB”.

---

## Proposition : architecture cible

### Idée centrale
Introduire un **pipeline batch** avec une **worker pool** (threads) pour l’étape I/O (Firecrawl), et écrire en DB au fil de l’eau :

1) Découper les URLs en chunks : `batch_size` (ex: 10–25).
2) Pour un batch :
   - **Firecrawl en parallèle** (max `firecrawl_concurrency`).
   - (Optionnel) `PROMPT_STRUCTURE` en parallèle (max `llm_concurrency`), OU séquentiel si on veut limiter le risque 429.
   - Accumuler `structured` dans un buffer de batch.
   - JSONfy + secure JSON sur le buffer du batch.
   - **insert batch en DB** (déjà possible via `insert_raw_news(list)`).
3) Répéter jusqu’à épuisement des URLs.

### Pourquoi threads ?
Firecrawl + réseau = I/O-bound. Les `ThreadPoolExecutor` marchent très bien et sont déjà utilisés ailleurs dans le repo (carousels).

### Concurrence “safe”
On ne connaît pas les quotas Firecrawl exacts, donc l’implémentation doit être configurable et prudente :

Recommandation de démarrage :
- `firecrawl_concurrency = 3` (prod safe), puis monter à 5 si stable.
- `llm_concurrency = 2-3` (OpenAI) si on parallélise aussi `STRUCTURE`.

Avec :
- retry/backoff sur 429/5xx/timeouts,
- “circuit breaker” si trop d’erreurs consécutives.

---

## Détails d’implémentation (plan concret)

### 1) Améliorer Firecrawl client (robustesse)
Fichier : `services/hand_brewery/firecrawl_client.py`

Ajouter :
- **timeout** (si le SDK permet, sinon wrapper + `requests`/`httpx` au niveau API, ou timeout global par thread via future timeout).
- **retry/backoff** :
  - backoff exponentiel (ex: 2s, 4s, 8s) + jitter,
  - arrêter après `max_retries` (ex: 3).
- normaliser les erreurs (429/402 crédits/403).

Important : conserver la signature `fetch_url_text(url) -> str`.

### 2) Mega Job : paralléliser à l’intérieur des batches
Fichier : `services/news_brewery/mega_job.py`

Aujourd’hui :
- `BATCH_SIZE = 5` et boucle séquentielle dans chaque batch.

À faire :
- remplacer la boucle interne par :
  - `ThreadPoolExecutor(max_workers=firecrawl_concurrency)` pour Firecrawl,
  - mapping URL -> raw_text (ou error),
  - puis structure step (séquentiel ou pool séparé).

Points à respecter :
- **Progress** : `current_index`, logs, `processed/skipped` doivent rester cohérents (utiliser un lock pour les incréments si multi-thread).
- **Stop** : `self._stop_event.is_set()` doit interrompre le batch proprement (canceller les futures si possible, ou ignorer les résultats tardifs).

### 3) Mega Job : batch size configurable
Expose `BATCH_SIZE` via :
- un param dans `MegaJobConfig` (ex: `batch_size`, `firecrawl_concurrency`, `llm_concurrency`),
- ou via `st.secrets`/env (fallback constants).

### 4) News Brewery : option “auto pipeline batch + DB”
Actuellement, les jobs sources sont “buffer -> JSON -> DB” pilotés par l’UI.

Deux options :

**Option A (minimale, rapide, peu risquée)**  
Ajouter dans chaque job source un mode “auto batching” similaire à Mega Job :
- scrapper N URLs,
- par batch : JSONfy + insert DB,
- sans passer par l’édition manuelle buffer/JSON.

**Option B (meilleure architecture, plus longue)**  
Factoriser un “BatchScrapeEngine” réutilisable :
- input : liste d’URLs + source metadata + prompts,
- output : insert batch `brew_items`.
Les jobs sources deviennent de la config / orchestration.

### 5) Écriture DB “au fil de l’eau”
Déjà supporté par :
- `services/raw_storage/raw_news_service.py` :
  - `enrich_raw_items(...)` puis `insert_raw_news(items)` qui fait un insert de liste.

Recommandation :
- insérer par batch de 10–25 items pour limiter les payloads.
- en cas d’échec DB sur un batch : retry (1-2 fois) puis log + continuer (ou stopper selon config).

---

## Idempotence / anti-doublons (important si batching/parallélisation)
Problème : si le job est relancé ou si un batch échoue puis retry, on peut insérer des doublons.

Solutions (par ordre de coût) :
1) **Dedup in-memory** : garder un set des URLs déjà traitées dans le run. (déjà fait pour la collecte, pas pour l’insert)
2) **Dedup avant insert** : requêter `brew_items` sur `source_link in (...)` du batch. (coûteux mais simple)
3) **Contrainte unique DB** (recommandée si possible) : unique sur `(source_link)` ou `(source_type, source_link)` selon le besoin, puis insert “upsert”.  
   - Nécessite migration Supabase.
   - Code : utiliser upsert avec `on_conflict`.

---

## Observabilité / UX
À maintenir/améliorer :
- logs par batch : “batch x/y, ok/ko, inserted count”
- métriques : temps moyen Firecrawl / temps structure / taux d’erreur
- ETA plus fiable (basé sur throughput réel)

---

## Risques & limites
- Rate limits Firecrawl : trop de concurrence → erreurs, timeouts, coûts. D’où la limite configurable + backoff.
- Rate limits OpenAI : si on parallélise structure, risque 429. D’où `llm_concurrency` faible.
- Qualité JSONfy : gros batch → prompt trop long → JSONfy instable. D’où batch size modéré (10–25) et monitor d’erreurs.
- Progress counters non-thread-safe : besoin d’un lock si on incrémente depuis des threads.

---

## Paramètres recommandés (v1)
- `batch_size`: 10 (puis 20 si stable)
- `firecrawl_concurrency`: 3 (puis 5)
- `llm_concurrency`: 2 (si on parallélise structure), sinon séquentiel
- `firecrawl_max_retries`: 3
- `openai_max_retries`: déjà présent dans certains services ; homogénéiser si besoin

---

## Plan de livraison (phases)
1) **Mega Job Home** : paralléliser Firecrawl intra-batch + config batch/concurrency + logs/locks.
2) Mesurer stabilité/temps sur 6h/20h (ex: 200 URLs).
3) Appliquer la même mécanique aux jobs sources News Brewery (option A), ou factoriser (option B).
4) (Optionnel) Idempotence DB via unique constraint + upsert.

---

## Critères d’acceptation
- Sur ~200 URLs, temps total réduit significativement (objectif : -40% à -70% selon quotas).
- Le job continue même si certaines URLs échouent (résultat “partial” acceptable).
- Les items apparaissent dans `brew_items` **progressivement** par batch (pas uniquement à la fin).
- Pas d’explosion de 429/503 (ou gérée via backoff).

