import streamlit as st
from db.supabase_client import get_supabase
from services.carousel.carousel_eco_service import insert_items_to_carousel_eco

# ======================================================
# PAGE CONFIG
# ======================================================

st.title("🌍 Carrousel Eco")
st.divider()

# ======================================================
# SESSION STATE INIT
# ======================================================

# Flag pour savoir si on doit initialiser avec les 8 premiers
if "eco_initialized" not in st.session_state:
    st.session_state.eco_initialized = False
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
    
    # Appel du service d'insertion
    result = insert_items_to_carousel_eco(st.session_state.eco_selected_items)
    
    if result["status"] == "success":
        st.success(result["message"])
        st.info(f"🎨 {result['inserted']} items prêts pour la transformation IA")
        # Reset sélection
        st.session_state.eco_selected_items = []
        st.session_state.eco_initialized = False
    else:
        st.error(f"❌ Erreur : {result['message']}")


def get_item_position(item_id):
    """Retourne la position d'un item (1-8) ou None si non sélectionné"""
    if item_id in st.session_state.eco_selected_items:
        return st.session_state.eco_selected_items.index(item_id) + 1
    return None


def set_item_position(item_id, target_position):
    """Modifie la position d'un item sélectionné"""
    if item_id not in st.session_state.eco_selected_items:
        return
    
    current_idx = st.session_state.eco_selected_items.index(item_id)
    target_idx = target_position - 1
    
    # Retirer et réinsérer
    item = st.session_state.eco_selected_items.pop(current_idx)
    st.session_state.eco_selected_items.insert(target_idx, item)


# ======================================================
# CONTENT
# ======================================================

with st.expander("📰 Bulletin Eco", expanded=False):
    
    # Fetch data
    items = fetch_top_eco_items(limit=14)
    
    if not items:
        st.warning("Aucun item ECO trouvé en DB")
    else:
        # Initialisation : cocher les 8 premiers par défaut (une seule fois)
        if not st.session_state.eco_initialized and len(items) >= 8:
            st.session_state.eco_selected_items = [item["id"] for item in items[:8]]
            st.session_state.eco_initialized = True
        
        # Header
        selected_count = len(st.session_state.eco_selected_items)
        st.caption(f"📊 Top 14 actualités ECO · **{selected_count} / 8** sélectionnées · Cochez et assignez les positions (1-8)")
        
        # Tableau
        for idx, item in enumerate(items, start=1):
            item_id = item["id"]
            title = item.get("title", "Sans titre")
            content = item.get("content", "")
            tag = item.get("tags", "")
            label = item.get("labels", "")
            score = item.get("score_global", 0)
            
            # Truncate
            title_short = title[:45] + "..." if len(title) > 45 else title
            content_short = content[:80] + "..." if len(content) > 80 else content
            
            # Row
            col_check, col_pos, col_title, col_content, col_tag, col_label, col_score, col_view = st.columns([0.4, 0.8, 2, 2.5, 0.6, 1, 0.7, 0.4])
            
            with col_check:
                # Checkbox logic
                is_selected = item_id in st.session_state.eco_selected_items
                is_disabled = (not is_selected) and (selected_count >= 8)
                
                st.checkbox(
                    label="",
                    value=is_selected,
                    key=f"check_eco_{item_id}",
                    disabled=is_disabled,
                    label_visibility="collapsed",
                    on_change=toggle_selection,
                    args=(item_id,)
                )
            
            with col_pos:
                # Input position (actif uniquement si coché)
                current_position = get_item_position(item_id)
                
                if is_selected:
                    new_position = st.number_input(
                        label="Pos",
                        min_value=1,
                        max_value=selected_count,
                        value=current_position if current_position else 1,
                        step=1,
                        key=f"pos_eco_{item_id}",
                        label_visibility="collapsed"
                    )
                    
                    # Si changement de position
                    if new_position != current_position:
                        set_item_position(item_id, new_position)
                        st.rerun()
                else:
                    st.markdown("—")
            
            with col_title:
                st.markdown(f"**{title_short}**")
            
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
        
        st.markdown("")
        
        # Bouton d'envoi
        if selected_count == 8:
            if st.button("🚀 Envoyer vers Carousel Eco", type="primary", use_container_width=True):
                send_to_carousel()
                st.rerun()
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
