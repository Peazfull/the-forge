"""
Service de génération d'images pour les carousels
Utilise l'API Google Gemini Nano Banana Pro
Documentation: https://ai.google.dev/gemini-api/docs/image-generation
"""

import streamlit as st
import requests
import base64
from typing import Dict


def generate_carousel_image(prompt: str) -> Dict[str, object]:
    """
    Génère une image 1:1 2K via Nano Banana Pro (gemini-3-pro-image-preview)
    
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
        
        # Endpoint pour Nano Banana Pro
        # Documentation: https://ai.google.dev/gemini-api/docs/image-generation
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt}
                ]
            }],
            "generationConfig": {
                "imageConfig": {
                    "aspectRatio": "1:1",  # Format carré
                    "imageSize": "2K"      # Résolution 2048x2048
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            
            # Format de réponse Gemini API standard
            # Structure: {"candidates": [{"content": {"parts": [{"text": "..."}, {"inlineData": {"data": "base64..."}}]}}]}
            
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    
                    # Parcourir les parts pour trouver l'image
                    for part in parts:
                        if "inlineData" in part and "data" in part["inlineData"]:
                            image_data = part["inlineData"]["data"]
                            
                            return {
                                "status": "success",
                                "image_data": image_data,
                                "image_url": None
                            }
            
            # Si on arrive ici, le format n'est pas celui attendu
            return {
                "status": "error",
                "message": f"Format de réponse inattendu. Keys: {list(data.keys())}. Contenu: {str(data)[:500]}"
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
