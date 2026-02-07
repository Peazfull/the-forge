# 🔧 Corrections Carrousel Eco - Génération Article par Article

## 📋 Résumé des problèmes corrigés

### ✅ **Problème #1 : Cover traitée en double**
**Avant :** La cover était ajoutée à la queue comme un item spécial `{is_cover: True}`, ce qui créait un traitement en double de l'item 1.

**Après :** La cover (position 0) est créée AVANT la queue, via `upsert_carousel_eco_cover()`. Elle est ensuite traitée NORMALEMENT dans la queue avec tous les autres items.

**Résultat :** Chaque item est traité 1 seule fois, pas de doublon.

---

### ✅ **Problème #2 : Mélange des images (caches non nettoyés)**
**Avant :** Les caches `session_state` (carousel_images, carousel_image_models, slide_previews) n'étaient jamais vidés entre les générations.

**Après :** Nettoyage complet de tous les caches dans :
- `send_to_carousel()` → avant démarrage
- `_finalize_generation()` → après fin

**Résultat :** Pas de confusion entre les anciennes et nouvelles générations.

---

### ✅ **Problème #3 : Boucle infinie sur erreur**
**Avant :** Si un item échouait, il était remis en queue indéfiniment via `generation_inflight_item`.

**Après :** 
- Suppression du système `generation_inflight_item` (trop complexe)
- Ajout d'un compteur d'erreurs par item : `generation_error_count[item_id]`
- Si 3 échecs consécutifs → item skip automatiquement

**Résultat :** Plus de boucle infinie, génération continue même si un item échoue.

---

### ✅ **Problème #4 : Verrou non libéré en cas d'erreur**
**Avant :** Si `insert_items_to_carousel_eco()` échouait, les verrous restaient activés → interface bloquée.

**Après :** Ajout d'un `try/except` global dans `send_to_carousel()` qui libère les verrous en cas d'erreur critique.

**Résultat :** Plus besoin de cliquer sur "🔓 Débloquer" manuellement.

---

### ✅ **Problème #5 : Logique simplifiée**
**Avant :** Logique complexe avec `is_cover`, `source_item`, `inflight_item`, etc.

**Après :** 
- Cover créée AVANT la queue (simple upsert)
- Queue contient TOUS les items (cover + items normaux)
- Chaque item est traité selon sa position (0 = cover, 1-N = items)

**Résultat :** Code plus simple, plus lisible, plus maintenable.

---

## 🔄 Workflow Corrigé

### **Étape 1 : Sélection**
L'utilisateur sélectionne 1 à 10 articles dans le Bulletin Eco.

### **Étape 2 : Insertion en DB**
`insert_items_to_carousel_eco()` insère les items avec positions 1-N.

### **Étape 3 : Création de la cover**
`upsert_carousel_eco_cover()` crée la cover (position 0) basée sur l'item 1.

### **Étape 4 : Nettoyage**
- Slides storage nettoyées
- Caches session_state vidés

### **Étape 5 : Génération séquentielle**
La queue contient TOUS les items (cover + items) :
- **Cover (position 0)** : génération prompt image + image (pas de textes)
- **Items (positions 1-N)** : génération textes + prompts + image

Chaque item est traité 1 par 1, avec 1 `st.rerun()` entre chaque.

### **Étape 6 : Finalisation**
- Caption Instagram générée automatiquement
- Verrous libérés
- Caches nettoyés
- Interface prête pour la preview

---

## 📊 Structure de la Queue

```
Queue = [
  {position: 0, ...},  # Cover (image seulement)
  {position: 1, ...},  # Item 1 (textes + image)
  {position: 2, ...},  # Item 2 (textes + image)
  ...
  {position: N, ...}   # Item N (textes + image)
]
```

**Traitement :**
- Run 1 : Cover (position 0) → génère image → `st.rerun()`
- Run 2 : Item 1 (position 1) → génère textes + image → `st.rerun()`
- Run 3 : Item 2 (position 2) → génère textes + image → `st.rerun()`
- ...
- Run N+1 : Fin → `_finalize_generation()`

---

## 🎯 Points clés

1. **Cover = position 0** (juste une image, pas de textes)
2. **Items = positions 1-N** (textes + image)
3. **1 item traité par run** (évite timeout Streamlit)
4. **Skip après 3 échecs** (évite boucle infinie)
5. **Caches nettoyés** avant et après génération
6. **Verrous sécurisés** avec try/except global

---

## ✅ Tests à faire

1. ✅ Sélectionner 5 articles → vérifier que 6 items sont créés (1 cover + 5 items)
2. ✅ Vérifier que la cover (position 0) n'a pas de `title_carou` / `content_carou`
3. ✅ Vérifier que les items 1-5 ont bien leurs textes générés
4. ✅ Relancer une génération avec d'autres articles → vérifier qu'il n'y a pas de mélange
5. ✅ Provoquer une erreur (API key invalide) → vérifier que l'interface ne bloque pas
6. ✅ Vérifier que les logs debug affichent correctement le progrès

---

## 🚀 Prochaines améliorations possibles

- Ajouter un bouton "⏸️ Pause" pour arrêter la génération en cours
- Afficher une progress bar visuelle (X/N items traités)
- Permettre de modifier l'ordre des items après génération
- Ajouter un système de "retry" manuel pour les items échoués

---

**Date :** 2026-02-07  
**Fichier modifié :** `front/views/CarrouselEco.py`  
**Lignes modifiées :** ~150 lignes (fonctions `send_to_carousel()`, `process_generation_queue()`, `_finalize_generation()`)
