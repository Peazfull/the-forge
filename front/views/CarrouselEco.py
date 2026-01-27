import streamlit as st
from db.supabase_client import get_supabase

# ======================================================
# PAGE CONFIG
# ======================================================

st.title("🌍 Carrousel Eco")
st.divider()

# ======================================================
# SESSION STATE INIT
# ======================================================

if "eco_selected_items" not in st.session_state:
    st.session_state.eco_selected_items = []

if "eco_modal_item" not in st.session_state:
    st.session_state.eco_modal_item = None

# ======================================================
# FONCTIONS
# ======================================================

def fetch_top_eco_items(limit=14):
    """Récupère le top N des items ECO triés par score"""
    try:
        supabase = get_supabase()
        response = supabase.table("brew_items").select(
            "id, title, content, tags, labels, score_global"
        ).eq("tags", "ECO").not_.is_("score_global", "null").order(
            "score_global", desc=True
        ).limit(limit).execute()
        
        return response.data or []
    except Exception as e:
        st.error(f"Erreur DB : {e}")
        return []


def toggle_selection(item_id):
    """Ajoute/retire un item de la sélection"""
    if item_id in st.session_state.eco_selected_items:
        st.session_state.eco_selected_items.remove(item_id)
    else:
        if len(st.session_state.eco_selected_items) < 8:
            st.session_state.eco_selected_items.append(item_id)


def open_modal(item):
    """Ouvre le modal avec le détail de l'item"""
    st.session_state.eco_modal_item = item


def close_modal():
    """Ferme le modal"""
    st.session_state.eco_modal_item = None


def send_to_carousel():
    """Envoie les 8 items sélectionnés vers la table carousel_eco"""
    # TODO: Implémenter l'insertion en DB (table carousel_eco à créer)
    st.success(f"✅ {len(st.session_state.eco_selected_items)} items envoyés vers Carousel Eco !")
    st.info("💡 Table carousel_eco à créer côté Supabase")
    # Reset sélection
    st.session_state.eco_selected_items = []


# ======================================================
# CONTENT
# ======================================================

with st.expander("📰 Bulletin Eco", expanded=True):
    
    # Fetch data
    items = fetch_top_eco_items(limit=14)
    
    if not items:
        st.warning("Aucun item ECO trouvé en DB")
    else:
        # Header
        selected_count = len(st.session_state.eco_selected_items)
        st.caption(f"📊 Top 14 actualités ECO · **{selected_count} / 8** sélectionnées")
        
        # Tableau
        for idx, item in enumerate(items, start=1):
            item_id = item["id"]
            title = item.get("title", "Sans titre")
            content = item.get("content", "")
            tag = item.get("tags", "")
            label = item.get("labels", "")
            score = item.get("score_global", 0)
            
            # Truncate
            title_short = title[:50] + "..." if len(title) > 50 else title
            content_short = content[:100] + "..." if len(content) > 100 else content
            
            # Row
            col_check, col_title, col_content, col_tag, col_label, col_score, col_view = st.columns([0.5, 2, 3, 0.8, 1.2, 0.8, 0.5])
            
            with col_check:
                # Checkbox logic
                is_selected = item_id in st.session_state.eco_selected_items
                is_disabled = (not is_selected) and (selected_count >= 8)
                
                if st.checkbox(
                    label="",
                    value=is_selected,
                    key=f"check_eco_{item_id}",
                    disabled=is_disabled,
                    label_visibility="collapsed"
                ):
                    if not is_selected:
                        toggle_selection(item_id)
                else:
                    if is_selected:
                        toggle_selection(item_id)
            
            with col_title:
                st.markdown(f"**{idx}.** {title_short}")
            
            with col_content:
                st.caption(content_short)
            
            with col_tag:
                st.markdown(f"`{tag}`")
            
            with col_label:
                st.markdown(f"`{label}`")
            
            with col_score:
                # Color coding
                if score >= 85:
                    st.markdown(f"🟢 **{score}**")
                elif score >= 70:
                    st.markdown(f"🟡 **{score}**")
                else:
                    st.markdown(f"⚪ **{score}**")
            
            with col_view:
                if st.button("👁️", key=f"view_eco_{item_id}", help="Voir le détail"):
                    open_modal(item)
            
            st.divider()
        
        # Action button
        st.markdown("")
        if selected_count == 8:
            if st.button("🚀 Envoyer vers Carousel Eco", type="primary", use_container_width=True):
                send_to_carousel()
        else:
            st.button(
                f"🚀 Envoyer vers Carousel Eco ({selected_count}/8)",
                disabled=True,
                use_container_width=True,
                help="Sélectionnez exactement 8 items"
            )


# ======================================================
# MODAL (DETAIL)
# ======================================================

if st.session_state.eco_modal_item:
    item = st.session_state.eco_modal_item
    
    @st.dialog("📄 Détail de l'actualité", width="large")
    def show_detail():
        st.markdown(f"### {item.get('title', 'Sans titre')}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tag", item.get('tags', 'N/A'))
        with col2:
            st.metric("Label", item.get('labels', 'N/A'))
        with col3:
            st.metric("Score", item.get('score_global', 0))
        
        st.divider()
        
        st.markdown("#### Contenu complet")
        st.markdown(item.get('content', 'Pas de contenu'))
        
        st.divider()
        
        if st.button("✖️ Fermer", use_container_width=True):
            close_modal()
            st.rerun()
    
    show_detail()
