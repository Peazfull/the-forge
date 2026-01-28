import streamlit as st
import time
import base64
from db.supabase_client import get_supabase
from services.carousel.carousel_eco_service import insert_items_to_carousel_eco, get_carousel_eco_items
from services.carousel.generate_carousel_texts_service import generate_all_carousel_texts, update_carousel_text
from services.carousel.image_generation_service import generate_carousel_image
from services.carousel.carousel_image_service import (
    generate_and_save_carousel_image,
    generate_prompt_image_3,
    save_prompt_image_3_to_db,
    read_carousel_image,
    save_image_base64
)

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
        padding: 4px 6px !important;
        min-width: 28px !important;
        height: 28px !important;
        font-size: 12px !important;
        line-height: 1 !important;
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

# Toujours initialiser eco_selected_items si absent (indépendant de eco_initialized)
if "eco_selected_items" not in st.session_state:
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
    # Sécurité : initialiser si absent
    if "eco_selected_items" not in st.session_state:
        st.session_state.eco_selected_items = []
    
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
    """Envoie les items sélectionnés et lance la génération automatique ligne par ligne"""
    # Sécurité : initialiser si absent
    if "eco_selected_items" not in st.session_state:
        st.session_state.eco_selected_items = []
    
    # Étape 1 : Insertion des items
    if st.session_state.generation_step == "insert":
        st.info("📤 Envoi des items...")
        result = insert_items_to_carousel_eco(st.session_state.eco_selected_items)
        
        if result["status"] != "success":
            st.error(f"❌ Erreur insertion : {result['message']}")
            # Reset
            del st.session_state.generation_step
            return
        
        st.success(f"✅ {result['inserted']} items envoyés")
        st.session_state.generation_step = "generate_item"
        st.session_state.generation_current_idx = 0
        time.sleep(1)
        st.rerun()
    
    # Étape 2 : Générer item par item
    elif st.session_state.generation_step == "generate_item":
        # Récupérer les items
        carousel_data = get_carousel_eco_items()
        
        if carousel_data["status"] != "success" or carousel_data["count"] == 0:
            st.error("❌ Erreur récupération items")
            del st.session_state.generation_step
            return
        
        items = carousel_data["items"]
        current_idx = st.session_state.generation_current_idx
        
        # Sécurité : forcer l'arrêt si index invalide
        if current_idx is None or current_idx < 0:
            del st.session_state.generation_step
            if "generation_current_idx" in st.session_state:
                del st.session_state.generation_current_idx
            return
        
        # Vérifier si on a fini
        if current_idx >= len(items):
            st.success("🎉 Génération terminée")
            
            # Reset
            st.session_state.eco_selected_items = []
            st.session_state.eco_initialized = False
            st.session_state.eco_preview_mode = False
            
            # Incrémenter compteur pour refresh inputs
            if "carousel_generation_count" not in st.session_state:
                st.session_state.carousel_generation_count = 0
            st.session_state.carousel_generation_count += 1
            
            # IMPORTANT : Supprimer generation_step EN DERNIER pour éviter un rerun supplémentaire
            del st.session_state.generation_step
            del st.session_state.generation_current_idx
            
            # Ne PAS faire de rerun ici, laisser la page s'afficher normalement
            return
        
        # Item actuel
        item = items[current_idx]
        item_id = item["id"]
        position = item["position"]
        title = item.get("title", "")
        content = item.get("content", "")
        
        # Progress
        st.info(f"⏳ Item #{position}/{len(items)} : {title[:40]}...")
        progress = (current_idx + 1) / len(items)
        st.progress(progress)
        
        # Sous-étapes avec spinner
        with st.spinner(f"✍️ Génération titre & contenu #{position}..."):
            # Import de la fonction individuelle
            from services.carousel.generate_carousel_texts_service import generate_carousel_text_for_item, generate_image_prompt_for_item
            
            # Générer titre et contenu
            text_result = generate_carousel_text_for_item(title, content)
            
            if text_result["status"] != "success":
                st.error(f"❌ Erreur texte #{position} : {text_result.get('message')}")
                st.session_state.generation_current_idx += 1
                time.sleep(1)
                st.rerun()
                return
            
            # Générer prompts d'images
            prompt_1_result = generate_image_prompt_for_item(title, content, prompt_type="sunset")
            prompt_2_result = generate_image_prompt_for_item(title, content, prompt_type="studio")
            
            # Sauvegarder en DB
            supabase = get_supabase()
            supabase.table("carousel_eco").update({
                "title_carou": text_result["title_carou"],
                "content_carou": text_result["content_carou"],
                "prompt_image_1": prompt_1_result.get("image_prompt"),
                "prompt_image_2": prompt_2_result.get("image_prompt")
            }).eq("id", item_id).execute()
        
        st.success(f"✅ Textes générés #{position}")
        
        # Générer l'image
        with st.spinner(f"🎨 Génération image #{position}..."):
            if prompt_1_result.get("status") == "success":
                img_result = generate_and_save_carousel_image(prompt_1_result["image_prompt"], position)
                
                if img_result["status"] == "success":
                    st.success(f"✅ Image générée #{position}")
                else:
                    st.error(f"❌ Image #{position} : {img_result.get('message')}")
            else:
                st.error(f"❌ Pas de prompt pour image #{position}")
        
        # Incrémenter le compteur pour forcer le refresh des inputs
        if "carousel_generation_count" not in st.session_state:
            st.session_state.carousel_generation_count = 0
        st.session_state.carousel_generation_count += 1
        
        # Passer à l'item suivant
        st.session_state.generation_current_idx += 1
        time.sleep(0.5)
        st.rerun()


def toggle_preview_mode():
    """Bascule entre tri par score et tri par position"""
    st.session_state.eco_preview_mode = not st.session_state.eco_preview_mode


def generate_texts():
    """Lance la génération IA des textes carousel + images initiales"""
    # Étape 1 : Générer les textes et prompts
    with st.spinner("Génération des textes et prompts..."):
        result = generate_all_carousel_texts()
    
    if result["status"] == "error":
        st.error(f"Erreur : {result.get('message', 'Erreur inconnue')}")
        time.sleep(1.5)
        st.rerun()
        return
    
    # Afficher résultat textes
    if result["status"] == "success":
        st.success(f"✅ {result['success']}/{result['total']} textes générés")
    elif result["status"] == "partial":
        st.warning(f"⚠️ {result['success']}/{result['total']} textes générés · {result['errors']} erreurs")
    
    time.sleep(1)
    
    # Étape 2 : Générer les images initiales (avec prompt_image_1)
    st.info("🎨 Génération des images en cours...")
    
    # Récupérer les items avec leurs prompts
    carousel_data = get_carousel_eco_items()
    
    if carousel_data["status"] == "success" and carousel_data["count"] > 0:
        success_images = 0
        error_images = 0
        
        for item in carousel_data["items"]:
            position = item["position"]
            prompt_image_1 = item.get("prompt_image_1")
            
            if prompt_image_1:
                # Générer et sauvegarder l'image
                img_result = generate_and_save_carousel_image(prompt_image_1, position)
                
                if img_result["status"] == "success":
                    success_images += 1
                else:
                    error_images += 1
        
        # Afficher résultat images
        if error_images == 0:
            st.success(f"✅ {success_images} images générées")
        else:
            st.warning(f"⚠️ {success_images}/{success_images + error_images} images générées")
    
    # Nettoyer le session_state pour forcer le rechargement des valeurs de la DB
    keys_to_delete = [key for key in st.session_state.keys() if key.startswith("title_carou_") or key.startswith("content_carou_")]
    for key in keys_to_delete:
        del st.session_state[key]
    
    # Incrémenter un compteur pour forcer le rechargement des inputs
    if "carousel_generation_count" not in st.session_state:
        st.session_state.carousel_generation_count = 0
    st.session_state.carousel_generation_count += 1
    
    # Attendre pour que l'utilisateur puisse voir les messages, puis refresh
    time.sleep(2)
    st.rerun()


def get_item_position(item_id):
    """Retourne la position d'un item (1-8) ou None si non sélectionné"""
    # Sécurité : initialiser si absent
    if "eco_selected_items" not in st.session_state:
        st.session_state.eco_selected_items = []
    
    if item_id in st.session_state.eco_selected_items:
        return st.session_state.eco_selected_items.index(item_id) + 1
    return None


def set_item_position(item_id, target_position):
    """Modifie la position d'un item sélectionné"""
    # Sécurité : initialiser si absent
    if "eco_selected_items" not in st.session_state:
        st.session_state.eco_selected_items = []
    
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
                    # Initialiser la génération
                    st.session_state.generation_step = "insert"
                    st.session_state.generation_current_idx = 0
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
    
    # Initialiser le compteur de génération si nécessaire
    if "carousel_generation_count" not in st.session_state:
        st.session_state.carousel_generation_count = 0
    
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
            # st.write(f"DEBUG - title_carou: '{title_carou}', content_carou: '{content_carou}'")
            
            # Header de l'item (plus compact)
            st.markdown(f"**#{position}** · {title_original[:50]}...")
            
            # Titre carousel
            col_title_input, col_title_save = st.columns([5, 0.3])
            
            with col_title_input:
                # Utiliser une clé unique avec compteur pour forcer le rechargement après génération
                input_key = f"title_carou_{item_id}_v{st.session_state.carousel_generation_count}"
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
            col_content_input, col_content_save = st.columns([5, 0.3])
            
            with col_content_input:
                # Utiliser une clé unique avec compteur pour forcer le rechargement après génération
                content_key = f"content_carou_{item_id}_v{st.session_state.carousel_generation_count}"
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
            
            # ======================================================
            # SECTION GÉNÉRATION D'IMAGE
            # ======================================================
            
            st.markdown("---")
            st.markdown("**🎨 Image Carousel**")
            
            # Récupérer les prompts depuis la DB
            prompt_image_1 = item.get("prompt_image_1") or ""
            prompt_image_2 = item.get("prompt_image_2") or ""
            prompt_image_3 = item.get("prompt_image_3") or ""
            
            # Vérifier si une image existe déjà
            existing_image = read_carousel_image(position)
            
            # Initialiser le state pour cette image si nécessaire
            if f"image_generating_{item_id}" not in st.session_state:
                st.session_state[f"image_generating_{item_id}"] = False
            
            # Preview de l'image
            col_preview_left, col_preview_center, col_preview_right = st.columns([1, 2, 1])
            
            with col_preview_center:
                if st.session_state.get(f"image_generating_{item_id}", False):
                    st.info("🎨 Génération en cours...")
                elif existing_image:
                    st.image(existing_image, caption=f"Image #{position}", use_container_width=True)
                else:
                    st.caption("Aucune image générée")
            
            st.markdown("")
            
            # Contrôles (3 colonnes)
            col_regen, col_manual, col_upload = st.columns(3)
            
            # Bouton 1 : Régénérer avec prompt_image_2 (studio sombre)
            with col_regen:
                if st.button("🔄 Régénérer", key=f"regen_{item_id}", use_container_width=True, type="secondary", disabled=not prompt_image_2):
                    if prompt_image_2:
                        st.session_state[f"image_generating_{item_id}"] = True
                        st.rerun()
            
            # Bouton 2 : Input manuel + génération
            with col_manual:
                manual_input_key = f"manual_input_{item_id}"
                if manual_input_key not in st.session_state:
                    st.session_state[manual_input_key] = ""
                
                # Afficher l'input dans un expander compact
                with st.expander("✨ Prompter", expanded=False):
                    manual_instructions = st.text_area(
                        label="Instructions manuelles",
                        placeholder="Ex: Ajouter un drapeau européen en fond",
                        key=f"manual_text_{item_id}",
                        height=60
                    )
                    
                    if st.button("Générer", key=f"gen_manual_{item_id}", use_container_width=True, type="primary"):
                        if manual_instructions.strip():
                            st.session_state[f"manual_instructions_{item_id}"] = manual_instructions
                            st.session_state[f"image_generating_manual_{item_id}"] = True
                            st.rerun()
                        else:
                            st.warning("Entrez des instructions")
            
            # Bouton 3 : Upload manuel
            with col_upload:
                uploaded_file = st.file_uploader(
                    label="📁 Charger",
                    type=["png", "jpg", "jpeg"],
                    key=f"upload_{item_id}",
                    label_visibility="collapsed"
                )
                
                if uploaded_file is not None:
                    # Sauvegarder l'image uploadée
                    image_bytes = uploaded_file.read()
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    
                    save_result = save_image_base64(image_base64, position)
                    if save_result["status"] == "success":
                        st.success("✅ Image chargée")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(save_result["message"])
            
            # Logique de génération (traitement async)
            if st.session_state.get(f"image_generating_{item_id}", False):
                with st.spinner("Génération (Nano Banana Pro)..."):
                    result = generate_and_save_carousel_image(prompt_image_2, position)
                
                st.session_state[f"image_generating_{item_id}"] = False
                
                if result["status"] == "success":
                    if result.get("tried_fallback"):
                        st.success("✅ Image générée (GPT Image 1.5)")
                    else:
                        st.success("✅ Image générée (Nano Banana Pro)")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result.get("message", "Erreur"))
            
            # Logique de génération manuelle
            if st.session_state.get(f"image_generating_manual_{item_id}", False):
                manual_instructions = st.session_state.get(f"manual_instructions_{item_id}", "")
                
                with st.spinner("Génération du prompt personnalisé..."):
                    # Générer prompt_image_3
                    prompt_result = generate_prompt_image_3(title_original, item.get("content", ""), manual_instructions)
                
                if prompt_result["status"] == "success":
                    # Sauvegarder prompt_image_3 en DB
                    save_prompt_image_3_to_db(item_id, prompt_result["image_prompt"])
                    
                    # Générer l'image
                    with st.spinner("Génération de l'image (Nano Banana Pro)..."):
                        result = generate_and_save_carousel_image(prompt_result["image_prompt"], position)
                    
                    st.session_state[f"image_generating_manual_{item_id}"] = False
                    
                    if result["status"] == "success":
                        if result.get("tried_fallback"):
                            st.success("✅ Image générée (GPT Image 1.5)")
                        else:
                            st.success("✅ Image générée (Nano Banana Pro)")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result.get("message", "Erreur"))
                else:
                    st.session_state[f"image_generating_manual_{item_id}"] = False
                    st.error(prompt_result.get("message", "Erreur génération prompt"))
            
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


# ======================================================
# TEST GÉNÉRATION D'IMAGE
# ======================================================

with st.expander("🎨 Test Image", expanded=False):
    st.caption("Génération d'image : Nano Banana Pro (2 retries) → Fallback GPT Image 1.5 (OpenAI state-of-the-art)")
    st.markdown("")
    
    # Zone de prompt
    image_prompt = st.text_area(
        label="Prompt de génération",
        placeholder="Ex: A minimalist financial graph showing market trends, blue and white colors, modern design",
        height=100,
        key="test_image_prompt"
    )
    
    # Bouton générer
    col_gen, col_spacer = st.columns([1, 3])
    
    with col_gen:
        if st.button("🎨 Générer", type="primary", use_container_width=True):
            if image_prompt.strip():
                # Afficher la progression avec les deux tentatives possibles
                progress_placeholder = st.empty()
                
                with progress_placeholder.container():
                    st.info("🎨 Génération en cours (Nano Banana Pro)...")
                
                result = generate_carousel_image(image_prompt)
                
                if result["status"] == "success":
                    progress_placeholder.empty()
                    st.session_state.test_image_result = result
                    
                    # Afficher le modèle utilisé
                    model_used = result.get("model_used", "")
                    if result.get("tried_fallback"):
                        st.warning(f"✅ Image générée avec GPT Image 1.5 (fallback)")
                    else:
                        st.success(f"✅ Image générée avec Nano Banana Pro")
                    st.rerun()
                else:
                    progress_placeholder.empty()
                    st.error(result.get('message', 'Erreur inconnue'))
            else:
                st.warning("Entrez un prompt")
    
    # Affichage de l'image générée
    if "test_image_result" in st.session_state and st.session_state.test_image_result:
        st.markdown("---")
        st.markdown("#### Image générée")
        
        result = st.session_state.test_image_result
        
        # Créer des colonnes pour limiter la taille de l'image (format vignette)
        col_left, col_image, col_right = st.columns([1, 2, 1])
        
        with col_image:
            if result.get("image_data"):
                # Décoder et afficher l'image base64
                try:
                    image_bytes = base64.b64decode(result["image_data"])
                    # Afficher le modèle et la résolution utilisés
                    model_used = result.get("model_used", "")
                    resolution = result.get("resolution", "1024x1024")
                    
                    if "gpt-image" in model_used.lower():
                        caption = f"🎨 GPT Image 1.5 (OpenAI state-of-the-art) · {resolution}"
                    else:
                        caption = f"✨ Nano Banana Pro (Gemini 3 Pro) · {resolution}"
                    
                    st.image(image_bytes, caption=caption, use_container_width=True)
                except Exception as e:
                    st.error(f"Erreur d'affichage : {str(e)}")
            elif result.get("image_url"):
                # Afficher l'image depuis l'URL
                st.image(result["image_url"], caption="Image générée", use_container_width=True)
        
        # Bouton pour réinitialiser
        col_clear_left, col_clear_btn, col_clear_right = st.columns([1, 2, 1])
        with col_clear_btn:
            if st.button("🗑️ Effacer", key="clear_test_image", use_container_width=True):
                del st.session_state.test_image_result
                st.rerun()


# ======================================================
# GÉNÉRATION AUTOMATIQUE (STATE MACHINE)
# ======================================================

# Si une génération est en cours, continuer le process
# Cette vérification est placée à la FIN pour permettre l'affichage des expanders
if "generation_step" in st.session_state:
    # Sécurité : compteur pour éviter boucle infinie
    if "generation_loop_count" not in st.session_state:
        st.session_state.generation_loop_count = 0
    
    st.session_state.generation_loop_count += 1
    
    # Si plus de 50 iterations, forcer l'arrêt
    if st.session_state.generation_loop_count > 50:
        st.error("⛔ Arrêt forcé : trop d'itérations")
        del st.session_state.generation_step
        del st.session_state.generation_current_idx
        st.session_state.generation_loop_count = 0
    else:
        send_to_carousel()
