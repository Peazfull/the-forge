import streamlit as st
import time
import base64
import os
import hashlib
from urllib.parse import urlparse, parse_qs
from db.supabase_client import get_supabase
from services.carousel.carousel_eco_service import insert_items_to_carousel_eco, get_carousel_eco_items, upsert_carousel_eco_cover
from services.carousel.generate_carousel_texts_service import generate_all_carousel_texts, update_carousel_text
from services.carousel.image_generation_service import generate_carousel_image
from services.carousel.carousel_image_service import (
    generate_and_save_carousel_image,
    generate_prompt_image_3,
    save_prompt_image_3_to_db,
    read_carousel_image,
    save_image_base64
)
from services.carousel.image_generation_service import save_image_to_carousel
from services.carousel.carousel_slide_service import generate_carousel_slide, generate_cover_slide

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
# DEBUG LOGS + RESET VERROU
# ======================================================
col_debug, col_reset = st.columns([4, 1])

with col_reset:
    if st.session_state.get("generation_in_progress", False):
        st.error("⚠️ Verrou bloqué")
        if st.button("🔓 Débloquer", type="primary"):
            st.session_state.generation_in_progress = False
            st.session_state.generation_active = False
            st.session_state.generation_queue = []
            st.success("✅ Débloqué")
            st.rerun()

with col_debug:
    pass

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


def get_model_from_image_url(image_url: str) -> str:
    """Extrait le modèle depuis l'URL (?model=...)."""
    if not image_url:
        return ""
    try:
        query = parse_qs(urlparse(image_url).query)
        return query.get("model", [""])[0]
    except Exception:
        return ""


def model_to_tag(model_name: str) -> str:
    """Convertit un nom modèle en tag standard pour l'URL."""
    if not model_name:
        return ""
    name = model_name.lower()
    if "gemini" in name or "nano" in name:
        return "gemini"
    if "gpt-image" in name:
        return "gpt-image-1.5"
    if "upload-manuel" in name:
        return "upload-manuel"
    return "unknown"


def generate_all_slide_previews():
    """Génère toutes les slides et les met en cache session_state."""
    carousel_data = get_carousel_eco_items()
    if carousel_data["status"] != "success" or carousel_data["count"] == 0:
        return {"status": "error", "message": "Aucun item"}
    
    if "slide_previews" not in st.session_state:
        st.session_state.slide_previews = {}
    
    errors = 0
    items_sorted = sorted(
        carousel_data["items"],
        key=lambda i: (0 if i.get("position") == 0 else 1, i.get("position", 999))
    )
    
    for item in items_sorted:
        item_id = item["id"]
        position = item["position"]
        title_carou = item.get("title_carou") or ""
        content_carou = item.get("content_carou") or ""
        image_url = item.get("image_url")
        image_bytes = None if image_url else read_carousel_image(position)
        
        if position == 0 and (not image_url and not image_bytes):
            errors += 1
            continue
        if position != 0 and (not title_carou or not content_carou or (not image_url and not image_bytes)):
            errors += 1
            continue
        
        if position == 0:
            hash_input = f"cover|{image_url or ''}|{len(image_bytes) if image_bytes else 0}"
        else:
            hash_input = f"{title_carou}|{content_carou}|{image_url or ''}|{len(image_bytes) if image_bytes else 0}"
        cache_key = hashlib.md5(hash_input.encode("utf-8")).hexdigest()
        
        try:
            if position == 0:
                slide_bytes = generate_cover_slide(
                    image_url=image_url,
                    image_bytes=image_bytes
                )
            else:
                slide_bytes = generate_carousel_slide(
                    title=title_carou.upper(),
                    content=content_carou,
                    image_url=image_url,
                    image_bytes=image_bytes
                )
            st.session_state.slide_previews[item_id] = {
                "key": cache_key,
                "bytes": slide_bytes
            }
        except Exception:
            errors += 1
    
    return {"status": "success", "errors": errors}


def send_to_carousel():
    """Démarre une génération robuste via file d'attente (1 item par run)."""
    # Initialiser les logs de debug
    if "debug_logs" not in st.session_state:
        st.session_state.debug_logs = []
    st.session_state.debug_logs = []  # Reset
    st.session_state.debug_logs.append("🚀 Début send_to_carousel()")
    
    # SÉCURITÉ : éviter double exécution
    if st.session_state.get("generation_in_progress", False):
        st.session_state.debug_logs.append("⚠️ Génération déjà en cours, arrêt")
        return
    
    # Sécurité : initialiser si absent
    if "eco_selected_items" not in st.session_state:
        st.session_state.eco_selected_items = []
    
    st.session_state.debug_logs.append(f"📊 Items sélectionnés : {len(st.session_state.eco_selected_items)}")
    
    # Étape 1 : Insertion
    st.session_state.debug_logs.append("📤 Début insertion en DB...")
    result = insert_items_to_carousel_eco(st.session_state.eco_selected_items)
        
    if result["status"] != "success":
        st.session_state.debug_logs.append(f"❌ Erreur insertion : {result.get('message', 'inconnue')}")
        return
    
    st.session_state.debug_logs.append(f"✅ Insertion OK : {result.get('inserted', 0)} items")
    
    # Étape 2 : Récupérer les items insérés
    st.session_state.debug_logs.append("📥 Récupération items depuis DB...")
    carousel_data = get_carousel_eco_items()
    
    if carousel_data["status"] != "success" or carousel_data["count"] == 0:
        st.session_state.debug_logs.append("❌ Erreur récupération ou 0 items")
        return
    
    items = carousel_data["items"]
    total_items = len(items)
    
    st.session_state.debug_logs.append(f"✅ Récupérés : {total_items} items")
    st.session_state.debug_logs.append(f"📋 IDs : {[item['id'] for item in items]}")
    st.session_state.debug_logs.append(f"📋 Positions : {[item['position'] for item in items]}")
    
    # Initialiser la file d'attente
    st.session_state.generation_in_progress = True
    st.session_state.generation_active = True
    # Ajouter une pseudo-tâche cover à la fin (basée sur l'item #1)
    cover_task = {"is_cover": True, "source_item": items[0]} if items else None
    queue = items + ([cover_task] if cover_task else [])
    
    st.session_state.generation_queue = queue
    st.session_state.generation_total = len(queue)
    st.session_state.generation_done = 0
    st.session_state.generation_errors = []
    st.session_state.debug_logs.append("🔒 Verrou activé + file d'attente initialisée")


def _finalize_generation():
    """Nettoie la génération et reset l'état UI."""
    # Reset sélection
    st.session_state.eco_selected_items = []
    st.session_state.eco_initialized = False
    st.session_state.eco_preview_mode = False
    st.session_state.debug_logs.append("🧹 Reset sélection")
    
    # Incrémenter compteur pour refresh des inputs
    if "carousel_generation_count" not in st.session_state:
        st.session_state.carousel_generation_count = 0
    st.session_state.carousel_generation_count += 1
    st.session_state.debug_logs.append(f"🔢 Compteur incrémenté : {st.session_state.carousel_generation_count}")
    
    # Libérer verrous
    st.session_state.generation_in_progress = False
    st.session_state.generation_active = False
    st.session_state.debug_logs.append("🔓 Verrou libéré")
    
    # Demander un rerun après la génération
    st.session_state.should_rerun_after_generation = True
    st.session_state.debug_logs.append("🔄 Rerun demandé")
    st.session_state.debug_logs.append("✅ Fin send_to_carousel()")


def process_generation_queue():
    """Traite un item par run pour éviter le freeze/timeout."""
    if not st.session_state.get("generation_active", False):
        return
    
    queue = st.session_state.get("generation_queue", [])
    
    if not queue:
        st.session_state.debug_logs.append("🔚 File d'attente vide")
        _finalize_generation()
        return
    
    # Prendre le prochain item
    item = queue.pop(0)
    st.session_state.generation_queue = queue
    
    # Import des fonctions
    from services.carousel.generate_carousel_texts_service import generate_carousel_text_for_item, generate_image_prompt_for_item
    supabase = get_supabase()
    
    # Traitement cover (position 0)
    if item.get("is_cover"):
        source = item.get("source_item") or {}
        source_title = source.get("title", "")
        source_content = source.get("content", "")
        
        st.session_state.debug_logs.append("━━━ SLIDE DE COUVERTURE (position 0) ━━━")
        st.session_state.debug_logs.append(f"  Source: {source_title[:40]}...")
        
        try:
            cover_upsert = upsert_carousel_eco_cover(source)
            if cover_upsert.get("status") != "success":
                raise Exception(cover_upsert.get("message", "Erreur cover DB"))
            cover_id = cover_upsert.get("id")
            
            prompt_result = generate_image_prompt_for_item(source_title, source_content, prompt_type="sunset")
            if prompt_result.get("status") != "success":
                raise Exception(prompt_result.get("message", "Prompt cover KO"))
            
            supabase.table("carousel_eco").update({
                "prompt_image_1": prompt_result.get("image_prompt")
            }).eq("id", cover_id).execute()
            
            img_result = generate_and_save_carousel_image(prompt_result["image_prompt"], position=0, item_id=cover_id)
            if img_result["status"] == "success":
                model_used = img_result.get("model_used", "inconnu")
                st.session_state.debug_logs.append(f"  ✅ Cover générée ({model_used})")
            else:
                st.session_state.debug_logs.append(f"  ⚠️ Cover échec : {img_result.get('message', '')[:50]}")
        except Exception as e:
            st.session_state.debug_logs.append(f"  ❌ ERREUR cover : {str(e)[:120]}")
            st.session_state.generation_errors.append({
                "id": "cover",
                "position": 0,
                "error": str(e)[:200]
            })
        
        st.session_state.generation_done = st.session_state.get("generation_done", 0) + 1
        return
    
    item_id = item["id"]
    position = item["position"]
    title = item.get("title", "")
    content = item.get("content", "")
    total_items = st.session_state.get("generation_total", 0)
    current_idx = st.session_state.get("generation_done", 0) + 1
    
    st.session_state.debug_logs.append(f"━━━ ITEM #{position} (iteration {current_idx}/{total_items}) ━━━")
    st.session_state.debug_logs.append(f"  ID: {item_id}")
    st.session_state.debug_logs.append(f"  Titre: {title[:40]}...")
    
    try:
        # Générer textes
        st.session_state.debug_logs.append("  ⏳ Génération textes...")
        text_result = generate_carousel_text_for_item(title, content)
        
        if text_result.get("status") != "success":
            raise Exception(f"Génération textes KO: {text_result.get('message', '')[:100]}")
        
        st.session_state.debug_logs.append("  ✅ Textes générés")
        
        # Générer prompts images
        st.session_state.debug_logs.append("  ⏳ Génération prompts images...")
        prompt_1_result = generate_image_prompt_for_item(title, content, prompt_type="sunset")
        prompt_2_result = generate_image_prompt_for_item(title, content, prompt_type="studio")
        st.session_state.debug_logs.append("  ✅ Prompts images générés")
        
        # Sauvegarder en DB
        st.session_state.debug_logs.append("  💾 Sauvegarde en DB...")
        supabase.table("carousel_eco").update({
            "title_carou": text_result["title_carou"],
            "content_carou": text_result["content_carou"],
            "prompt_image_1": prompt_1_result.get("image_prompt"),
            "prompt_image_2": prompt_2_result.get("image_prompt")
        }).eq("id", item_id).execute()
        st.session_state.debug_logs.append("  ✅ Sauvegarde DB OK")
        
        # Générer image
        if prompt_1_result.get("status") == "success":
            st.session_state.debug_logs.append("  🎨 Génération image...")
            img_result = generate_and_save_carousel_image(prompt_1_result["image_prompt"], position, item_id=item_id)
            
            if img_result["status"] == "success":
                model_used = img_result.get("model_used", "inconnu")
                st.session_state.debug_logs.append(f"  ✅ Image générée ({model_used})")
                if img_result.get("tried_fallback"):
                    st.session_state.debug_logs.append("  📌 Source modèle: GPT Image 1.5 (fallback)")
                else:
                    st.session_state.debug_logs.append("  📌 Source modèle: Nano Banana Pro (Gemini)")
                if img_result.get("tried_fallback"):
                    gemini_settings = img_result.get("gemini_settings") or {}
                    timeout = gemini_settings.get("timeout", "n/a")
                    retries = gemini_settings.get("max_retries", "n/a")
                    st.session_state.debug_logs.append(
                        f"  ⚠️ Fallback GPT Image 1.5 (timeout Gemini: {timeout}s, retries: {retries})"
                    )
                # Stocker le modèle utilisé pour affichage
                if "carousel_image_models" not in st.session_state:
                    st.session_state.carousel_image_models = {}
                st.session_state.carousel_image_models[position] = {
                    "model": model_used,
                    "tried_fallback": img_result.get("tried_fallback", False)
                }
            else:
                st.session_state.debug_logs.append(f"  ⚠️ Image échec : {img_result.get('message', '')[:50]}")
        else:
            st.session_state.debug_logs.append("  ⚠️ Pas de prompt image valide")
        
        st.session_state.debug_logs.append(f"  ✔️ Item #{position} terminé")
    
    except Exception as e:
        st.session_state.debug_logs.append(f"  ❌ ERREUR : {str(e)[:120]}")
        st.session_state.generation_errors.append({
            "id": item_id,
            "position": position,
            "error": str(e)[:200]
        })
    
    # Incrémenter le compteur de traitement
    st.session_state.generation_done = st.session_state.get("generation_done", 0) + 1
    
    # Si fin de file, finaliser
    if not st.session_state.generation_queue:
        st.session_state.debug_logs.append("🔚 Fin de la file - tous les items traités")
        _finalize_generation()


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
        fallback_images = 0
        
        for item in carousel_data["items"]:
            position = item["position"]
            prompt_image_1 = item.get("prompt_image_1")
            
            if prompt_image_1:
                # Générer et sauvegarder l'image
                img_result = generate_and_save_carousel_image(prompt_image_1, position, item_id=item.get("id"))
                
                if img_result["status"] == "success":
                    success_images += 1
                    st.session_state.debug_logs.append(
                        f"  ✅ Image générée ({img_result.get('model_used', 'inconnu')})"
                    )
                    if img_result.get("tried_fallback"):
                        fallback_images += 1
                        st.session_state.debug_logs.append("  📌 Source modèle: GPT Image 1.5 (fallback)")
                else:
                    error_images += 1
                    st.session_state.debug_logs.append(f"  ⚠️ Image échec : {img_result.get('message', '')[:50]}")
        
        # Afficher résultat images
        if error_images == 0:
            st.success(f"✅ {success_images} images générées")
        else:
            st.warning(f"⚠️ {success_images}/{success_images + error_images} images générées")
        
        if fallback_images > 0:
            st.info(f"ℹ️ {fallback_images} images générées via fallback GPT Image 1.5")
    
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
    
    if target_idx == current_idx:
        return
    
    # Si la position cible est déjà prise, on swap
    if 0 <= target_idx < len(st.session_state.eco_selected_items):
        other_item_id = st.session_state.eco_selected_items[target_idx]
        st.session_state.eco_selected_items[target_idx] = item_id
        st.session_state.eco_selected_items[current_idx] = other_item_id
        return
    
    # Sinon, on réinsère (fallback)
    item = st.session_state.eco_selected_items.pop(current_idx)
    st.session_state.eco_selected_items.insert(target_idx, item)


def move_item_up(item_id):
    """Monte un item d'une position"""
    if "eco_selected_items" not in st.session_state:
        st.session_state.eco_selected_items = []
    if item_id not in st.session_state.eco_selected_items:
        return
    idx = st.session_state.eco_selected_items.index(item_id)
    if idx == 0:
        return
    st.session_state.eco_selected_items[idx], st.session_state.eco_selected_items[idx - 1] = (
        st.session_state.eco_selected_items[idx - 1],
        st.session_state.eco_selected_items[idx],
    )


def move_item_down(item_id):
    """Descend un item d'une position"""
    if "eco_selected_items" not in st.session_state:
        st.session_state.eco_selected_items = []
    if item_id not in st.session_state.eco_selected_items:
        return
    idx = st.session_state.eco_selected_items.index(item_id)
    if idx >= len(st.session_state.eco_selected_items) - 1:
        return
    st.session_state.eco_selected_items[idx], st.session_state.eco_selected_items[idx + 1] = (
        st.session_state.eco_selected_items[idx + 1],
        st.session_state.eco_selected_items[idx],
    )


# ======================================================
# GESTION GÉNÉRATION (AVANT TOUT AFFICHAGE)
# ======================================================
# Si le bouton "Envoyer" a été cliqué, exécuter la génération AVANT de render le reste
if st.session_state.get("trigger_generation", False):
    st.session_state.trigger_generation = False  # Reset le flag immédiatement
    
    # Reset logs au moment du clic
    if "debug_logs" not in st.session_state:
        st.session_state.debug_logs = []
    st.session_state.debug_logs = []
    st.session_state.debug_logs.append("🚀 Nouvelle demande de génération")
    
    # Si une génération est déjà en cours, ne pas relancer
    if st.session_state.get("generation_in_progress", False):
        st.session_state.debug_logs.append("⚠️ Génération déjà en cours, nouvelle demande ignorée")
        st.warning("Une génération est déjà en cours. Attends la fin avant de relancer.")
        st.rerun()
    
    # Initialiser la génération (file d'attente)
    with st.spinner("🔄 Initialisation de la génération..."):
        send_to_carousel()
    
    st.rerun()


# Traitement séquentiel (1 item par run)
if st.session_state.get("generation_active", False):
    with st.spinner("⚙️ Génération en cours (item par item)..."):
        process_generation_queue()
    
    # Continuer tant qu'il reste des items
    if st.session_state.get("generation_active", False):
        st.rerun()
    elif st.session_state.get("should_rerun_after_generation", False):
        st.session_state.should_rerun_after_generation = False
        st.rerun()


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
        
        # Nettoyer la sélection si des items ne sont plus dans le top courant
        allowed_ids = {item["id"] for item in items}
        if "eco_selected_items" in st.session_state:
            st.session_state.eco_selected_items = [
                item_id for item_id in st.session_state.eco_selected_items
                if item_id in allowed_ids
            ]
        
        # Header
        selected_count = len(st.session_state.eco_selected_items)
        
        col_header, col_preview_btn = st.columns([3, 1])
        with col_header:
            st.caption(f"Top 14 · **{selected_count}** sélectionnée{'s' if selected_count > 1 else ''}")
            if selected_count > 1 and not st.session_state.eco_preview_mode:
                st.caption("Astuce: changer une position fait un échange automatique (pas de doublons).")
        
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
        
        # Zone UX d'ordre (instantané)
        if selected_count > 0:
            st.markdown("#### Ordre sélectionné")
            st.caption("Réorganisez avec ↑ / ↓ (pas de doublons, instantané).")
            items_dict = {item["id"]: item for item in items}
            
            for idx, item_id in enumerate(st.session_state.eco_selected_items, start=1):
                item = items_dict.get(item_id, {})
                title = item.get("title", "Sans titre")
                title_short = title[:55] + "..." if len(title) > 55 else title
                
                col_pos, col_title, col_up, col_down, col_remove = st.columns([0.6, 4, 0.6, 0.6, 0.6])
                
                with col_pos:
                    st.markdown(f"**#{idx}**")
                with col_title:
                    st.caption(title_short)
                with col_up:
                    if st.button("↑", key=f"move_up_{item_id}", disabled=idx == 1):
                        move_item_up(item_id)
                        st.rerun()
                with col_down:
                    if st.button("↓", key=f"move_down_{item_id}", disabled=idx == selected_count):
                        move_item_down(item_id)
                        st.rerun()
                with col_remove:
                    if st.button("✖", key=f"remove_{item_id}"):
                        toggle_selection(item_id)
                        st.rerun()
            
            st.markdown("---")
        
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
                # Affichage simple de la position (ordre géré dans la zone dédiée)
                current_position = get_item_position(item_id)
                if is_selected:
                    st.markdown(f"**#{current_position}**")
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
                    use_container_width=True,
                    key="send_button"
                ):
                    # Activer le flag pour déclencher la génération
                    st.session_state.trigger_generation = True
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
# DEBUG LOGS (APRES BULLETIN)
# ======================================================
if "debug_logs" in st.session_state and st.session_state.debug_logs:
    with st.expander("🐛 Debug Logs (voir ce qui s'est passé)", expanded=True):
        st.code("\n".join(st.session_state.debug_logs), language="text")
        
        if st.button("🗑️ Effacer les logs"):
            st.session_state.debug_logs = []
            st.rerun()


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
                title_len = len(title_carou)
                new_title_carou = st.text_input(
                    label=f"Titre (3 mots max) · {len(title_carou)}/50 caractères",
                    value=title_carou,
                    key=input_key,
                    placeholder="Ex: FED : CHOC HISTORIQUE"
                )
            
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
                content_len = len(content_carou)
                new_content_carou = st.text_area(
                    label=f"Content (3 phrases max) · {len(content_carou)}/300 caractères",
                    value=content_carou,
                    key=content_key,
                    placeholder="Ex: La banque centrale frappe fort. Les marchés explosent.",
                    height=70
                )
            
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
            existing_image_url = item.get("image_url")
            
            # Layout : Image à gauche (petite), Contrôles à droite (empilés)
            col_image, col_controls = st.columns([1, 2])
            
            # COLONNE GAUCHE : Preview de l'image (petite)
            with col_image:
                if existing_image_url:
                    st.image(existing_image_url, caption=f"Image #{position}", use_container_width=True)
                elif existing_image:
                    st.image(existing_image, caption=f"Image #{position}", use_container_width=True)
                else:
                    st.caption("Aucune image générée")
                
                # Afficher le modèle utilisé (session_state ou URL)
                model_name = ""
                tried_fallback = False
                if "carousel_image_models" in st.session_state:
                    model_info = st.session_state.carousel_image_models.get(position)
                    if model_info:
                        model_name = model_info.get("model", "")
                        tried_fallback = model_info.get("tried_fallback", False)
                
                # Si on a seulement le flag fallback, déduire la source
                if not model_name and tried_fallback:
                    model_name = "gpt-image-1.5"
                elif not model_name and existing_image and not tried_fallback:
                    model_name = "gemini"
                
                if not model_name and existing_image_url:
                    model_name = get_model_from_image_url(existing_image_url)
                
                # Si URL sans modèle mais session_state en a un, persister en DB
                if existing_image_url and not get_model_from_image_url(existing_image_url) and model_name:
                    model_tag = model_to_tag(model_name)
                    if model_tag:
                        image_url = f"{existing_image_url.split('?')[0]}?model={model_tag}"
                        save_image_to_carousel(item_id, image_url)
                        existing_image_url = image_url
                
                if model_name:
                    # Afficher avec émoji et couleur selon le modèle
                    if model_name == "upload-manuel":
                        st.caption("📁 Upload manuel")
                    elif "gemini" in model_name.lower() or "nano" in model_name.lower():
                        st.caption("🟢 Nano Banana Pro (Gemini)")
                    elif "gpt-image" in model_name.lower():
                        if tried_fallback:
                            st.caption("🟡 GPT Image 1.5 (fallback)")
                        else:
                            st.caption("🔵 GPT Image 1.5")
                    else:
                        st.caption(f"⚪ {model_name}")
                elif existing_image_url or existing_image:
                    st.caption("⚪ Modèle inconnu")
            
            # COLONNE DROITE : Contrôles empilés verticalement
            with col_controls:
            
                # Bouton 1 : Régénérer avec prompt_image_2 (studio sombre)
                if st.button("🔄 Régénérer", key=f"regen_{item_id}", use_container_width=True, type="secondary", disabled=not prompt_image_2):
                    if prompt_image_2:
                        with st.spinner("🎨 Génération..."):
                            result = generate_and_save_carousel_image(prompt_image_2, position, item_id=item_id)
                        
                        if result["status"] == "success":
                            # Stocker le modèle utilisé
                            if "carousel_image_models" not in st.session_state:
                                st.session_state.carousel_image_models = {}
                            st.session_state.carousel_image_models[position] = {
                                "model": result.get("model_used", "inconnu"),
                                "tried_fallback": result.get("tried_fallback", False)
                            }
                            st.success(f"✅ Image régénérée ({result.get('model_used', '?')})")
                            if result.get("tried_fallback"):
                                gemini_settings = result.get("gemini_settings") or {}
                                timeout = gemini_settings.get("timeout", "n/a")
                                retries = gemini_settings.get("max_retries", "n/a")
                                st.info(f"Fallback GPT Image 1.5 (timeout Gemini: {timeout}s, retries: {retries})")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"❌ {result.get('message', 'Erreur')[:100]}")
                
                # Bouton 2 : Input manuel + génération
                with st.expander("✨ Prompter", expanded=False):
                    manual_instructions = st.text_area(
                        label="Instructions manuelles",
                        placeholder="Ex: Ajouter un drapeau européen en fond",
                        key=f"manual_text_{item_id}",
                        height=60
                    )
                    
                    if st.button("Générer", key=f"gen_manual_{item_id}", use_container_width=True, type="primary"):
                        if manual_instructions.strip():
                            with st.spinner("🎨 Génération du prompt..."):
                                # Générer prompt_image_3
                                prompt_result = generate_prompt_image_3(title_original, item.get("content", ""), manual_instructions)
                            
                            if prompt_result["status"] == "success":
                                # Sauvegarder en DB
                                save_prompt_image_3_to_db(item_id, prompt_result["image_prompt"])
                                
                                # Générer l'image
                                with st.spinner("🎨 Génération de l'image..."):
                                    result = generate_and_save_carousel_image(prompt_result["image_prompt"], position, item_id=item_id)
                                
                                if result["status"] == "success":
                                    # Stocker le modèle utilisé
                                    if "carousel_image_models" not in st.session_state:
                                        st.session_state.carousel_image_models = {}
                                    st.session_state.carousel_image_models[position] = {
                                        "model": result.get("model_used", "inconnu"),
                                        "tried_fallback": result.get("tried_fallback", False)
                                    }
                                    st.success(f"✅ Image générée ({result.get('model_used', '?')})")
                                    if result.get("tried_fallback"):
                                        gemini_settings = result.get("gemini_settings") or {}
                                        timeout = gemini_settings.get("timeout", "n/a")
                                        retries = gemini_settings.get("max_retries", "n/a")
                                        st.info(f"Fallback GPT Image 1.5 (timeout Gemini: {timeout}s, retries: {retries})")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result.get('message', 'Erreur')[:100]}")
                            else:
                                st.error(f"❌ Erreur prompt : {prompt_result.get('message', '')[:100]}")
                        else:
                            st.warning("Entrez des instructions")
                
                # Bouton 3 : Upload manuel
                st.markdown("**📁 Charger une image**")
                
                # Tracking pour éviter retraitement multiple
                upload_key = f"upload_{item_id}"
                last_upload_key = f"last_upload_{item_id}"
                
                uploaded_file = st.file_uploader(
                    label="Upload image",
                    type=["png", "jpg", "jpeg"],
                    key=upload_key,
                    label_visibility="collapsed"
                )
                
                if uploaded_file is not None:
                    # Vérifier si c'est un nouveau fichier (pas déjà traité)
                    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                    last_file_id = st.session_state.get(last_upload_key)
                    
                    if file_id != last_file_id:
                        # Nouveau fichier, traiter
                        # IMPORTANT : Sauvegarder directement les bytes dans session_state
                        # (pas de base64 inutile pour l'affichage)
                        image_bytes = uploaded_file.read()
                        
                        # Stocker en session_state
                        if "carousel_images" not in st.session_state:
                            st.session_state.carousel_images = {}
                        st.session_state.carousel_images[position] = image_bytes
                        
                        # Aussi essayer sur disque (optionnel)
                        try:
                            from services.carousel.carousel_image_service import get_image_path
                            image_path = get_image_path(position)
                            os.makedirs(os.path.dirname(image_path), exist_ok=True)
                            with open(image_path, 'wb') as f:
                                f.write(image_bytes)
                        except:
                            pass  # Échec silencieux
                        
                        # Upload vers Supabase Storage + sauvegarde URL en DB
                        try:
                            from services.carousel.carousel_image_service import upload_image_bytes
                            upload_result = upload_image_bytes(image_bytes, position)
                            if upload_result.get("public_url"):
                                from services.carousel.image_generation_service import save_image_to_carousel
                                image_url = f"{upload_result['public_url']}?model=upload-manuel"
                                save_image_to_carousel(item_id, image_url)
                        except:
                            pass
                        
                        st.session_state[last_upload_key] = file_id
                        
                        # Marquer comme upload manuel
                        if "carousel_image_models" not in st.session_state:
                            st.session_state.carousel_image_models = {}
                        st.session_state.carousel_image_models[position] = {
                            "model": "upload-manuel",
                            "tried_fallback": False
                        }
                        
                        st.success("✅ Image chargée")
                        time.sleep(0.5)
                        st.rerun()
            
            # Plus besoin de logique async avec flags - tout est fait directement dans les boutons

        # Bouton global : générer les previews slides
        st.divider()
        if st.button("🖼️ Générer les slides", type="primary", use_container_width=True):
            with st.spinner("Génération des slides en cours..."):
                result = generate_all_slide_previews()
            if result.get("status") == "success":
                if result.get("errors", 0) == 0:
                    st.success("✅ Slides générées")
                else:
                    st.warning(f"⚠️ Slides générées avec {result.get('errors')} erreurs")
            else:
                st.error("❌ Impossible de générer les slides")
            st.rerun()


# ======================================================
# PREVIEW SLIDES
# ======================================================

with st.expander("🖼️ Preview Slides", expanded=False):
    carousel_data = get_carousel_eco_items()
    
    if carousel_data["status"] == "error":
        st.error(f"Erreur : {carousel_data.get('message', 'Erreur inconnue')}")
    elif carousel_data["count"] == 0:
        st.info("Aucun item · Envoyez d'abord des items depuis 'Bulletin Eco'")
    else:
        if "slide_previews" not in st.session_state:
            st.session_state.slide_previews = {}
        
        items_sorted = sorted(
            carousel_data["items"],
            key=lambda i: (0 if i.get("position") == 0 else 1, i.get("position", 999))
        )
        
        cols = None
        # Ajouter un item "outro" en fin de preview
        items_with_outro = items_sorted + [{"id": "outro", "position": 999}]
        
        for idx, item in enumerate(items_with_outro):
            item_id = item["id"]
            position = item["position"]
            title_carou = item.get("title_carou") or ""
            content_carou = item.get("content_carou") or ""
            image_url = item.get("image_url")
            image_bytes = None if image_url else read_carousel_image(position)
            
            if idx % 3 == 0:
                cols = st.columns(3)
            col = cols[idx % 3]
            
            with col:
                if item_id == "outro":
                    st.markdown("**Slide de fin**")
                elif position == 0:
                    st.markdown("**Slide de couverture (0)**")
                else:
                    st.markdown(f"**Slide #{position}**")
                
                if item_id != "outro":
                    if st.button("🔄 Regénérer slide", key=f"regen_slide_{item_id}", use_container_width=True):
                        st.session_state.slide_previews.pop(item_id, None)
                        st.rerun()
                
                # Empêcher la génération si les champs sont vides
                if item_id == "outro":
                    outro_path = os.path.join(
                        os.path.dirname(__file__),
                        "..", "layout", "assets", "carousel_eco", "outro.png"
                    )
                    if os.path.exists(outro_path):
                        st.image(outro_path, use_container_width=True)
                    else:
                        st.warning("outro.png introuvable")
                    continue
                
                if position == 0 and (not image_url and not image_bytes):
                    st.warning("Il manque l'image pour générer la cover.")
                    continue
                if position != 0 and (not title_carou or not content_carou or (not image_url and not image_bytes)):
                    st.warning("Il manque le titre, le texte ou l'image pour générer la slide.")
                    continue
                
                # Cache preview (key simple basée sur contenu)
                if position == 0:
                    hash_input = f"cover|{image_url or ''}|{len(image_bytes) if image_bytes else 0}"
                else:
                    hash_input = f"{title_carou}|{content_carou}|{image_url or ''}|{len(image_bytes) if image_bytes else 0}"
                cache_key = hashlib.md5(hash_input.encode("utf-8")).hexdigest()
                cached = st.session_state.slide_previews.get(item_id)
                
                if not cached or cached.get("key") != cache_key:
                    try:
                        if position == 0:
                            slide_bytes = generate_cover_slide(
                                image_url=image_url,
                                image_bytes=image_bytes
                            )
                        else:
                            slide_bytes = generate_carousel_slide(
                                title=title_carou.upper(),
                                content=content_carou,
                                image_url=image_url,
                                image_bytes=image_bytes
                            )
                        st.session_state.slide_previews[item_id] = {
                            "key": cache_key,
                            "bytes": slide_bytes
                        }
                    except Exception as e:
                        st.error(f"Erreur génération slide : {str(e)[:120]}")
                        continue
                
                st.image(st.session_state.slide_previews[item_id]["bytes"], use_container_width=True)


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
    st.caption("Génération d'image : Nano Banana Pro (timeout 75s, 0 retry) → Fallback GPT Image 1.5 (OpenAI state-of-the-art)")
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


# Plus besoin de state machine, la génération se fait en une seule passe
