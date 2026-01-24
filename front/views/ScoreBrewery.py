import streamlit as st
from services.scoring.scoring_service import (
    score_single_item,
    get_scoring_stats,
    fetch_items_to_score
)
from services.scoring.update_score import update_item_score
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
    <h1>⭐ Score</h1>
    <p>Attribution automatique de score qualité/importance · 0-100</p>
</div>
""", unsafe_allow_html=True)


# ======================================================
# SECTION 1 : LANCER LE SCORING
# ======================================================

st.markdown("""
<div class="section-header">
    <h2>🎯 Scoring</h2>
</div>
""", unsafe_allow_html=True)

with st.container():
    col_button, col_limit = st.columns([3, 1])
    
    with col_limit:
        limit_option = st.selectbox(
            "Limite",
            options=[10, 50, 100, 500, "Tous"],
            index=4,  # Par défaut "Tous"
            label_visibility="collapsed"
        )
        
        if limit_option == "Tous":
            limit_value = None
        else:
            limit_value = int(limit_option)
    
    with col_button:
        # Compter les items à scorer
        try:
            items_to_score = fetch_items_to_score(limit=limit_value, force_all=True)
            items_count = len(items_to_score)
        except Exception as e:
            st.error(f"Erreur lors du comptage des items: {str(e)}")
            items_count = 0
        
        if items_count == 0:
            st.info("📭 Aucun item enrichi dans la base de données")
    
        if items_count > 0:
            if st.button("🎯 Lancer le scoring", use_container_width=True, type="primary"):
                
                # Progress bar container
                progress_container = st.container()
                status_container = st.container()
                
                with progress_container:
                    progress_bar = st.progress(0)
                    progress_text = st.empty()
                
                with status_container:
                    status_text = st.empty()
                
                # Lancer le scoring
                start_time = time.time()
                
                items = fetch_items_to_score(limit=limit_value, force_all=True)
                total = len(items)
                success_count = 0
                error_count = 0
                last_error_msg = ""
                
                for idx, item in enumerate(items, start=1):
                    try:
                        item_id = item.get("id")
                        title = item.get("title", "")
                        content = item.get("content", "")
                        tags = item.get("tags")
                        labels = item.get("labels")
                        entities = item.get("entities")
                        source_type = item.get("source_type")
                        
                        # Afficher la progression
                        progress = idx / total
                        progress_bar.progress(progress)
                        progress_text.markdown(f"**Traitement : {idx}/{total} items** ({int(progress*100)}%)")
                        status_text.text(f"Item: {title[:40]}... | Tag: {tags} | Label: {labels}")
                        
                        # Scorer l'item
                        result = score_single_item(item_id, title, content, tags, labels, entities, source_type)
                        
                        # DEBUG visible
                        if result["status"] == "success":
                            success_count += 1
                            status_text.text(f"✅ Score: {result.get('score')} | {title[:40]}...")
                        else:
                            error_count += 1
                            error_msg = result.get('message', 'Inconnue')
                            last_error_msg = error_msg
                            status_text.text(f"❌ Erreur: {error_msg[:80]}")
                    
                    except Exception as e:
                        error_count += 1
                        last_error_msg = str(e)
                        status_text.text(f"❌ Exception: {str(e)[:80]}")
                
                duration = time.time() - start_time
                
                # Afficher les résultats
                progress_bar.progress(1.0)
                progress_text.markdown(f"**✅ Scoring terminé !**")
                status_text.empty()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✅ Succès", success_count)
                with col2:
                    st.metric("❌ Erreurs", error_count)
                with col3:
                    st.metric("⏱️ Durée", f"{duration:.1f}s")
                
                # Afficher message de debug si échec total
                if success_count == 0 and error_count > 0:
                    st.error(f"🚨 AUCUN item scoré avec succès ! Dernière erreur: {last_error_msg}")
                    st.warning("⚠️ Ne pas relancer tout de suite, lire l'erreur ci-dessus !")
                    # Ne pas rerun immédiatement pour laisser voir l'erreur
                elif success_count == 0 and error_count == 0:
                    st.warning("⚠️ Process terminé mais aucun résultat (succès=0, erreur=0). Problème de logique ?")
                else:
                    st.success(f"🎉 Scoring terminé ! {success_count}/{total} items traités avec succès.")
                    # Forcer le rechargement des stats seulement si succès
                    time.sleep(1)
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
    stats = get_scoring_stats()
    
    if stats.get("status") == "error":
        st.error(f"Erreur : {stats.get('message')}")
    else:
        by_range = stats.get("by_range", {})
        
        # Métriques globales (4 colonnes)
        cols_global = st.columns(4)
        
        with cols_global[0]:
            st.markdown("""
                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 6px;'>
                    <div style='font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;'>Total</div>
                    <div style='font-size: 20px; font-weight: 600; color: #111827; margin-top: 2px;'>{}</div>
                </div>
            """.format(stats["total_items"]), unsafe_allow_html=True)
        
        with cols_global[1]:
            st.markdown("""
                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 6px;'>
                    <div style='font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;'>Scorés</div>
                    <div style='font-size: 20px; font-weight: 600; color: #10b981; margin-top: 2px;'>{}</div>
                </div>
            """.format(stats["scored_items"]), unsafe_allow_html=True)
        
        with cols_global[2]:
            st.markdown("""
                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 6px;'>
                    <div style='font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;'>Non scorés</div>
                    <div style='font-size: 20px; font-weight: 600; color: #f59e0b; margin-top: 2px;'>{}</div>
                </div>
            """.format(stats["not_scored"]), unsafe_allow_html=True)
        
        with cols_global[3]:
            st.markdown("""
                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 6px;'>
                    <div style='font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;'>Score moyen</div>
                    <div style='font-size: 20px; font-weight: 600; color: #3b82f6; margin-top: 2px;'>{}</div>
                </div>
            """.format(stats["average_score"]), unsafe_allow_html=True)
        
        st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)
        
        # Distribution par tranches (5 colonnes)
        if by_range:
            cols_range = st.columns(5)
            
            with cols_range[0]:
                st.markdown("""
                    <div style='text-align: center; padding: 8px; background: #fee2e2; border-radius: 6px;'>
                        <div style='font-size: 10px; color: #991b1b; text-transform: uppercase; letter-spacing: 0.5px;'>0-19</div>
                        <div style='font-size: 20px; font-weight: 600; color: #dc2626; margin-top: 2px;'>{}</div>
                    </div>
                """.format(by_range.get("0-19", 0)), unsafe_allow_html=True)
            
            with cols_range[1]:
                st.markdown("""
                    <div style='text-align: center; padding: 8px; background: #fed7aa; border-radius: 6px;'>
                        <div style='font-size: 10px; color: #9a3412; text-transform: uppercase; letter-spacing: 0.5px;'>20-39</div>
                        <div style='font-size: 20px; font-weight: 600; color: #ea580c; margin-top: 2px;'>{}</div>
                    </div>
                """.format(by_range.get("20-39", 0)), unsafe_allow_html=True)
            
            with cols_range[2]:
                st.markdown("""
                    <div style='text-align: center; padding: 8px; background: #fef3c7; border-radius: 6px;'>
                        <div style='font-size: 10px; color: #854d0e; text-transform: uppercase; letter-spacing: 0.5px;'>40-59</div>
                        <div style='font-size: 20px; font-weight: 600; color: #ca8a04; margin-top: 2px;'>{}</div>
                    </div>
                """.format(by_range.get("40-59", 0)), unsafe_allow_html=True)
            
            with cols_range[3]:
                st.markdown("""
                    <div style='text-align: center; padding: 8px; background: #dbeafe; border-radius: 6px;'>
                        <div style='font-size: 10px; color: #1e40af; text-transform: uppercase; letter-spacing: 0.5px;'>60-79</div>
                        <div style='font-size: 20px; font-weight: 600; color: #2563eb; margin-top: 2px;'>{}</div>
                    </div>
                """.format(by_range.get("60-79", 0)), unsafe_allow_html=True)
            
            with cols_range[4]:
                st.markdown("""
                    <div style='text-align: center; padding: 8px; background: #d1fae5; border-radius: 6px;'>
                        <div style='font-size: 10px; color: #065f46; text-transform: uppercase; letter-spacing: 0.5px;'>80-100</div>
                        <div style='font-size: 20px; font-weight: 600; color: #059669; margin-top: 2px;'>{}</div>
                    </div>
                """.format(by_range.get("80-100", 0)), unsafe_allow_html=True)

st.markdown("")


# ======================================================
# SECTION 3 : PREVIEW & ÉDITION
# ======================================================

st.markdown("""
<div class="section-header">
    <h2>✏️ Preview & Édition</h2>
</div>
""", unsafe_allow_html=True)

with st.container():
    # Filtres
    col_tag, col_label, col_score_min, col_score_max, col_sort = st.columns(5)

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
    
    with col_score_min:
        filter_score_min = st.number_input(
            "Score min",
            min_value=0,
            max_value=100,
            value=0,
            step=10,
            label_visibility="collapsed"
        )
    
    with col_score_max:
        filter_score_max = st.number_input(
            "Score max",
            min_value=0,
            max_value=100,
            value=100,
            step=10,
            label_visibility="collapsed"
        )
    
    with col_sort:
        filter_sort = st.selectbox(
            "Tri",
            options=["Score ↓", "Score ↑"],
            index=0,
            label_visibility="collapsed"
        )
    
    st.markdown("")

    # Requête DB avec filtres
    try:
        supabase = get_supabase()
    
        query = supabase.table("brew_items").select(
            "id, title, content, tags, labels, score_global"
        ).not_.is_("score_global", "null").order(
            "score_global", desc=(filter_sort == "Score ↓")
        )
        
        # Appliquer les filtres
        if filter_tag != "Tous":
            query = query.eq("tags", filter_tag)
        
        if filter_label != "Tous":
            query = query.eq("labels", filter_label)
        
        if filter_score_min > 0:
            query = query.gte("score_global", filter_score_min)
        
        if filter_score_max < 100:
            query = query.lte("score_global", filter_score_max)
        
        response = query.execute()
        items = response.data or []
        
        if items:
            st.caption(f"📊 {len(items)} items · Cliquez pour voir le détail et éditer le score")
            
            # Afficher le tableau
            import pandas as pd
            
            df = pd.DataFrame(items)
            
            # Créer un DataFrame pour l'affichage
            df_display = df.copy()
            df_display["title_short"] = df_display["title"].str[:50] + "..."
            
            # Sélectionner les colonnes à afficher
            df_table = df_display[["title_short", "tags", "labels", "score_global"]]
            df_table.columns = ["Titre", "Tag", "Label", "Score"]
            
            # Fonction de style pour colorer les scores
            def color_scores(val):
                if isinstance(val, (int, float)):
                    if val >= 80:
                        return "background: #d1fae5; color: #065f46; font-weight: 600; border-radius: 4px; padding: 4px 8px;"
                    elif val >= 60:
                        return "background: #dbeafe; color: #1e40af; font-weight: 600; border-radius: 4px; padding: 4px 8px;"
                    elif val >= 40:
                        return "background: #fef3c7; color: #854d0e; font-weight: 600; border-radius: 4px; padding: 4px 8px;"
                    elif val >= 20:
                        return "background: #fed7aa; color: #9a3412; font-weight: 600; border-radius: 4px; padding: 4px 8px;"
                    else:
                        return "background: #fee2e2; color: #991b1b; font-weight: 600; border-radius: 4px; padding: 4px 8px;"
                return ""
            
            # Appliquer le style sur la colonne Score
            styled_df = df_table.style.applymap(color_scores, subset=["Score"])
            
            # Afficher le tableau avec sélection
            event = st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                height=450,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # Si une ligne est sélectionnée, afficher le détail + édition
            if event.selection and "rows" in event.selection and len(event.selection["rows"]) > 0:
                selected_idx = event.selection["rows"][0]
                selected_item = df.iloc[selected_idx]
                
                st.markdown("")
                st.markdown("#### 📝 Détail & Édition")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**{selected_item['title']}**")
                    st.markdown(selected_item["content"])
                
                with col2:
                    st.metric("Tag", selected_item["tags"])
                    st.metric("Label", selected_item["labels"])
                    
                    st.markdown("---")
                    
                    # Section édition score - TRÈS VISIBLE
                    st.markdown("### ✏️ Modifier le score")
                    st.markdown(f"**Score actuel : {int(selected_item['score_global'])}/100**")
                    st.markdown("")
                    
                    # Initialiser la valeur dans session_state si pas encore définie
                    if f"temp_score_{selected_item['id']}" not in st.session_state:
                        st.session_state[f"temp_score_{selected_item['id']}"] = int(selected_item["score_global"])
                    
                    # Slider GROS et visible
                    new_score_slider = st.slider(
                        "👆 Glissez pour changer",
                        min_value=0,
                        max_value=100,
                        value=st.session_state[f"temp_score_{selected_item['id']}"],
                        step=5,
                        key=f"slider_{selected_item['id']}"
                    )
                    
                    # Mettre à jour session state
                    st.session_state[f"temp_score_{selected_item['id']}"] = new_score_slider
                    
                    # Affichage du score sélectionné
                    st.markdown(f"### Score sélectionné : **{new_score_slider}**")
                    st.markdown("")
                    
                    # GROS BOUTON BIEN VISIBLE
                    if st.button("💾 SAUVEGARDER CE SCORE", type="primary", use_container_width=True, key=f"save_btn_{selected_item['id']}"):
                        result = update_item_score(selected_item["id"], new_score_slider)
                        
                        if result["status"] == "success":
                            st.success(f"✅ Score mis à jour : {new_score_slider}/100")
                            # Nettoyer session state
                            if f"temp_score_{selected_item['id']}" in st.session_state:
                                del st.session_state[f"temp_score_{selected_item['id']}"]
                            time.sleep(0.8)
                            st.rerun()
                        else:
                            st.error(f"❌ Erreur : {result['message']}")
        else:
            st.info("Aucun item scoré trouvé avec ces filtres")
            
    except Exception as e:
        st.error(f"Erreur : {e}")
