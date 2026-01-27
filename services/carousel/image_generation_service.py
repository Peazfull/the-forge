"""
Service de génération d'images pour les carousels
Utilise l'API Google Gemini Imagen
"""

import streamlit as st
import requests
import base64
from typing import Dict


def generate_carousel_image(prompt: str) -> Dict[str, object]:
    """
    Génère une image 1:1 2K via l'API Google Generative AI (Imagen)
    
    Args:
        prompt: Le prompt de génération d'image
        
    Returns:
        {
            "status": "success" | "error",
            "image_url": "...",  # URL de l'image générée (si succès)
            "image_data": "...",  # Données base64 de l'image (si succès)
            "message": "..."  # Message d'erreur (si échec)
        }
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # Essayer avec l'API Gemini 2.0 qui supporte les images
        # Documentation: https://ai.google.dev/gemini-api/docs/imagen
        url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
        
        payload = {
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "negativePrompt": "",
                "safetySetting": "block_some",
                "personGeneration": "allow_adult",
                "sampleImageSize": "2048"  # 2K
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            
            # Débugger la réponse complète pour voir le format
            print(f"DEBUG - Response data keys: {data.keys()}")
            
            # Essayer différents formats de réponse possibles
            image_data = None
            
            # Format 1: generatedImages avec base64
            if "generatedImages" in data and len(data["generatedImages"]) > 0:
                image_obj = data["generatedImages"][0]
                if "imageBytes" in image_obj:
                    image_data = image_obj["imageBytes"]
                elif "image" in image_obj:
                    image_data = image_obj["image"]
            
            # Format 2: predictions (Vertex AI style)
            elif "predictions" in data and len(data["predictions"]) > 0:
                prediction = data["predictions"][0]
                if "bytesBase64Encoded" in prediction:
                    image_data = prediction["bytesBase64Encoded"]
                elif "image" in prediction:
                    image_data = prediction["image"]
            
            # Format 3: image directement dans la réponse
            elif "image" in data:
                image_data = data["image"]
            
            if image_data:
                return {
                    "status": "success",
                    "image_data": image_data,
                    "image_url": None
                }
            else:
                return {
                    "status": "error",
                    "message": f"Format de réponse inattendu. Keys disponibles: {list(data.keys())}"
                }
        else:
            error_detail = f"Status: {response.status_code}\nURL: {url}\nRéponse: {response.text[:500]}"
            return {
                "status": "error",
                "message": f"Erreur API ({response.status_code}): {response.text}",
                "debug": error_detail
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Timeout : la génération a pris trop de temps"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur : {str(e)}"
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
