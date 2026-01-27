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
        
        # Charger le modèle Imagen 3.0 (nouveau modèle 2026)
        if quality == "hd":
            # Imagen 3.0 (haute qualité)
            model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        else:
            # Imagen 3.0 Fast (rapide)
            model = ImageGenerationModel.from_pretrained("imagen-3.0-fast-generate-001")
        
        # Générer l'image avec Imagen 3.0
        # Imagen 3.0 utilise une API simplifiée
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1",
        )
        
        # Récupérer la première image
        if response.images and len(response.images) > 0:
            image = response.images[0]
            
            # Convertir en base64
            # Imagen 3.0 retourne l'image via _image_bytes
            image_bytes = image._image_bytes
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Imagen 3.0 génère en 1024x1024 par défaut
            # HD utilise imagen-3.0-generate-001 (meilleure qualité)
            # Standard utilise imagen-3.0-fast-generate-001 (plus rapide)
            resolution = "1K"  # Les deux génèrent en 1024x1024
            model_name = "Imagen 3.0" if quality == "hd" else "Imagen 3.0 Fast"
            
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
    Génère une image pour carousel avec fallback automatique Imagen 3.0 → Fast
    
    Stratégie:
    1. Essayer Imagen 3.0 (haute qualité, plus lent)
    2. Si échec → Fallback Imagen 3.0 Fast (rapide)
    
    Note: Les deux génèrent en 1024x1024 (1K), mais Imagen 3.0 a une meilleure qualité
    
    Args:
        prompt: Le prompt de génération d'image
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "...",
            "model_used": "...",
            "resolution": "1K",
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
        "message": f"❌ ÉCHEC COMPLET (Imagen 3.0 + Fast)\n\n🔴 Imagen 3.0:\n{hd_msg}\n\n🟡 Imagen 3.0 Fast:\n{std_msg}"
    }
