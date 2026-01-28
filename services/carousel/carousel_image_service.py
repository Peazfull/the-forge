"""
Service de génération et sauvegarde d'images pour carousel_eco
Gère la génération avec les 3 types de prompts et la sauvegarde sur disque
"""

import streamlit as st
import os
import base64
from typing import Dict, Optional
from openai import OpenAI
from db.supabase_client import get_supabase
from services.carousel.image_generation_service import generate_carousel_image
from prompts.carousel.generate_image_prompts_manual import PROMPT_GENERATE_IMAGE_PROMPT_MANUAL
import json


REQUEST_TIMEOUT = 60
MAX_RETRIES = 2

# Chemin du dossier de sauvegarde des images
CAROUSEL_IMAGE_DIR = os.path.join(
    os.path.dirname(__file__), 
    "..", "..", 
    "front", "layout", "assets", "carousel_eco"
)


def get_image_path(position: int) -> str:
    """
    Retourne le chemin complet de l'image pour une position donnée
    
    Args:
        position: Position dans le carousel (1-8)
        
    Returns:
        Chemin complet vers imgcaroueco{position}.png
    """
    os.makedirs(CAROUSEL_IMAGE_DIR, exist_ok=True)
    return os.path.join(CAROUSEL_IMAGE_DIR, f"imgcaroueco{position}.png")


def save_image_base64(image_base64: str, position: int) -> Dict[str, object]:
    """
    Sauvegarde une image base64 sur disque
    
    Args:
        image_base64: Image encodée en base64
        position: Position dans le carousel (1-8)
        
    Returns:
        {"status": "success" | "error", "path": str, "message": str}
    """
    try:
        # Décoder le base64
        image_bytes = base64.b64decode(image_base64)
        
        # Sauvegarder
        image_path = get_image_path(position)
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        return {
            "status": "success",
            "path": image_path,
            "message": f"Image sauvegardée : imgcaroueco{position}.png"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "path": None,
            "message": f"Erreur sauvegarde : {str(e)}"
        }


def generate_and_save_carousel_image(prompt: str, position: int) -> Dict[str, object]:
    """
    Génère une image avec un prompt et la sauvegarde sur disque
    
    Args:
        prompt: Le prompt de génération d'image
        position: Position dans le carousel (1-8)
        
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
    # Générer l'image
    result = generate_carousel_image(prompt)
    
    if result["status"] != "success":
        return result
    
    # Sauvegarder sur disque
    save_result = save_image_base64(result["image_data"], position)
    
    if save_result["status"] != "success":
        return {
            "status": "error",
            "message": f"Image générée mais erreur sauvegarde : {save_result['message']}"
        }
    
    # Succès complet
    return {
        "status": "success",
        "image_data": result["image_data"],
        "image_path": save_result["path"],
        "model_used": result.get("model_used", "unknown"),
        "tried_fallback": result.get("tried_fallback", False),
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


def save_prompt_image_3_to_db(item_id: str, prompt_image_3: str) -> Dict[str, object]:
    """
    Sauvegarde le prompt_image_3 en base de données
    
    Args:
        item_id: UUID de l'item dans carousel_eco
        prompt_image_3: Le prompt généré
        
    Returns:
        {"status": "success" | "error", "message": str}
    """
    try:
        supabase = get_supabase()
        
        response = supabase.table("carousel_eco").update({
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
    Lit une image de carousel depuis le disque
    
    Args:
        position: Position dans le carousel (1-8)
        
    Returns:
        Bytes de l'image ou None si inexistante
    """
    try:
        image_path = get_image_path(position)
        
        if not os.path.exists(image_path):
            return None
        
        with open(image_path, 'rb') as f:
            return f.read()
            
    except Exception as e:
        print(f"Erreur lecture image position {position}: {str(e)}")
        return None
