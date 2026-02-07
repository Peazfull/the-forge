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
    /* Variables */
    :root {
        --gray-50: #f9fafb;
        --gray-100: #f3f4f6;
        --gray-200: #e5e7eb;
        --gray-600: #4b5563;
        --gray-900: #111827;
    }
    
    /* Réduire l'espace en haut */
    .block-container {
        padding-top: 2rem !important;
    }
    
    /* Header principal */
    .page-header {
        background: transparent;
        color: var(--gray-900);
        padding: 24px 0;
        margin-bottom: 24px;
        border-bottom: 2px solid var(--gray-200);
    }
    
    .page-header h1 {
        margin: 0 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    
    .page-header p {
        margin: 4px 0 0 0 !important;
        color: var(--gray-600);
        font-size: 14px !important;
    }
    
    /* Section headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 0 12px 0;
        border-bottom: 1px solid var(--gray-200);
        margin: 24px 0 16px 0;
    }
    
    .section-header h2 {
        margin: 0 !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        color: var(--gray-900);
    }
    
    .section-title {
        font-size: 15px;
        font-weight: 600;
        color: var(--gray-900);
        margin: 0 0 8px 0;
    }
    
    /* Boutons */
    .stButton button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
</style>
""", unsafe_allow_html=True)


# ======================================================
# HEADER
# ======================================================

st.markdown("""
<div class="page-header">
    <h1>🏛️ Enrich</h1>
    <p>Enrichissement automatique des métadonnées · AI-Powered</p>
</div>
""", unsafe_allow_html=True)


# ======================================================
# SECTION 1 : LANCER L'ENRICHISSEMENT
# ======================================================

st.markdown("""
<div class="section-header">
    <h2>⚡ Enrichissement</h2>
</div>
""", unsafe_allow_html=True)

with st.container():
    col_button, col_limit, col_force = st.columns([2.5, 0.8, 0.7])
    
    with col_limit:
        limit_option = st.selectbox(
            "Limite",
            options=[10, 50, 100, 500, "Tous"],
            index=4,
            label_visibility="collapsed"
        )
        
        if limit_option == "Tous":
            limit_value = None
        else:
            limit_value = int(limit_option)
    
    with col_force:
        force_all = st.checkbox("♻️ Re-traiter tout", value=False, help="Si décoché : uniquement les nouveaux items")
    
    with col_button:
        # Compter les items à enrichir
        items_to_enrich = fetch_items_to_enrich(limit=limit_value, force_all=force_all)
        items_count = len(items_to_enrich)
        
        # Compter le total pour affichage
        items_total = fetch_items_to_enrich(limit=None, force_all=True)
        total_count = len(items_total)
        
        if total_count == 0:
            st.info("📭 Aucun item dans la base de données")
        elif items_count == 0 and not force_all:
            st.success("✅ Tous les items sont déjà enrichis ! (cochez ♻️ pour re-traiter)")
    
        if items_count > 0:
            button_label = f"🚀 Enrichir {items_count} item{'s' if items_count > 1 else ''}"
            if st.button(button_label, use_container_width=True, type="primary"):
                
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
                
                # Récupérer les items selon le mode sélectionné
                items = fetch_items_to_enrich(limit=limit_value, force_all=force_all)
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

st.markdown("""
<div class="section-header">
    <h2>📊 Statistiques</h2>
</div>
""", unsafe_allow_html=True)

with st.container():
    stats = get_enrichment_stats()
    
    if stats.get("status") == "error":
        st.error(f"Erreur : {stats.get('message')}")
    else:
        by_tags = stats.get("by_tags", {})
        
        # Design minimaliste en une seule ligne avec colonnes
        cols = st.columns(5)
        
        with cols[0]:
            st.markdown("""
                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 6px;'>
                    <div style='font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;'>Total</div>
                    <div style='font-size: 20px; font-weight: 600; color: #111827; margin-top: 2px;'>{}</div>
                </div>
            """.format(stats["total_items"]), unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown("""
                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 6px;'>
                    <div style='font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;'>Enrichis</div>
                    <div style='font-size: 20px; font-weight: 600; color: #10b981; margin-top: 2px;'>{}</div>
                </div>
            """.format(stats["enriched_items"]), unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown("""
                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 6px;'>
                    <div style='font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;'>Eco</div>
                    <div style='font-size: 20px; font-weight: 600; color: #3b82f6; margin-top: 2px;'>{}</div>
                </div>
            """.format(by_tags.get("ECO", 0)), unsafe_allow_html=True)
        
        with cols[3]:
            st.markdown("""
                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 6px;'>
                    <div style='font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;'>Bourse</div>
                    <div style='font-size: 20px; font-weight: 600; color: #8b5cf6; margin-top: 2px;'>{}</div>
                </div>
            """.format(by_tags.get("BOURSE", 0)), unsafe_allow_html=True)
        
        
        with cols[4]:
            st.markdown("""
                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 6px;'>
                    <div style='font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;'>Crypto</div>
                    <div style='font-size: 20px; font-weight: 600; color: #f59e0b; margin-top: 2px;'>{}</div>
                </div>
            """.format(by_tags.get("CRYPTO", 0)), unsafe_allow_html=True)

st.markdown("")


# ======================================================
# SECTION 3 : PREVIEW DB
# ======================================================

st.markdown("""
<div class="section-header">
    <h2>👁️ Base de données</h2>
</div>
""", unsafe_allow_html=True)

with st.container():
    # Filtres
    col_tag, col_label, col_zone = st.columns(3)

    with col_tag:
        filter_tag = st.selectbox(
            "Tag",
            options=["Tous", "ECO", "BOURSE", "CRYPTO"],
            index=0,
            label_visibility="collapsed",
            placeholder="Tag"
        )
    
    with col_label:
        filter_label = st.selectbox(
            "Label",
            options=["Tous", "Eco-Geopol", "Indices", "PEA", "Action", "Commodités", "Crypto"],
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
