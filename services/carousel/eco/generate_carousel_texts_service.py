import json
import streamlit as st
import time
from openai import OpenAI
from typing import Dict, List
from db.supabase_client import get_supabase
from prompts.carousel.eco.generate_carousel_texts import PROMPT_GENERATE_CAROUSEL_TEXTS
from prompts.carousel.eco.generate_image_prompts import PROMPT_GENERATE_IMAGE_PROMPT
from prompts.carousel.eco.generate_image_prompts_variant import PROMPT_GENERATE_IMAGE_PROMPT_VARIANT
from concurrent.futures import ThreadPoolExecutor, as_completed


REQUEST_TIMEOUT = 30  # Réduit à 30s pour éviter freeze long
MAX_RETRIES = 3  # 3 retries pour gérer le rate limiting
RETRY_DELAY = 10  # Délai entre les retries (secondes)
MAX_WORKERS = 8  # Nombre de threads pour parallélisation


def generate_image_prompt_for_item(title: str, content: str, prompt_type: str = "sunset") -> Dict[str, object]:
    """
    Génère un prompt d'image pour un item via OpenAI.
    
    Args:
        title: Titre original
        content: Contenu original
        prompt_type: Type de prompt ("sunset" pour DA violet/orange ou "studio" pour DA sombre)
    
    Returns:
        {
            "status": "success" | "error",
            "image_prompt": str,
            "message": str (si erreur)
        }
    """
    
    if not title or not content:
        return {
            "status": "error",
            "message": "Titre ou contenu manquant",
            "image_prompt": None
        }
    
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Construire l'input
        user_input = f"TITRE: {title}\n\nCONTENT: {content}"
        
        # Sélectionner le prompt système selon le type
        if prompt_type == "studio":
            system_prompt = PROMPT_GENERATE_IMAGE_PROMPT_VARIANT
            temperature = 0.65
        else:  # "sunset" par défaut
            system_prompt = PROMPT_GENERATE_IMAGE_PROMPT
            temperature = 0.6
        
        # Retry logic avec délai progressif pour gérer le rate limiting
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    timeout=REQUEST_TIMEOUT
                )
                
                raw_json = response.choices[0].message.content or ""
                data = json.loads(raw_json)
                
                break
                
            except Exception as e:
                error_msg = str(e)
                # Si c'est une erreur 429 (rate limit) et qu'il reste des tentatives
                if "429" in error_msg and attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (attempt + 1)  # Délai progressif
                    time.sleep(delay)
                    continue
                elif attempt < MAX_RETRIES - 1:
                    time.sleep(2)  # Petit délai pour les autres erreurs
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


def generate_carousel_text_for_item(title: str, content: str) -> Dict[str, object]:
    """
    Génère le titre et contenu carousel pour un item via OpenAI.
    
    Args:
        title: Titre original
        content: Contenu original
    
    Returns:
        {
            "status": "success" | "error",
            "title_carou": str,
            "content_carou": str,
            "message": str (si erreur)
        }
    """
    
    if not title or not content:
        return {
            "status": "error",
            "message": "Titre ou contenu manquant",
            "title_carou": None,
            "content_carou": None
        }
    
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Construire l'input
        user_input = f"TITRE: {title}\n\nCONTENT: {content}"
        
        # Retry logic avec délai progressif pour gérer le rate limiting
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_GENERATE_CAROUSEL_TEXTS},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7,  # Plus créatif pour le clickbait
                    response_format={"type": "json_object"},
                    timeout=REQUEST_TIMEOUT
                )
                
                raw_json = response.choices[0].message.content or ""
                data = json.loads(raw_json)
                
                break
                
            except Exception as e:
                error_msg = str(e)
                # Si c'est une erreur 429 (rate limit) et qu'il reste des tentatives
                if "429" in error_msg and attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (attempt + 1)  # Délai progressif
                    time.sleep(delay)
                    continue
                elif attempt < MAX_RETRIES - 1:
                    time.sleep(2)  # Petit délai pour les autres erreurs
                    continue
                else:
                    raise e
        
        # Validation
        if "title_carou" not in data or "content_carou" not in data:
            return {
                "status": "error",
                "message": "Champs manquants dans la réponse IA",
                "title_carou": None,
                "content_carou": None
            }
        
        return {
            "status": "success",
            "title_carou": data["title_carou"],
            "content_carou": data["content_carou"]
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Erreur JSON: {str(e)}",
            "title_carou": None,
            "content_carou": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur: {str(e)}",
            "title_carou": None,
            "content_carou": None
        }


def generate_all_carousel_texts() -> Dict[str, object]:
    """
    Génère les textes carousel pour tous les items dans carousel_eco.
    
    Returns:
        {
            "status": "success" | "partial" | "error",
            "total": int,
            "success": int,
            "errors": int,
            "details": [...]
        }
    """
    
    try:
        supabase = get_supabase()
        
        # Récupérer tous les items de carousel_eco (triés par position)
        response = supabase.table("carousel_eco").select(
            "id, position, title, content"
        ).order("position", desc=False).execute()
        
        items = response.data or []
        
        if not items:
            return {
                "status": "error",
                "message": "Aucun item dans carousel_eco",
                "total": 0,
                "success": 0,
                "errors": 0,
                "details": []
            }
        
        total = len(items)
        success_count = 0
        error_count = 0
        details = []
        
        # Générer pour chaque item
        for item in items:
            item_id = item["id"]
            position = item["position"]
            title = item["title"]
            content = item["content"]
            
            # Génération IA - Textes carousel
            result_text = generate_carousel_text_for_item(title, content)
            
            # Génération IA - Prompts d'images (2 variations)
            result_img_1 = generate_image_prompt_for_item(title, content, prompt_type="sunset")
            result_img_2 = generate_image_prompt_for_item(title, content, prompt_type="studio")
            
            # Vérifier si toutes les générations ont réussi
            all_success = (
                result_text["status"] == "success" and 
                result_img_1["status"] == "success" and 
                result_img_2["status"] == "success"
            )
            
            if all_success:
                # Mise à jour en DB
                update_response = supabase.table("carousel_eco").update({
                    "title_carou": result_text["title_carou"],
                    "content_carou": result_text["content_carou"],
                    "prompt_image_1": result_img_1["image_prompt"],
                    "prompt_image_2": result_img_2["image_prompt"]
                }).eq("id", item_id).execute()
                
                if update_response.data:
                    success_count += 1
                    details.append({
                        "position": position,
                        "status": "success",
                        "title_carou": result_text["title_carou"]
                    })
                else:
                    error_count += 1
                    details.append({
                        "position": position,
                        "status": "error",
                        "message": "Erreur UPDATE DB"
                    })
            else:
                # Compiler les erreurs
                errors = []
                if result_text["status"] != "success":
                    errors.append(f"Texte: {result_text['message']}")
                if result_img_1["status"] != "success":
                    errors.append(f"Image 1: {result_img_1['message']}")
                if result_img_2["status"] != "success":
                    errors.append(f"Image 2: {result_img_2['message']}")
                
                error_count += 1
                details.append({
                    "position": position,
                    "status": "error",
                    "message": " | ".join(errors)
                })
        
        return {
            "status": "success" if error_count == 0 else "partial",
            "total": total,
            "success": success_count,
            "errors": error_count,
            "details": details
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur globale: {str(e)}",
            "total": 0,
            "success": 0,
            "errors": 0,
            "details": []
        }


def update_carousel_text(item_id: str, field: str, value: str) -> Dict[str, object]:
    """
    Met à jour un champ texte d'un item carousel.
    
    Args:
        item_id: UUID de l'item
        field: "title_carou", "content_carou", "prompt_image_2" ou "prompt_image_3"
        value: Nouvelle valeur
    
    Returns:
        {"status": "success" | "error", "message": str}
    """
    
    if field not in ["title_carou", "content_carou", "prompt_image_2", "prompt_image_3"]:
        return {
            "status": "error",
            "message": f"Champ invalide: {field}"
        }
    
    try:
        supabase = get_supabase()
        
        response = supabase.table("carousel_eco").update({
            field: value
        }).eq("id", item_id).execute()
        
        if response.data:
            return {
                "status": "success",
                "message": "Texte mis à jour"
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


def generate_all_image_prompts_parallel(items: List[Dict], prompt_type: str = "sunset", progress_callback=None) -> Dict[str, object]:
    """
    Génère tous les prompts images en parallèle (OPTIMISÉ).
    
    Args:
        items: Liste des items avec id, title, content
        prompt_type: Type de prompt ("sunset" ou "studio")
        progress_callback: Fonction appelée à chaque item terminé (callback(item_id, position, success))
    
    Returns:
        {
            "status": "success" | "partial" | "error",
            "total": int,
            "success": int,
            "errors": int,
            "details": [...]
        }
    """
    
    def process_single_item(item):
        """Process un item et retourne le résultat."""
        item_id = item.get("id")
        position = item.get("position", -1)
        title = item.get("title", "")
        content = item.get("content", "")
        
        # Générer le prompt image
        result = generate_image_prompt_for_item(title, content, prompt_type)
        
        if result.get("status") == "success":
            # Sauvegarder dans DB
            try:
                supabase = get_supabase()
                supabase.table("carousel_eco").update({
                    "prompt_image_1": result.get("image_prompt")
                }).eq("id", item_id).execute()
                
                # Callback de progression
                if progress_callback:
                    progress_callback(item_id, position, True)
                
                return {
                    "item_id": item_id,
                    "position": position,
                    "status": "success",
                    "image_prompt": result.get("image_prompt")
                }
            except Exception as e:
                if progress_callback:
                    progress_callback(item_id, position, False)
                return {
                    "item_id": item_id,
                    "position": position,
                    "status": "error",
                    "message": f"Erreur DB: {str(e)}"
                }
        else:
            if progress_callback:
                progress_callback(item_id, position, False)
            return {
                "item_id": item_id,
                "position": position,
                "status": "error",
                "message": result.get("message", "Erreur inconnue")
            }
    
    # Génération parallèle avec ThreadPoolExecutor
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_single_item, item): item for item in items}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "status": "error",
                    "message": f"Thread error: {str(e)}"
                })
    
    # Agréger les résultats
    total = len(items)
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = total - success_count
    
    if success_count == total:
        status = "success"
    elif success_count > 0:
        status = "partial"
    else:
        status = "error"
    
    return {
        "status": status,
        "total": total,
        "success": success_count,
        "errors": error_count,
        "details": results
    }
