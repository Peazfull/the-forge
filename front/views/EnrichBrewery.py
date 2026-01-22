import streamlit as st
from services.enrichment.enrichment_service import (
    enrich_items_batch,
    get_enrichment_stats,
    fetch_items_to_enrich
)
from db.supabase_client import get_supabase
import time


# ======================================================
# CUSTOM CSS
# ======================================================

st.markdown("""
<style>
    /* Cards modernes */
    .card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 16px;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
    }
    
    /* Header épuré */
    h1 {
        font-weight: 600 !important;
        font-size: 2rem !important;
        margin-bottom: 8px !important;
    }
    
    /* Suppression dividers par défaut */
    hr {
        margin: 2rem 0 !important;
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, #e0e0e0, transparent) !important;
    }
</style>
""", unsafe_allow_html=True)


# ======================================================
# HEADER
# ======================================================

st.markdown("# 🏛️ Enrich")
st.markdown("Enrichissement automatique des métadonnées")
st.markdown("")


# ======================================================
# SECTION 1 : LANCER L'ENRICHISSEMENT
# ======================================================

with st.container():
    st.markdown("### ⚡ Enrichissement")
    
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
    # Compter les items à enrichir (tous les items)
    items_to_enrich = fetch_items_to_enrich(limit=limit_value, force_all=True)
    items_count = len(items_to_enrich)
    
    if items_count == 0:
        st.info("📭 Aucun item dans la base de données")
    else:
        st.info(f"📊 {items_count} items prêts")

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
            
            # Récupérer TOUS les items (force_all=True)
            items = fetch_items_to_enrich(limit=limit_value, force_all=True)
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

st.markdown("")


# ======================================================
# SECTION 2 : STATISTIQUES
# ======================================================

with st.container():
    st.markdown("### 📊 Statistiques")
    st.markdown("")
    
    stats = get_enrichment_stats()
    
    if stats.get("status") == "error":
        st.error(f"Erreur : {stats.get('message')}")
    else:
        # Métriques globales en grid
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📦 Total", stats["total_items"])
        with col2:
            st.metric("✅ Enrichis", stats["enriched_items"])
        with col3:
            st.metric("⏳ Restants", stats["not_enriched"])
        
        st.markdown("")
        
        # Répartition par TAG avec gradient
        by_tags = stats.get("by_tags", {})
        
        if by_tags:
            col_eco, col_bourse, col_action, col_crypto = st.columns(4)
            
            with col_eco:
                st.metric("🌍 ECO", by_tags.get("ECO", 0))
            
            with col_bourse:
                st.metric("📈 BOURSE", by_tags.get("BOURSE", 0))
            
            with col_action:
                st.metric("🏢 ACTION", by_tags.get("ACTION", 0))
            
            with col_crypto:
                st.metric("₿ CRYPTO", by_tags.get("CRYPTO", 0))

st.markdown("")


# ======================================================
# SECTION 3 : PREVIEW DB
# ======================================================

with st.container():
    st.markdown("### 👁️ Base de données")
    st.markdown("")
    
    # Filtres
    col_tag, col_label, col_zone = st.columns(3)

    with col_tag:
        filter_tag = st.selectbox(
            "Tag",
            options=["Tous", "ECO", "BOURSE", "ACTION", "CRYPTO"],
            index=0,
            label_visibility="collapsed",
            placeholder="Tag"
        )
    
    with col_label:
        filter_label = st.selectbox(
            "Label",
            options=["Tous", "Eco_GeoPol", "PEA", "Action_USA", "Action"],
            index=0,
            label_visibility="collapsed",
            placeholder="Label"
        )
    
    with col_zone:
        filter_zone = st.selectbox(
            "Zone",
            options=["Tous", "Europe", "USA", "ASIA", "OCEANIA"],
            index=0,
            label_visibility="collapsed",
            placeholder="Zone"
        )
    
    st.markdown("")

    # Requête DB avec filtres
    try:
        supabase = get_supabase()
    
        query = supabase.table("brew_items").select(
            "id, title, content, tags, labels, entities, zone, country, processed_at"
        ).not_.is_("labels", "null").order("processed_at", desc=True)
        
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
            st.caption(f"📊 {len(items)} items · Cliquez pour voir le détail")
        
        # Afficher le tableau
        import pandas as pd
        
        df = pd.DataFrame(items)
        
        # Créer un DataFrame pour l'affichage avec contenus tronqués
        df_display = df.copy()
        df_display["title_short"] = df_display["title"].str[:40] + "..."
        df_display["content_short"] = df_display["content"].str[:60] + "..."
        
        # Sélectionner les colonnes à afficher
        df_table = df_display[["title_short", "content_short", "tags", "labels", "entities", "zone", "country"]]
        df_table.columns = ["Titre", "Contenu", "Tag", "Label", "Entités", "Zone", "Pays"]
        
        # Fonction de style pour colorer les tags avec gradient transparent
        def color_tags(val):
            if val == "ECO":
                return "background: linear-gradient(135deg, rgba(74, 144, 226, 0.15) 0%, rgba(74, 144, 226, 0.25) 100%); color: #2c5aa0; font-weight: 600; border-radius: 6px; padding: 4px 12px;"
            elif val == "BOURSE":
                return "background: linear-gradient(135deg, rgba(155, 89, 182, 0.15) 0%, rgba(155, 89, 182, 0.25) 100%); color: #6c3483; font-weight: 600; border-radius: 6px; padding: 4px 12px;"
            elif val == "ACTION":
                return "background: linear-gradient(135deg, rgba(39, 174, 96, 0.15) 0%, rgba(39, 174, 96, 0.25) 100%); color: #1e7e34; font-weight: 600; border-radius: 6px; padding: 4px 12px;"
            elif val == "CRYPTO":
                return "background: linear-gradient(135deg, rgba(243, 156, 18, 0.15) 0%, rgba(243, 156, 18, 0.25) 100%); color: #c87f0a; font-weight: 600; border-radius: 6px; padding: 4px 12px;"
            return ""
        
        # Appliquer le style sur la colonne Tag
        styled_df = df_table.style.applymap(color_tags, subset=["Tag"])
        
        # Afficher le tableau avec sélection
        event = st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=450,
            on_select="rerun",
            selection_mode="single-row"
        )
        
            # Si une ligne est sélectionnée, afficher le détail complet
            if event.selection and "rows" in event.selection and len(event.selection["rows"]) > 0:
                selected_idx = event.selection["rows"][0]
                selected_item = df.iloc[selected_idx]
                
                st.markdown("")
                st.markdown("#### 📄 Détail")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**{selected_item['title']}**")
                    st.markdown(selected_item["content"])
                
                with col2:
                    st.metric("Tag", selected_item["tags"])
                    st.metric("Label", selected_item["labels"])
                    st.metric("Entités", selected_item["entities"])
                    st.caption(f"{selected_item['zone']} · {selected_item['country']}")
        else:
            st.info("Aucun item enrichi trouvé avec ces filtres")
            
    except Exception as e:
        st.error(f"Erreur : {e}")
