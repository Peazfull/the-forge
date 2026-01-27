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


def move_up(item_id):
    """Déplace un item vers le haut dans l'ordre de sélection"""
    idx = st.session_state.eco_selected_items.index(item_id)
    if idx > 0:
        st.session_state.eco_selected_items[idx], st.session_state.eco_selected_items[idx - 1] = \
            st.session_state.eco_selected_items[idx - 1], st.session_state.eco_selected_items[idx]


def move_down(item_id):
    """Déplace un item vers le bas dans l'ordre de sélection"""
    idx = st.session_state.eco_selected_items.index(item_id)
    if idx < len(st.session_state.eco_selected_items) - 1:
        st.session_state.eco_selected_items[idx], st.session_state.eco_selected_items[idx + 1] = \
            st.session_state.eco_selected_items[idx + 1], st.session_state.eco_selected_items[idx]


# ======================================================
# CONTENT
# ======================================================

with st.expander("📰 Bulletin Eco", expanded=True):
    
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
                
                # Utiliser un callback pour éviter le rerun qui ouvre la modale
                st.checkbox(
                    label="",
                    value=is_selected,
                    key=f"check_eco_{item_id}",
                    disabled=is_disabled,
                    label_visibility="collapsed",
                    on_change=toggle_selection,
                    args=(item_id,)
                )
            
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
        
        st.markdown("")


# ======================================================
# ORDRE DE SÉLECTION
# ======================================================

if st.session_state.eco_selected_items:
    with st.expander("🔢 Ordre du carrousel (drag to reorder)", expanded=True):
        st.caption("👇 Utilisez les flèches pour réordonner les 8 items sélectionnés")
        
        # Récupérer les items complets depuis la DB
        selected_count = len(st.session_state.eco_selected_items)
        
        if selected_count > 0:
            all_items = fetch_top_eco_items(limit=14)
            items_dict = {item["id"]: item for item in all_items}
            
            for position, item_id in enumerate(st.session_state.eco_selected_items, start=1):
                item = items_dict.get(item_id)
                if not item:
                    continue
                
                col_pos, col_arrows, col_title, col_score = st.columns([0.5, 1, 4, 1])
                
                with col_pos:
                    st.markdown(f"**#{position}**")
                
                with col_arrows:
                    col_up, col_down = st.columns(2)
                    with col_up:
                        if position > 1:
                            if st.button("⬆️", key=f"up_{item_id}", help="Monter"):
                                move_up(item_id)
                                st.rerun()
                    with col_down:
                        if position < selected_count:
                            if st.button("⬇️", key=f"down_{item_id}", help="Descendre"):
                                move_down(item_id)
                                st.rerun()
                
                with col_title:
                    title = item.get("title", "Sans titre")
                    title_short = title[:60] + "..." if len(title) > 60 else title
                    st.markdown(title_short)
                
                with col_score:
                    score = item.get("score_global", 0)
                    st.markdown(f"⭐ **{score}**")
        
        st.divider()
        
        # Action button
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
