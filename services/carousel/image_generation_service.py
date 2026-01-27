"""
Service de génération d'images pour les carousels
Utilise l'API Google Gemini 3 Pro Image Preview (meilleur rendu)
Documentation: https://ai.google.dev/gemini-api/docs/image-generation
"""

import streamlit as st
import requests
import base64
import time
from typing import Dict


def _try_generate_image(model: str, prompt: str, image_size: str, max_retries: int, retry_delays: list, timeout: int) -> Dict[str, object]:
    """
    Fonction interne pour essayer de générer une image avec un modèle spécifique
    """
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "imageConfig": {
                "aspectRatio": "1:1",
                "imageSize": image_size
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Retry automatique en cas de surcharge (503)
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            
            # Si succès, on sort de la boucle
            if response.status_code == 200:
                data = response.json()
                
                # Parser la réponse
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        
                        for part in parts:
                            if "inlineData" in part and "data" in part["inlineData"]:
                                image_data = part["inlineData"]["data"]
                                
                                return {
                                    "status": "success",
                                    "image_data": image_data,
                                    "image_url": None,
                                    "model_used": model,
                                    "resolution": image_size
                                }
                
                # Format inattendu
                return {
                    "status": "error",
                    "message": f"Format de réponse inattendu pour {model}"
                }
            
            # Si 503 (overloaded) et qu'il reste des tentatives
            if response.status_code == 503 and attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"{model} surchargé, retry dans {wait_time}s (tentative {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            
            # Autres erreurs
            return {
                "status": "error",
                "message": f"Erreur {response.status_code} avec {model}: {response.text[:200]}"
            }
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"{model} timeout, retry dans {wait_time}s")
                time.sleep(wait_time)
                continue
            else:
                return {
                    "status": "error",
                    "message": f"Timeout après {max_retries} tentatives avec {model}"
                }
    
    return {
        "status": "error",
        "message": f"Échec après {max_retries} tentatives avec {model}"
    }


def generate_carousel_image(prompt: str) -> Dict[str, object]:
    """
    Génère une image 1:1 avec Nano Banana Pro (gemini-3-pro-image-preview)
    
    Stratégie:
    - Nano Banana Pro (2K) - 2 min timeout, 5 retries avec backoff progressif
    - Pas de fallback (Flash ne supporte pas bien le format image)
    
    Args:
        prompt: Le prompt de génération d'image
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "...",
            "model_used": "gemini-3-pro-image-preview",
            "resolution": "2K",
            "message": "..." (si erreur)
        }
    """
    # Essayer Nano Banana Pro avec 5 retries et backoff progressif
    result = _try_generate_image(
        model="gemini-3-pro-image-preview",
        prompt=prompt,
        image_size="2K",
        max_retries=5,  # Augmenté de 3 à 5
        retry_delays=[5, 10, 15, 20, 30],  # Backoff progressif
        timeout=120  # 2 minutes
    )
    
    return result


def save_image_to_carousel(item_id: str, image_url: str) -> Dict[str, object]:
    """
    Sauvegarde l'URL de l'image dans la table carousel_eco
    
    Args:
        item_id: L'ID de l'item
        image_url: L'URL de l'image à sauvegarder
        
    Returns:
        {"status": "success" | "error", "message": "..."}
    """
    try:
        from db.supabase_client import get_supabase
        supabase = get_supabase()
        
        response = supabase.table("carousel_eco").update({
            "image_url": image_url
        }).eq("id", item_id).execute()
        
        return {
            "status": "success",
            "message": "Image enregistrée"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur DB : {str(e)}"
        }
