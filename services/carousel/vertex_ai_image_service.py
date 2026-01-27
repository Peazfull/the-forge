"""
Service de génération d'images via Google Gen AI SDK (nouveau SDK unifié 2026)
Utilise Nano Banana Pro (Gemini 3 Pro Image Preview) via Vertex AI
Documentation: https://googleapis.github.io/python-genai/
"""

import streamlit as st
import os
import base64
from typing import Dict
from google import genai
from google.genai import types


def _init_client() -> genai.Client:
    """
    Initialise le client Google Gen AI avec Vertex AI
    """
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
    
    # Créer le client Vertex AI
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )
    
    return client


def generate_image_vertex_ai(prompt: str) -> Dict[str, object]:
    """
    Génère une image via Vertex AI - Nano Banana Pro (Gemini 3 Pro Image Preview)
    Utilise le nouveau SDK google-genai unifié
    
    Args:
        prompt: Le prompt de génération (contrôle total utilisateur)
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "base64...",
            "model_used": "Nano-Banana-Pro",
            "resolution": "1024x1024",
            "message": "..." (si erreur)
        }
    """
    try:
        # Initialiser le client
        client = _init_client()
        
        # Générer l'image avec Nano Banana Pro (Gemini 3 Pro Image Preview)
        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="1:1",
                ),
            ),
        )
        
        # Extraire l'image de la réponse
        for part in response.parts:
            if part.inline_data:
                # Récupérer l'image en bytes
                image_bytes = part.inline_data.data
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                return {
                    "status": "success",
                    "image_data": image_base64,
                    "image_url": None,
                    "model_used": "Nano-Banana-Pro",
                    "resolution": "1024x1024"
                }
        
        return {
            "status": "error",
            "message": "❌ Aucune image générée par Nano Banana Pro"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Erreur Nano Banana Pro : {str(e)}"
        }


def generate_carousel_image_vertex(prompt: str) -> Dict[str, object]:
    """
    Génère une image pour carousel avec Nano Banana Pro (Gemini 3 Pro Image)
    Utilise le nouveau SDK google-genai unifié via Vertex AI
    
    Avantages:
    - Meilleur rendu photoréaliste (Nano Banana Pro)
    - Infrastructure Vertex AI stable
    - Output natif 1024x1024 (pas d'upscaling artificiel)
    - SDK moderne et unifié
    
    Args:
        prompt: Le prompt de génération d'image (utilisé tel quel)
        
    Returns:
        {
            "status": "success" | "error",
            "image_data": "...",
            "model_used": "Nano-Banana-Pro",
            "resolution": "1024x1024",
            "message": "..." (si erreur)
        }
    """
    # Générer avec Nano Banana Pro uniquement (pas de fallback Imagen qui est nul)
    return generate_image_vertex_ai(prompt)
