"""
Service de génération d'images pour les carousels
Stratégie: Nano Banana Pro (Gemini) → Fallback DALL-E 3 (OpenAI)
"""

import streamlit as st
import requests
import base64
import time
from typing import Dict
from openai import OpenAI


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


def _generate_with_gpt_image(prompt: str) -> Dict[str, object]:
    """
    Génère une image avec GPT Image 1.5 (OpenAI) en fallback
    Meilleur que DALL-E 3 : instruction following supérieur, meilleur text rendering
    """
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        response = client.images.generate(
            model="gpt-image-1.5",  # Nouveau modèle state-of-the-art 2026
            prompt=prompt,
            size="1024x1024",  # Format 1:1
            quality="high",  # Qualité haute (low/medium/high)
        )
        
        # Récupérer l'URL de l'image et la télécharger en base64
        image_url = response.data[0].url
        
        # Télécharger l'image
        img_response = requests.get(image_url, timeout=30)
        if img_response.status_code == 200:
            image_base64 = base64.b64encode(img_response.content).decode('utf-8')
            
            return {
                "status": "success",
                "image_data": image_base64,
                "image_url": image_url,
                "model_used": "gpt-image-1.5",
                "resolution": "1024x1024"
            }
        else:
            return {
                "status": "error",
                "message": f"❌ Erreur téléchargement image GPT Image 1.5 : {img_response.status_code}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Erreur GPT Image 1.5 : {str(e)}"
        }


def generate_carousel_image(prompt: str) -> Dict[str, object]:
    """
    Génère une image 1:1 avec Nano Banana Pro → Fallback GPT Image 1.5
    
    Stratégie:
    1. Essayer Nano Banana Pro (Gemini 3 Pro Image) - 2 retries
    2. Si échec → Fallback GPT Image 1.5 (OpenAI) - State-of-the-art, quality high
    
    Args:
        prompt: Le prompt de génération d'image
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "...",
            "model_used": "gemini-3-pro-image-preview" ou "gpt-image-1.5",
            "resolution": "2K" ou "1024x1024",
            "message": "..." (si erreur)
        }
    """
    # TENTATIVE 1 : Nano Banana Pro (2 retries)
    result_gemini = _try_generate_image(
        model="gemini-3-pro-image-preview",
        prompt=prompt,
        image_size="2K",
        max_retries=2,
        retry_delays=[5, 10],
        timeout=120  # 2 minutes
    )
    
    if result_gemini.get("status") == "success":
        result_gemini["tried_fallback"] = False
        return result_gemini
    
    # FALLBACK : GPT Image 1.5 (OpenAI)
    print(f"⚠️ Nano Banana Pro échoué : {result_gemini.get('message')}")
    print("🔄 Fallback vers GPT Image 1.5...")
    
    result_gpt = _generate_with_gpt_image(prompt)
    
    if result_gpt.get("status") == "success":
        result_gpt["tried_fallback"] = True
        result_gpt["gemini_error"] = result_gemini.get('message', 'Erreur Gemini')
        return result_gpt
    
    # Les deux ont échoué
    gemini_msg = result_gemini.get('message', 'Erreur inconnue')
    gpt_msg = result_gpt.get('message', 'Erreur inconnue')
    
    return {
        "status": "error",
        "message": f"❌ ÉCHEC COMPLET (Nano Banana Pro + GPT Image 1.5)\n\n🔴 Nano Banana Pro:\n{gemini_msg}\n\n🟡 GPT Image 1.5:\n{gpt_msg}\n\n💡 Réessayez dans quelques minutes."
    }


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
