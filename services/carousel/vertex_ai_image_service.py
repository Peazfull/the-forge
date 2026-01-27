"""
Service de génération d'images via Google Cloud Vertex AI
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
    Génère une image via Vertex AI Imagen
    
    Args:
        prompt: Le prompt de génération
        quality: "standard" (1024x1024, rapide) ou "hd" (2048x2048, qualité)
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "base64...",
            "model_used": "vertex-ai-imagen",
            "resolution": "1K" | "2K",
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
        
        # Charger le modèle Imagen
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Paramètres selon la qualité
        if quality == "hd":
            # HD : 2048x2048
            number_of_images = 1
            aspect_ratio = "1:1"
            guidance_scale = 15  # Plus de fidélité au prompt
        else:
            # Standard : 1024x1024
            number_of_images = 1
            aspect_ratio = "1:1"
            guidance_scale = 10
        
        # Générer l'image
        response = model.generate_images(
            prompt=prompt,
            number_of_images=number_of_images,
            aspect_ratio=aspect_ratio,
            guidance_scale=guidance_scale,
            add_watermark=False,  # Pas de watermark
        )
        
        # Récupérer la première image
        if response.images and len(response.images) > 0:
            image = response.images[0]
            
            # Convertir en base64
            image_bytes = image._image_bytes
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            resolution = "2K" if quality == "hd" else "1K"
            
            return {
                "status": "success",
                "image_data": image_base64,
                "image_url": None,
                "model_used": "vertex-ai-imagen",
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
    Génère une image pour carousel avec fallback automatique HD → Standard
    
    Stratégie:
    1. Essayer HD (2K) - haute qualité
    2. Si échec → Fallback Standard (1K)
    
    Args:
        prompt: Le prompt de génération d'image
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "...",
            "model_used": "...",
            "resolution": "2K" | "1K",
            "message": "..." (si erreur)
        }
    """
    # TENTATIVE 1 : HD (2K)
    result_hd = generate_image_vertex_ai(prompt, quality="hd")
    
    if result_hd.get("status") == "success":
        result_hd["tried_fallback"] = False
        return result_hd
    
    # FALLBACK : Standard (1K)
    result_standard = generate_image_vertex_ai(prompt, quality="standard")
    
    if result_standard.get("status") == "success":
        result_standard["tried_fallback"] = True
        result_standard["hd_error"] = result_hd.get('message', 'Erreur HD')
        return result_standard
    
    # Les deux ont échoué
    hd_msg = result_hd.get('message', 'Erreur inconnue')
    std_msg = result_standard.get('message', 'Erreur inconnue')
    
    return {
        "status": "error",
        "message": f"❌ ÉCHEC COMPLET (HD + Standard)\n\n🔴 HD (2K):\n{hd_msg}\n\n🟡 Standard (1K):\n{std_msg}"
    }
