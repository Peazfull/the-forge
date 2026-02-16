"""
Service de génération et sauvegarde d'images pour carousel_bourse
Gère la génération avec les 3 types de prompts et la sauvegarde sur disque
"""

import streamlit as st
import os
import base64
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from openai import OpenAI
from db.supabase_client import get_supabase
from services.carousel.image_generation_service import generate_carousel_image
from prompts.carousel.bourse.generate_image_prompts_manual import PROMPT_GENERATE_IMAGE_PROMPT_MANUAL
import json


REQUEST_TIMEOUT = 60
MAX_RETRIES = 2

# Chemin du dossier de sauvegarde des images
CAROUSEL_IMAGE_DIR = os.path.join(
    os.path.dirname(__file__), 
    "..", "..", "..",
    "front", "layout", "assets", "carousel", "bourse"
)

STORAGE_BUCKET = "carousel-bourse"


def list_image_files():
    """Liste les fichiers présents dans le bucket carousel-bourse."""
    try:
        supabase = get_supabase()
        items = supabase.storage.from_(STORAGE_BUCKET).list()
        return {item['name'] for item in items} if items else set()
    except Exception:
        return set()


def clear_image_files() -> bool:
    """Supprime tous les fichiers du bucket carousel-bourse."""
    try:
        supabase = get_supabase()
        files = list_image_files()
        if not files:
            return True
        supabase.storage.from_(STORAGE_BUCKET).remove(list(files))
        return True
    except Exception:
        return False


def _append_model_to_url(public_url: str, model_tag: str) -> str:
    """Ajoute ?model=... à une URL (ou l'upsert si déjà présent)."""
    if not public_url or not model_tag:
        return public_url
    parts = urlparse(public_url)
    query = parse_qs(parts.query)
    query["model"] = [model_tag]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parts._replace(query=new_query))


def get_image_path(position: int) -> str:
    """
    Retourne le chemin complet de l'image pour une position donnée
    
    Args:
        position: Position dans le carousel (1-10)
        
    Returns:
        Chemin complet vers imgcaroubourse{position}.png
    """
    os.makedirs(CAROUSEL_IMAGE_DIR, exist_ok=True)
    return os.path.join(CAROUSEL_IMAGE_DIR, f"imgcaroubourse{position}.png")


def upload_image_bytes(image_bytes: bytes, position: int) -> Dict[str, object]:
    """
    Upload une image vers Supabase Storage (bucket public).
    """
    try:
        supabase = get_supabase()
        object_path = f"imgcaroubourse{position}.png"
        
        supabase.storage.from_(STORAGE_BUCKET).upload(
            object_path,
            image_bytes,
            file_options={"content-type": "image/png", "upsert": True}
        )
        
        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(object_path)
        return {
            "status": "success",
            "public_url": public_url
        }
    except Exception as e:
        return {
            "status": "error",
            "public_url": None,
            "message": f"Erreur upload storage : {str(e)}"
        }


def save_image_base64(image_base64: str, position: int) -> Dict[str, object]:
    """
    Sauvegarde une image base64 sur disque ET en session_state
    
    Args:
        image_base64: Image encodée en base64
        position: Position dans le carousel (1-10)
        
    Returns:
        {"status": "success" | "error", "path": str, "message": str}
    """
    try:
        # Décoder le base64
        image_bytes = base64.b64decode(image_base64)
        
        # Sauvegarder en session_state (pour affichage immédiat)
        if "carousel_images" not in st.session_state:
            st.session_state.carousel_images = {}
        st.session_state.carousel_images[position] = image_bytes
        
        # Essayer aussi sur disque (mais peut échouer en prod)
        try:
            image_path = get_image_path(position)
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
        except:
            pass  # Échec silencieux si pas de droits d'écriture
        
        # Upload vers Supabase Storage (bucket public)
        upload_result = upload_image_bytes(image_bytes, position)
        
        return {
            "status": "success",
            "path": f"session_state[{position}]",
            "public_url": upload_result.get("public_url"),
            "message": f"Image sauvegardée : imgcaroubourse{position}.png"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "path": None,
            "message": f"Erreur sauvegarde : {str(e)}"
        }


def generate_and_save_carousel_image(prompt: str, position: int, item_id: Optional[str] = None, aspect_ratio: str = "1:1") -> Dict[str, object]:
    """
    Génère une image avec un prompt et la sauvegarde sur disque
    
    Args:
        prompt: Le prompt de génération d'image
        position: Position dans le carousel (1-10)
        item_id: ID de l'item dans la DB (optionnel)
        aspect_ratio: Ratio d'aspect de l'image ("1:1", "5:4", "16:9", "9:16")
        position: Position dans le carousel (1-10)
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": str (base64),
            "image_path": str,
            "model_used": str,
            "tried_fallback": bool,
            "message": str
        }
    """
    # Générer l'image avec l'aspect ratio spécifié
    result = generate_carousel_image(prompt, aspect_ratio=aspect_ratio)
    
    if result["status"] != "success":
        return result
    
    # Sauvegarder sur disque + storage
    save_result = save_image_base64(result["image_data"], position)
    
    if save_result["status"] != "success":
        return {
            "status": "error",
            "message": f"Image générée mais erreur sauvegarde : {save_result['message']}"
        }
    
    # Succès complet
    # Enregistrer l'URL en DB si possible
    image_url = save_result.get("public_url")
    if item_id and image_url:
        model_used = result.get("model_used", "").lower()
        if "gemini" in model_used or "nano" in model_used:
            model_tag = "gemini"
        elif "gpt-image" in model_used:
            model_tag = "gpt-image-1.5"
        else:
            model_tag = "unknown"
        
        image_url = _append_model_to_url(image_url, model_tag)
        save_image_to_bourse(item_id, image_url)
    
    return {
        "status": "success",
        "image_data": result["image_data"],
        "image_path": save_result["path"],
        "image_url": image_url,
        "model_used": result.get("model_used", "unknown"),
        "tried_fallback": result.get("tried_fallback", False),
        "gemini_settings": result.get("gemini_settings"),
        "resolution": result.get("resolution", "1024x1024"),
        "message": "Image générée et sauvegardée"
    }


def generate_prompt_image_3(title: str, content: str, manual_instructions: str) -> Dict[str, object]:
    """
    Génère le prompt_image_3 en combinant base sunset + instructions manuelles
    
    Args:
        title: Titre de l'actualité
        content: Contenu de l'actualité
        manual_instructions: Instructions manuelles de l'utilisateur
        
    Returns:
        {
            "status": "success" | "error",
            "image_prompt": str,
            "message": str
        }
    """
    if not title or not content or not manual_instructions:
        return {
            "status": "error",
            "message": "Titre, contenu ou instructions manquants",
            "image_prompt": None
        }
    
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Construire l'input avec les instructions manuelles
        user_input = f"TITRE: {title}\n\nCONTENT: {content}\n\nINSTRUCTIONS MANUELLES: {manual_instructions}"
        
        # Retry logic
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_GENERATE_IMAGE_PROMPT_MANUAL},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.65,
                    response_format={"type": "json_object"},
                    timeout=REQUEST_TIMEOUT
                )
                
                raw_json = response.choices[0].message.content or ""
                data = json.loads(raw_json)
                
                break
                
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    continue
                else:
                    raise e
        
        # Validation
        if "image_prompt" not in data:
            return {
                "status": "error",
                "message": "Champ image_prompt manquant dans la réponse IA",
                "image_prompt": None
            }
        
        return {
            "status": "success",
            "image_prompt": data["image_prompt"]
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Erreur JSON: {str(e)}",
            "image_prompt": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur: {str(e)}",
            "image_prompt": None
        }


def save_image_to_bourse(item_id: str, image_url: str) -> Dict[str, object]:
    """Sauvegarde l'URL de l'image dans la table carousel_bourse."""
    try:
        supabase = get_supabase()
        supabase.table("carousel_bourse").update({
            "image_url": image_url
        }).eq("id", item_id).execute()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": f"Erreur DB : {str(e)}"}


def save_prompt_image_3_to_db(item_id: str, prompt_image_3: str) -> Dict[str, object]:
    """
    Sauvegarde le prompt_image_3 en base de données
    
    Args:
        item_id: UUID de l'item dans carousel_bourse
        prompt_image_3: Le prompt généré
        
    Returns:
        {"status": "success" | "error", "message": str}
    """
    try:
        supabase = get_supabase()
        
        response = supabase.table("carousel_bourse").update({
            "prompt_image_3": prompt_image_3
        }).eq("id", item_id).execute()
        
        if response.data:
            return {
                "status": "success",
                "message": "Prompt 3 sauvegardé en DB"
            }
        else:
            return {
                "status": "error",
                "message": "Aucune donnée retournée"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur DB: {str(e)}"
        }


def read_carousel_image(position: int) -> Optional[bytes]:
    """
    Lit une image de carousel depuis session_state ou disque
    
    Args:
        position: Position dans le carousel (1-10)
        
    Returns:
        Bytes de l'image ou None si inexistante
    """
    try:
        # D'abord chercher en session_state (priorité)
        if "carousel_images" in st.session_state:
            if position in st.session_state.carousel_images:
                return st.session_state.carousel_images[position]
        
        # Sinon lire depuis le disque
        image_path = get_image_path(position)
        
        if not os.path.exists(image_path):
            return None
        
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            # Mettre en cache dans session_state
            if "carousel_images" not in st.session_state:
                st.session_state.carousel_images = {}
            st.session_state.carousel_images[position] = image_bytes
            return image_bytes
            
    except Exception as e:
        print(f"Erreur lecture image position {position}: {str(e)}")
        return None
