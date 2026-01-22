import streamlit as st
from services.enrichment.enrichment_service import (
    enrich_items_batch,
    get_enrichment_stats,
    fetch_items_to_enrich
)
from db.supabase_client import get_supabase
import time


# ======================================================
# HEADER
# ======================================================

st.title("🏛️ The Ministry — Enrich Metadata")
st.markdown("**Enrichissement automatique des métadonnées** (tag, label, entities, zone, country)")
st.divider()


# ======================================================
# SECTION 1 : LANCER L'ENRICHISSEMENT
# ======================================================

st.subheader("🚀 Lancer l'enrichissement")

col_button, col_limit = st.columns([3, 1])

with col_limit:
    limit_option = st.selectbox(
        "Limite",
        options=[10, 50, 100, 500, "Tous"],
        index=0
    )
    
    if limit_option == "Tous":
        limit_value = None
    else:
        limit_value = int(limit_option)

with col_button:
    # Compter les items non enrichis
    items_to_enrich = fetch_items_to_enrich(limit=limit_value)
    items_count = len(items_to_enrich)
    
    if items_count == 0:
        st.info("✅ Tous les items sont déjà enrichis !")
    else:
        st.info(f"📊 {items_count} items à enrichir")

if items_count > 0:
    if st.button("🚀 Lancer l'enrichissement", type="primary", use_container_width=True):
        
        # Progress bar container
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            progress_text = st.empty()
        
        with status_container:
            status_text = st.empty()
        
        # Lancer l'enrichissement
        start_time = time.time()
        
        # Simuler le traitement item par item pour afficher la progression
        items = fetch_items_to_enrich(limit=limit_value)
        total = len(items)
        success_count = 0
        error_count = 0
        
        from services.enrichment.enrichment_service import enrich_single_item
        
        for idx, item in enumerate(items, start=1):
            item_id = item.get("id")
            title = item.get("title", "")
            content = item.get("content", "")
            
            # Afficher la progression
            progress = idx / total
            progress_bar.progress(progress)
            progress_text.markdown(f"**Traitement : {idx}/{total} items** ({int(progress*100)}%)")
            status_text.text(f"Item en cours : {title[:50]}...")
            
            # Enrichir l'item
            result = enrich_single_item(item_id, title, content)
            
            if result["status"] == "success":
                success_count += 1
            else:
                error_count += 1
        
        duration = time.time() - start_time
        
        # Afficher les résultats
        progress_bar.progress(1.0)
        progress_text.markdown(f"**✅ Enrichissement terminé !**")
        status_text.empty()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Succès", success_count)
        with col2:
            st.metric("❌ Erreurs", error_count)
        with col3:
            st.metric("⏱️ Durée", f"{duration:.1f}s")
        
        st.success(f"🎉 Enrichissement terminé ! {success_count}/{total} items traités avec succès.")
        
        # Forcer le rechargement des stats
        st.rerun()

st.divider()


# ======================================================
# SECTION 2 : STATISTIQUES
# ======================================================

st.subheader("📊 Statistiques d'enrichissement")

stats = get_enrichment_stats()

if stats.get("status") == "error":
    st.error(f"Erreur : {stats.get('message')}")
else:
    # Métriques globales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📦 Total items", stats["total_items"])
    with col2:
        st.metric("✅ Items enrichis", stats["enriched_items"])
    with col3:
        st.metric("⏳ À enrichir", stats["not_enriched"])
    
    st.divider()
    
    # Répartition par TAG
    st.markdown("### 🏷️ Répartition par TAG")
    
    by_tags = stats.get("by_tags", {})
    
    if by_tags:
        col_eco, col_bourse, col_crypto = st.columns(3)
        
        with col_eco:
            eco_count = by_tags.get("ECO", 0)
            st.metric("🌍 ECO", eco_count)
        
        with col_bourse:
            bourse_count = by_tags.get("BOURSE", 0)
            st.metric("📈 BOURSE", bourse_count)
        
        with col_crypto:
            crypto_count = by_tags.get("CRYPTO", 0)
            st.metric("₿ CRYPTO", crypto_count)
    else:
        st.info("Aucun item enrichi pour le moment")
    
    st.divider()
    
    # Répartition par LABEL
    st.markdown("### 🏷️ Répartition par LABEL")
    
    by_labels = stats.get("by_labels", {})
    
    if by_labels:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌐 Eco_GeoPol", by_labels.get("Eco_GeoPol", 0))
        with col2:
            st.metric("🇪🇺 PEA", by_labels.get("PEA", 0))
        with col3:
            st.metric("🇺🇸 Action_USA", by_labels.get("Action_USA", 0))
        with col4:
            st.metric("🌏 Action", by_labels.get("Action", 0))
    else:
        st.info("Aucun item enrichi pour le moment")
    
    st.divider()
    
    # Répartition par ZONE
    st.markdown("### 🌍 Répartition par ZONE")
    
    by_zone = stats.get("by_zone", {})
    
    if by_zone:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🇪🇺 Europe", by_zone.get("Europe", 0))
        with col2:
            st.metric("🇺🇸 USA", by_zone.get("USA", 0))
        with col3:
            st.metric("🌏 ASIA", by_zone.get("ASIA", 0))
        with col4:
            st.metric("🌊 OCEANIA", by_zone.get("OCEANIA", 0))
    else:
        st.info("Aucun item enrichi pour le moment")

st.divider()


# ======================================================
# SECTION 3 : PREVIEW DB
# ======================================================

st.subheader("👁️ Preview DB enrichie")

# Filtres
col_tag, col_label, col_zone = st.columns(3)

with col_tag:
    filter_tag = st.selectbox(
        "Filtrer par TAG",
        options=["Tous", "ECO", "BOURSE", "CRYPTO"],
        index=0
    )

with col_label:
    filter_label = st.selectbox(
        "Filtrer par LABEL",
        options=["Tous", "Eco_GeoPol", "PEA", "Action_USA", "Action"],
        index=0
    )

with col_zone:
    filter_zone = st.selectbox(
        "Filtrer par ZONE",
        options=["Tous", "Europe", "USA", "ASIA", "OCEANIA"],
        index=0
    )

# Requête DB avec filtres
try:
    supabase = get_supabase()
    
    query = supabase.table("brew_items").select(
        "id, title, tags, labels, entities, zone, country, processed_at"
    ).not_.is_("labels", "null").order("processed_at", desc=True).limit(50)
    
    # Appliquer les filtres
    if filter_tag != "Tous":
        query = query.eq("tags", filter_tag)
    
    if filter_label != "Tous":
        query = query.eq("labels", filter_label)
    
    if filter_zone != "Tous":
        query = query.eq("zone", filter_zone)
    
    response = query.execute()
    items = response.data or []
    
    if items:
        st.info(f"📊 {len(items)} items affichés (max 50)")
        
        # Afficher le tableau
        import pandas as pd
        
        df = pd.DataFrame(items)
        
        # Sélectionner et réordonner les colonnes
        df_display = df[["title", "tags", "labels", "entities", "zone", "country"]]
        
        # Renommer les colonnes pour l'affichage
        df_display.columns = ["Titre", "Tag", "Label", "Entités", "Zone", "Pays"]
        
        # Tronquer les titres longs
        df_display["Titre"] = df_display["Titre"].str[:60] + "..."
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aucun item enrichi trouvé avec ces filtres")
        
except Exception as e:
    st.error(f"Erreur lors de la récupération des données : {e}")
