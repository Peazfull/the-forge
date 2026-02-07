# 🔧 Corrections Appliquées - Carrousel Bourse

## 📅 Date
7 février 2026

## 🎯 Objectif
Corriger les bugs de génération identiques à ceux de Carrousel Eco et renforcer la qualité des images générées (style "photo de presse").

---

## 🐛 Bugs Identifiés et Corrigés

### 1. **Mélange d'images (Storage Overwriting)**
**Problème :** Les images générées écrasaient les anciennes dans Supabase Storage si elles avaient la même position (ex: `imgcaroubourse1.png`).

**Solution :**
- Ajout de `clear_image_files()` et `list_image_files()` dans `carousel_image_service.py`
- Nettoyage complet des 2 buckets au début de chaque génération :
  - `carousel-bourse` (images générées)
  - `carousel-bourse-slides` (slides finales)
- Reset des caches `session_state` : `carousel_images`, `carousel_image_models`, `slide_previews`

### 2. **Cover (position 0) Traitée en Double**
**Problème :** L'item `items[0]` était utilisé pour créer une `cover_task` ET inclus dans la queue principale, causant un double traitement.

**Solution :**
- La cover est maintenant générée **SYNCHRONE** dans `send_to_carousel()`, **AVANT** l'initialisation de la queue
- La queue ne contient que les items de contenu (positions 1-N)
- Code clairement séparé avec marqueur `━━━ GÉNÉRATION COVER (position 0) - SYNCHRONE ━━━`

### 3. **Boucle Infinie sur Erreur**
**Problème :** Si un item échouait, le système `generation_inflight_item` le remettait infiniment en queue sans limite.

**Solution :**
- **Suppression complète** de la logique `generation_inflight_item`
- Ajout d'un compteur d'erreurs par item : `st.session_state.generation_error_count`
- Si un item échoue 3 fois consécutives, il est **ignoré** (skip)
- Message de log : `⏭️ Item #{position} ignoré (3 échecs)`

### 4. **Verrou Non Libéré sur Erreur Critique**
**Problème :** Si une erreur survenait avant l'initialisation de la queue, le verrou `generation_in_progress` restait bloqué.

**Solution :**
- Ajout d'un **`try-except` global** autour de toute la fonction `send_to_carousel()`
- Dans le `except`, reset forcé des verrous :
  ```python
  st.session_state.generation_in_progress = False
  st.session_state.generation_active = False
  ```
- Log d'erreur critique avec message tronqué (200 caractères max)

### 5. **Positions Incorrectes (Logique Cover/Items)**
**Problème :** La logique de positions était ambiguë avec le `cover_task` ajouté en début de queue.

**Solution :**
- Cover : position `0`, générée de manière synchrone, **AVANT** la queue
- Items : positions `1-N`, queue normale
- Hiérarchie claire et prévisible

### 6. **Nettoyage Incomplet du Cache**
**Problème :** Seul le bucket `carousel-bourse-slides` était nettoyé, pas `carousel-bourse`.

**Solution :**
- Nettoyage des **2 buckets** au début de `send_to_carousel()`
- Fonctions créées dans `carousel_image_service.py` :
  - `list_image_files()` : liste les fichiers du bucket `carousel-bourse`
  - `clear_image_files()` : supprime tous les fichiers du bucket `carousel-bourse`

### 7. **Session State Non Nettoyé Entre Générations**
**Problème :** Les variables `carousel_images` et `carousel_image_models` persistaient entre les générations.

**Solution :**
- Ajout du reset explicite dans `_finalize_generation()` :
  ```python
  st.session_state.carousel_images = {}
  st.session_state.carousel_image_models = {}
  st.session_state.slide_previews = {}
  st.session_state.generation_error_count = {}
  if "generation_inflight_item" in st.session_state:
      del st.session_state.generation_inflight_item
  ```

### 8. **Bouton "Débloquer" Affiché Pendant Génération Active**
**Problème :** Le bouton `🔓 Débloquer` apparaissait même quand la génération tournait normalement.

**Solution :**
- Condition stricte pour afficher le bouton :
  ```python
  if st.session_state.get("generation_in_progress", False) and not st.session_state.get("generation_active", False):
  ```
- Le bouton n'apparaît **QUE** si `generation_in_progress=True` ET `generation_active=False` (état vraiment bloqué)

---

## 🎨 Renforcement des Prompts Images

### Objectif
Éliminer les éléments graphiques non réalistes (charts, dashboards, écrans avec données) et garantir un style **"photo de presse réelle"**.

### Modifications dans les 3 Prompts

Fichiers modifiés :
- `prompts/carousel/bourse/generate_image_prompts.py` (style "sunset")
- `prompts/carousel/bourse/generate_image_prompts_variant.py` (style "studio")
- `prompts/carousel/bourse/generate_image_prompts_manual.py` (avec instructions manuelles)

### Ajouts Critiques

#### 1. Section "INTERDICTIONS CRITIQUES ⛔"
```
🚫 AUCUN écran affichant des graphiques, données, charts
🚫 AUCUN graphique de trading, courbe boursière, infographie
🚫 AUCUN dashboard, tableau de bord, visualisation de données
🚫 AUCUN élément CGI, illustration, dessin, style artistique
🚫 AUCUN texte visible (titres, labels, légendes)
🚫 AUCUN watermark, logo média, overlay

→ L'image doit montrer UNIQUEMENT des éléments physiques et réels du monde réel
```

#### 2. Renforcement "PHOTO DE PRESSE RÉELLE"
- Ajout explicite : `PRESS PHOTOGRAPH (PHOTO DE PRESSE RÉELLE)`
- Ajout : `IMITATION PHOTO DE PRESSE`
- Logos : `authentique et RÉEL, intégré naturellement dans un contexte photographique réaliste`
- Personnalités : `UNIQUEMENT si elle est le CŒUR de l'actualité` + `Style PHOTO DE PRESSE RÉELLE`

#### 3. NEGATIVE PROMPTS Obligatoires
Ajout d'instructions explicites pour GPT-4o-mini d'inclure ces negative prompts dans le prompt final généré :
```
- NO SCREENS showing data/graphics (no digital displays with charts or visualizations)
- NO CHARTS, NO INFOGRAPHICS, NO DASHBOARDS (no bar graphs, line graphs, or statistical displays)
- The image must show ONLY physical, real-world elements
- NO digital screens displaying charts or data visualizations.
- NO bar graphs, line graphs, or statistical displays.
- The image must show ONLY physical, real-world elements photographed in a press context.
```

#### 4. Exemple Enrichi
Ajout d'une section "NEGATIVE PROMPTS (CRITICAL)" dans l'exemple de référence pour montrer à GPT-4o-mini comment intégrer ces interdictions.

---

## ✅ Workflow Après Correction

### Phase 1 : Initialisation (`send_to_carousel()`)
1. ✅ Vérification verrou (éviter double exécution)
2. ✅ Insertion des items en DB
3. ✅ Récupération des items depuis DB
4. ✅ **Nettoyage complet** des 2 buckets (`carousel-bourse` + `carousel-bourse-slides`)
5. ✅ **Reset des caches** `session_state`
6. ✅ **Génération SYNCHRONE de la cover** (position 0) :
   - Upsert cover en DB
   - Génération prompt image (type "sunset")
   - Génération image
   - Sauvegarde en storage
7. ✅ Initialisation de la queue **SANS** la cover (seulement items 1-N)
8. ✅ Activation des verrous (`generation_in_progress`, `generation_active`)

### Phase 2 : Traitement Queue (`process_generation_queue()`)
Pour chaque item (position 1-N) :
1. ✅ Vérification compteur d'erreurs (max 3)
2. ✅ Génération textes (titre + contenu carousel)
3. ✅ Génération prompts images (sunset + studio) avec **renforcements "press photo"**
4. ✅ Sauvegarde en DB
5. ✅ Génération image (Gemini 3 Pro / fallback GPT Image 1.5) avec **negative prompts renforcés**
6. ✅ En cas d'erreur :
   - Incrément du compteur d'erreurs pour cet item
   - Si < 3 erreurs : remise en queue
   - Si ≥ 3 erreurs : skip définitif
7. ✅ `st.rerun()` pour traiter l'item suivant

### Phase 3 : Finalisation (`_finalize_generation()`)
1. ✅ Reset `bourse_selected_items`
2. ✅ **Reset complet des caches** (`carousel_images`, `carousel_image_models`, `slide_previews`, `generation_error_count`, `generation_inflight_item`)
3. ✅ Libération des verrous
4. ✅ Génération automatique de la caption Instagram
5. ✅ Rerun final

---

## 📊 Résultats Attendus

### Stabilité
- ✅ Pas de boucle infinie
- ✅ Pas de verrou bloqué
- ✅ Gestion d'erreurs robuste (max 3 tentatives)
- ✅ Affichage correct du bouton "Débloquer" uniquement en cas de blocage réel

### Qualité des Images
- ✅ Pas de mélange d'images anciennes/nouvelles
- ✅ Pas de cover en double
- ✅ **Style "photo de presse" respecté**
- ✅ **Aucun graphique, chart ou dashboard dans les images**
- ✅ Logos authentiques et réels
- ✅ Personnalités uniquement si centrales à l'actualité

### UX
- ✅ "Click and forget" : l'utilisateur lance et peut attendre sans interaction
- ✅ Logs clairs et détaillés pour le debug
- ✅ Gestion automatique de la caption Instagram

---

## 🔗 Fichiers Modifiés

### Frontend
- ✅ `front/views/CarrouselBourse.py`
  - Fonction `send_to_carousel()` : try-except global, cover synchrone, nettoyage buckets
  - Fonction `process_generation_queue()` : suppression inflight_item, compteur d'erreurs
  - Fonction `_finalize_generation()` : reset caches complets
  - Bouton "Débloquer" : condition stricte

### Services
- ✅ `services/carousel/bourse/carousel_image_service.py`
  - Ajout `list_image_files()`
  - Ajout `clear_image_files()`

### Prompts
- ✅ `prompts/carousel/bourse/generate_image_prompts.py`
- ✅ `prompts/carousel/bourse/generate_image_prompts_variant.py`
- ✅ `prompts/carousel/bourse/generate_image_prompts_manual.py`
  - Section "INTERDICTIONS CRITIQUES ⛔"
  - Renforcement "PHOTO DE PRESSE RÉELLE"
  - NEGATIVE PROMPTS obligatoires
  - Exemple enrichi

---

## 🚀 Prochaines Étapes

1. Tester une génération complète sur Carrousel Bourse
2. Vérifier la qualité des images (absence de graphiques/charts)
3. Confirmer la stabilité du workflow (pas de boucle infinie)

---

**Status : ✅ Toutes les corrections appliquées**
