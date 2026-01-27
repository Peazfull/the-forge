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
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
from vertexai.preview.vision_models import ImageGenerationModel


def _generate_with_gemini(prompt: str, project_id: str, location: str) -> Dict[str, object]:
    """
    Génère une image avec Gemini 3 Pro Image Preview (GenerativeModel)
    """
    try:
        # Initialiser Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Charger le modèle Gemini 3 Pro Image
        model = GenerativeModel("gemini-3-pro-image-preview")
        
        # Générer l'image via generate_content
        response = model.generate_content([prompt])
        
        # Extraire l'image de la réponse
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_bytes = part.inline_data.data
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        
                        return {
                            "status": "success",
                            "image_data": image_base64,
                            "image_url": None,
                            "model_used": "vertex-ai-Gemini-3-Pro-Image",
                            "resolution": "1024x1024"
                        }
        
        return {
            "status": "error",
            "message": "❌ Aucune image générée par Gemini 3 Pro"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Erreur Gemini 3 Pro : {str(e)}"
        }


def _generate_with_imagen(prompt: str, project_id: str, location: str) -> Dict[str, object]:
    """
    Génère une image avec Imagen 3.0 Fast (ImageGenerationModel)
    """
    try:
        # Initialiser Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Charger le modèle Imagen 3.0 Fast
        model = ImageGenerationModel.from_pretrained("imagen-3.0-fast-generate-001")
        
        # Générer l'image
        generation_params = {
            "prompt": prompt,
            "number_of_images": 1,
            "aspect_ratio": "1:1",
            "safety_filter_level": "block_few",
            "person_generation": "allow_adult",
            "add_watermark": False,
        }
        
        response = model.generate_images(**generation_params)
        
        # Récupérer la première image
        if response.images and len(response.images) > 0:
            image = response.images[0]
            image_bytes = image._image_bytes
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            return {
                "status": "success",
                "image_data": image_base64,
                "image_url": None,
                "model_used": "vertex-ai-Imagen-3.0-Fast",
                "resolution": "1024x1024"
            }
        else:
            return {
                "status": "error",
                "message": "❌ Aucune image générée par Imagen 3.0 Fast"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Erreur Imagen 3.0 Fast : {str(e)}"
        }


def generate_image_vertex_ai(prompt: str, quality: str = "standard") -> Dict[str, object]:
    """
    Génère une image via Vertex AI - Gemini 3 Pro Image Preview (meilleur rendu)
    
    Args:
        prompt: Le prompt de génération (contrôle total utilisateur)
        quality: "hd" (gemini-3-pro-image-preview, meilleur rendu via GenerativeModel) 
                 ou "standard" (imagen-3.0-fast-generate-001, rapide et stable)
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "base64...",
            "model_used": "vertex-ai-gemini-3-pro-image ou vertex-ai-imagen-3.0-fast",
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
        
        # Appeler la fonction appropriée selon la qualité demandée
        if quality == "hd":
            # Gemini 3 Pro Image (GenerativeModel)
            return _generate_with_gemini(prompt, project_id, location)
        else:
            # Imagen 3.0 Fast (ImageGenerationModel)
            return _generate_with_imagen(prompt, project_id, location)
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Erreur Vertex AI : {str(e)}"
        }


def generate_carousel_image_vertex(prompt: str) -> Dict[str, object]:
    """
    Génère une image pour carousel avec GEMINI 3 PRO IMAGE (meilleur rendu) via Vertex AI
    
    Stratégie:
    1. Essayer Gemini 3 Pro Image Preview (meilleur rendu natif, "Nano Banana Pro")
    2. Si échec → Fallback Imagen 3.0 Fast (rapide et stable)
    
    Avantages Vertex AI:
    - Infrastructure stable et dédiée (meilleure disponibilité)
    - Meilleur rendu avec gemini-3-pro-image-preview
    - PAS d'upscaling artificiel (output natif pur)
    
    Qualité HD:
    - Génération 1024x1024 native avec paramètres optimaux
    - Modèle gemini-3-pro-image-preview (meilleure qualité photoréaliste)
    - Contrôle total du prompt par l'utilisateur
    - Filtres minimaux pour plus de détails
    
    Args:
        prompt: Le prompt de génération d'image (utilisé tel quel)
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "...",
            "model_used": "vertex-ai-Gemini-3-Pro-Image" ou "vertex-ai-Imagen-3.0-Fast",
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
        "message": f"❌ ÉCHEC COMPLET (Gemini Pro + Imagen Fast)\n\n🔴 Gemini 3 Pro Image:\n{hd_msg}\n\n🟡 Imagen 3.0 Fast:\n{std_msg}"
    }
