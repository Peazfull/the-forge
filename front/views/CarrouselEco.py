import streamlit as st
import time
from db.supabase_client import get_supabase
from services.carousel.carousel_eco_service import insert_items_to_carousel_eco, get_carousel_eco_items
from services.carousel.generate_carousel_texts_service import generate_all_carousel_texts, update_carousel_text

# ======================================================
# CUSTOM CSS
# ======================================================

def inject_custom_css():
    st.markdown("""
    <style>
    /* Variables */
    :root {
        --gray-50: #f9fafb;
        --gray-100: #f3f4f6;
        --gray-200: #e5e7eb;
        --gray-600: #4b5563;
        --gray-900: #111827;
        --green: #10b981;
        --blue: #3b82f6;
    }
    
    /* Réduire padding */
    .block-container {
        padding-top: 2rem !important;
    }
    
    /* Header */
    .carousel-header {
        background: transparent;
        color: var(--gray-900);
        padding: 20px 0;
        margin-bottom: 24px;
        border-bottom: 2px solid var(--gray-200);
    }
    
    .carousel-header h1 {
        margin: 0 !important;
        font-size: 24px !important;
        font-weight: 600 !important;
    }
    
    .carousel-header p {
        margin: 4px 0 0 0 !important;
        color: var(--gray-600);
        font-size: 13px !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        font-size: 15px !important;
        font-weight: 600 !important;
    }
    
    /* Captions */
    .stCaption {
        font-size: 13px !important;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 6px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    
    /* Save buttons (petite taille) */
    .save-btn button {
        padding: 4px 8px !important;
        min-width: 40px !important;
        font-size: 18px !important;
    }
    
    /* Inputs */
    input, textarea {
        font-size: 14px !important;
        border-radius: 6px !important;
    }
    
    /* Markdown headers */
    h3 {
        font-size: 16px !important;
        font-weight: 600 !important;
        margin-top: 16px !important;
    }
    
    /* Dividers */
    hr {
        margin: 12px 0 !important;
        border-color: var(--gray-200) !important;
    }
    
    /* Compteur de caractères */
    .char-counter {
        font-size: 11px;
        color: var(--gray-600);
        margin-top: -8px;
        margin-bottom: 8px;
    }
    
    .char-counter.warning {
        color: #f59e0b;
        font-weight: 500;
    }
    
    .char-counter.error {
        color: #ef4444;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# ======================================================
# PAGE CONFIG
# ======================================================

inject_custom_css()

st.markdown("""
<div class="carousel-header">
    <h1>🌍 Carrousel Eco</h1>
    <p>Sélection & génération de contenus carrousel pour actualités économiques</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# SESSION STATE INIT
# ======================================================

# Flag pour savoir si on doit initialiser avec les 8 premiers
if "eco_initialized" not in st.session_state:
    st.session_state.eco_initialized = False
    st.session_state.eco_selected_items = []

if "eco_modal_item" not in st.session_state:
    st.session_state.eco_modal_item = None

if "eco_preview_mode" not in st.session_state:
    st.session_state.eco_preview_mode = False

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
    """Envoie les items sélectionnés vers la table carousel_eco"""
    
    # Appel du service d'insertion
    result = insert_items_to_carousel_eco(st.session_state.eco_selected_items)
    
    if result["status"] == "success":
        st.success(f"{result['inserted']} items envoyés · Prêts pour génération")
        # Reset sélection
        st.session_state.eco_selected_items = []
        st.session_state.eco_initialized = False
        st.session_state.eco_preview_mode = False
    else:
        st.error(f"Erreur : {result['message']}")


def toggle_preview_mode():
    """Bascule entre tri par score et tri par position"""
    st.session_state.eco_preview_mode = not st.session_state.eco_preview_mode


def generate_texts():
    """Lance la génération IA des textes carousel"""
    with st.spinner("Génération en cours..."):
        result = generate_all_carousel_texts()
    
    # Nettoyer le session_state pour forcer le rechargement des valeurs de la DB
    keys_to_delete = [key for key in st.session_state.keys() if key.startswith("title_carou_") or key.startswith("content_carou_")]
    for key in keys_to_delete:
        del st.session_state[key]
    
    if result["status"] == "success":
        st.success(f"{result['success']}/{result['total']} textes générés")
    elif result["status"] == "partial":
        st.warning(f"{result['success']}/{result['total']} textes générés · {result['errors']} erreurs")
    else:
        st.error(f"Erreur : {result.get('message', 'Erreur inconnue')}")
    
    # Attendre 1.5s pour que l'utilisateur puisse voir le message, puis refresh
    time.sleep(1.5)
    st.rerun()


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
        
        col_header, col_preview_btn = st.columns([3, 1])
        with col_header:
            st.caption(f"Top 14 · **{selected_count}** sélectionnée{'s' if selected_count > 1 else ''}")
        
        with col_preview_btn:
            if selected_count > 0:
                if st.session_state.eco_preview_mode:
                    if st.button("Tri par score", key="toggle_preview", use_container_width=True, type="secondary"):
                        toggle_preview_mode()
                        st.rerun()
                else:
                    if st.button("Preview ordre", key="toggle_preview", use_container_width=True, type="secondary"):
                        toggle_preview_mode()
                        st.rerun()
        
        st.markdown("")
        
        # Réorganiser les items selon le mode
        if st.session_state.eco_preview_mode and selected_count > 0:
            # Mode preview : afficher dans l'ordre de eco_selected_items
            # Créer un dict pour accès rapide aux items par ID
            items_dict = {item["id"]: item for item in items}
            
            # Reconstruire la liste dans l'ordre de eco_selected_items
            display_items = []
            for item_id in st.session_state.eco_selected_items:
                if item_id in items_dict:
                    display_items.append(items_dict[item_id])
            
            # Ajouter les items non-sélectionnés à la fin
            unselected_items = [item for item in items if item["id"] not in st.session_state.eco_selected_items]
            display_items.extend(unselected_items)
            
            # Info preview
            st.info(f"Mode preview · Ordre final du carrousel (1-{selected_count})")
        else:
            # Mode normal : tri par score (défaut)
            display_items = items
        
        # Tableau
        for idx, item in enumerate(display_items, start=1):
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
                    # En mode preview, afficher la position en lecture seule
                    if st.session_state.eco_preview_mode:
                        st.markdown(f"**#{current_position}**")
                    else:
                        # Mode normal : input modifiable
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
        
        # Boutons d'action
        col_send, col_generate = st.columns(2)
        
        with col_send:
            if selected_count > 0:
                if st.button(
                    f"Envoyer ({selected_count})",
                    type="primary",
                    use_container_width=True
                ):
                    send_to_carousel()
                    st.rerun()
            else:
                st.button(
                    "Envoyer (0)",
                    disabled=True,
                    use_container_width=True,
                    help="Sélectionnez au moins 1 item"
                )
        
        with col_generate:
            # Vérifier si des items existent dans carousel_eco
            carousel_data = get_carousel_eco_items()
            has_items_in_db = carousel_data.get("count", 0) > 0
            
            if has_items_in_db:
                if st.button(
                    "Générer textes",
                    type="secondary",
                    use_container_width=True
                ):
                    generate_texts()
                    st.rerun()
            else:
                st.button(
                    "Générer textes",
                    disabled=True,
                    use_container_width=True,
                    help="Envoyez d'abord des items"
                )


# ======================================================
# TEXTES CAROUSEL (MODIFICATION)
# ======================================================

with st.expander("🎨 Textes Carousel", expanded=False):
    
    carousel_data = get_carousel_eco_items()
    
    if carousel_data["status"] == "error":
        st.error(f"Erreur : {carousel_data.get('message', 'Erreur inconnue')}")
    elif carousel_data["count"] == 0:
        st.info("Aucun item · Envoyez d'abord des items depuis 'Bulletin Eco'")
    else:
        st.caption(f"{carousel_data['count']} items · Modifiez les textes si nécessaire")
        st.markdown("")
        
        for item in carousel_data["items"]:
            item_id = item["id"]
            position = item["position"]
            title_original = item["title"]
            # Récupération avec gestion des valeurs None
            title_carou = item.get("title_carou") or ""
            content_carou = item.get("content_carou") or ""
            
            # Debug: afficher les valeurs brutes
            st.write(f"DEBUG - title_carou: '{title_carou}', content_carou: '{content_carou}'")
            
            # Header de l'item (plus compact)
            st.markdown(f"**#{position}** · {title_original[:50]}...")
            
            # Titre carousel
            col_title_input, col_title_save = st.columns([5, 0.6])
            
            with col_title_input:
                # Utiliser une clé unique qui force le rechargement après génération
                input_key = f"title_carou_{item_id}"
                new_title_carou = st.text_input(
                    label="Titre (3 mots max)",
                    value=title_carou,
                    key=input_key,
                    placeholder="Ex: FED : CHOC HISTORIQUE"
                )
                
                # Compteur de caractères pour titre
                title_len = len(new_title_carou)
                # Limites indicatives (à ajuster selon Pillow)
                if title_len > 50:  # Limite haute (rouge)
                    st.markdown(f'<p class="char-counter error">{title_len} caractères (trop long)</p>', unsafe_allow_html=True)
                elif title_len > 35:  # Limite moyenne (orange)
                    st.markdown(f'<p class="char-counter warning">{title_len} caractères (limite proche)</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p class="char-counter">{title_len} caractères</p>', unsafe_allow_html=True)
            
            with col_title_save:
                if st.button("💾", key=f"save_title_{item_id}", use_container_width=True, type="primary"):
                    result = update_carousel_text(item_id, "title_carou", new_title_carou)
                    if result["status"] == "success":
                        st.success("✓")
                        st.rerun()
                    else:
                        st.error("✗")
            
            # Content carousel
            col_content_input, col_content_save = st.columns([5, 0.6])
            
            with col_content_input:
                # Utiliser une clé unique qui force le rechargement après génération
                content_key = f"content_carou_{item_id}"
                new_content_carou = st.text_area(
                    label="Content (2 phrases max)",
                    value=content_carou,
                    key=content_key,
                    placeholder="Ex: La banque centrale frappe fort. Les marchés explosent.",
                    height=70
                )
                
                # Compteur de caractères pour content
                content_len = len(new_content_carou)
                # Limites indicatives (à ajuster selon Pillow)
                if content_len > 200:  # Limite haute (rouge)
                    st.markdown(f'<p class="char-counter error">{content_len} caractères (trop long)</p>', unsafe_allow_html=True)
                elif content_len > 150:  # Limite moyenne (orange)
                    st.markdown(f'<p class="char-counter warning">{content_len} caractères (limite proche)</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p class="char-counter">{content_len} caractères</p>', unsafe_allow_html=True)
            
            with col_content_save:
                if st.button("💾", key=f"save_content_{item_id}", use_container_width=True, type="secondary"):
                    result = update_carousel_text(item_id, "content_carou", new_content_carou)
                    if result["status"] == "success":
                        st.success("✓")
                        st.rerun()
                    else:
                        st.error("✗")
            
            st.divider()


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
