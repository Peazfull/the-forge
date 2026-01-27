"""
Service de génération d'images via Google Cloud Vertex AI
Utilise Gemini 3 Pro Image Preview (meilleur rendu) via l'infrastructure Vertex AI
Plus stable et fiable que l'API Gemini directe
Documentation: https://cloud.google.com/vertex-ai/docs/generative-ai/image/generate-images
"""

import streamlit as st
import os
import base64
from typing import Dict
from google.cloud import aiplatform
from vertexai.preview.vision_models import ImageGenerationModel


def generate_image_vertex_ai(prompt: str, quality: str = "standard") -> Dict[str, object]:
    """
    Génère une image via Vertex AI - Gemini 3 Pro Image Preview (meilleur rendu)
    
    Args:
        prompt: Le prompt de génération (contrôle total utilisateur)
        quality: "hd" (gemini-3-pro-image-preview, meilleur rendu) 
                 ou "standard" (gemini-2.5-flash-image, rapide)
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "base64...",
            "model_used": "vertex-ai-gemini-3-pro-image",
            "resolution": "1024x1024" (natif),
            "message": "..." (si erreur)
        }
    """
    try:
        # Configuration de l'authentification
        project_id = st.secrets["GCP_PROJECT_ID"]
        location = st.secrets["VERTEX_AI_LOCATION"]
        
        # En production (Streamlit Cloud) : utiliser les secrets
        # En local : utiliser le fichier JSON
        key_path = os.path.join(os.path.dirname(__file__), "..", "..", "vertex-ai-key.json")
        
        if os.path.exists(key_path):
            # Local : utiliser le fichier JSON
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
        else:
            # Streamlit Cloud : utiliser les secrets
            import json
            import tempfile
            
            # Récupérer les credentials depuis les secrets
            gcp_creds = st.secrets["gcp_service_account"]
            
            # Créer un fichier temporaire avec les credentials
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(dict(gcp_creds), f)
                temp_key_path = f.name
            
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_key_path
        
        # Initialiser Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        # Charger Gemini 3 Pro Image Preview via Vertex AI (meilleur rendu)
        if quality == "hd":
            # Gemini 3 Pro Image Preview (meilleur qualité)
            model = ImageGenerationModel.from_pretrained("gemini-3-pro-image-preview")
        else:
            # Gemini 2.5 Flash Image (rapide)
            model = ImageGenerationModel.from_pretrained("gemini-2.5-flash-image")
        
        # Générer l'image avec Gemini 3 Pro Image - PARAMÈTRES OPTIMAUX
        # Pas d'upscaling artificiel, on veut le meilleur output natif direct
        generation_params = {
            "prompt": prompt,
            "number_of_images": 1,
            "aspect_ratio": "1:1",
            "safety_filter_level": "block_few",  # Moins de restrictions
            "person_generation": "allow_adult",  # Autoriser les personnes
            "add_watermark": False,  # Pas de watermark
        }
        
        # Mode HD : utilise gemini-3-pro-image-preview (meilleur rendu photoréaliste)
        # Mode Standard : utilise gemini-2.5-flash-image (rapide)
        # Pas de modification du prompt pour laisser l'utilisateur avoir le contrôle total
        
        response = model.generate_images(**generation_params)
        
        # Récupérer la première image
        if response.images and len(response.images) > 0:
            image = response.images[0]
            
            # PAS D'UPSCALING ARTIFICIEL
            # On veut le meilleur output natif direct d'Imagen 3.0
            # Résolution native : 1024x1024
            
            # Convertir en base64
            image_bytes = image._image_bytes
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Gemini génère en 1024x1024 natif
            resolution = "1024x1024"
            model_name = "Gemini-3-Pro-Image" if quality == "hd" else "Gemini-2.5-Flash-Image"
            
            return {
                "status": "success",
                "image_data": image_base64,
                "image_url": None,
                "model_used": f"vertex-ai-{model_name}",
                "resolution": resolution
            }
        else:
            return {
                "status": "error",
                "message": "❌ Aucune image générée par Vertex AI"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Erreur Vertex AI : {str(e)}"
        }


def generate_carousel_image_vertex(prompt: str) -> Dict[str, object]:
    """
    Génère une image pour carousel avec GEMINI 3 PRO IMAGE (meilleur rendu) via Vertex AI
    
    Stratégie:
    1. Essayer Gemini 3 Pro Image Preview (meilleur rendu natif)
    2. Si échec → Fallback Gemini 2.5 Flash Image (rapide)
    
    Avantages Vertex AI:
    - Infrastructure stable et dédiée (pas d'overload comme l'API directe)
    - Meilleur rendu avec gemini-3-pro-image-preview
    - PAS d'upscaling artificiel
    
    Qualité HD:
    - Génération 1024x1024 native avec paramètres optimaux
    - Modèle gemini-3-pro-image-preview (meilleur qualité photoréaliste)
    - Contrôle total du prompt par l'utilisateur
    - Filtres minimaux pour plus de détails
    
    Args:
        prompt: Le prompt de génération d'image (utilisé tel quel)
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "...",
            "model_used": "...",
            "resolution": "1024x1024",
            "message": "..." (si erreur)
        }
    """
    # TENTATIVE 1 : Imagen 3.0 (haute qualité)
    result_hd = generate_image_vertex_ai(prompt, quality="hd")
    
    if result_hd.get("status") == "success":
        result_hd["tried_fallback"] = False
        return result_hd
    
    # FALLBACK : Imagen 3.0 Fast (rapide)
    result_standard = generate_image_vertex_ai(prompt, quality="standard")
    
    if result_standard.get("status") == "success":
        result_standard["tried_fallback"] = True
        result_standard["hd_error"] = result_hd.get('message', 'Erreur Imagen 3.0')
        return result_standard
    
    # Les deux ont échoué
    hd_msg = result_hd.get('message', 'Erreur inconnue')
    std_msg = result_standard.get('message', 'Erreur inconnue')
    
    return {
        "status": "error",
        "message": f"❌ ÉCHEC COMPLET (Gemini Pro + Flash)\n\n🔴 Gemini 3 Pro Image:\n{hd_msg}\n\n🟡 Gemini 2.5 Flash:\n{std_msg}"
    }
