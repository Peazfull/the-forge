import json
import streamlit as st
from openai import OpenAI
from typing import Dict, List
from db.supabase_client import get_supabase
from prompts.carousel.generate_carousel_texts import PROMPT_GENERATE_CAROUSEL_TEXTS


REQUEST_TIMEOUT = 60
MAX_RETRIES = 2


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
        
        # Retry logic
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
                if attempt < MAX_RETRIES - 1:
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
            
            # Génération IA
            result = generate_carousel_text_for_item(title, content)
            
            if result["status"] == "success":
                # Mise à jour en DB
                update_response = supabase.table("carousel_eco").update({
                    "title_carou": result["title_carou"],
                    "content_carou": result["content_carou"]
                }).eq("id", item_id).execute()
                
                if update_response.data:
                    success_count += 1
                    details.append({
                        "position": position,
                        "status": "success",
                        "title_carou": result["title_carou"]
                    })
                else:
                    error_count += 1
                    details.append({
                        "position": position,
                        "status": "error",
                        "message": "Erreur UPDATE DB"
                    })
            else:
                error_count += 1
                details.append({
                    "position": position,
                    "status": "error",
                    "message": result["message"]
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
        field: "title_carou" ou "content_carou"
        value: Nouvelle valeur
    
    Returns:
        {"status": "success" | "error", "message": str}
    """
    
    if field not in ["title_carou", "content_carou"]:
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
