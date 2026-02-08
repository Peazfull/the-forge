"""Service pour générer des prompts d'image Breaking avec recommandations manuelles."""

import json
import streamlit as st
from openai import OpenAI
from typing import Dict

from prompts.breaking.generate_breaking_image_prompts_manual import (
    PROMPT_GENERATE_BREAKING_IMAGE_PROMPT_MANUAL,
)


REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 10


def generate_breaking_image_prompt_manual(
    title: str, content: str, manual_recommendations: str
) -> Dict[str, object]:
    """
    Génère un prompt d'image Breaking enrichi avec des recommandations manuelles.
    
    Args:
        title: Titre de la breaking news
        content: Contenu de la breaking news
        manual_recommendations: Recommandations manuelles de l'utilisateur
    
    Returns:
        {
            "status": "success" | "error",
            "image_prompt": str,
            "message": str (si erreur)
        }
    """
    
    if not title or not content:
        return {
            "status": "error",
            "message": "Titre ou contenu manquant",
            "image_prompt": None,
        }
    
    if not manual_recommendations or not manual_recommendations.strip():
        return {
            "status": "error",
            "message": "Recommandations manuelles manquantes",
            "image_prompt": None,
        }
    
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Construire l'input
        user_input = f"""TITRE: {title}

CONTENU: {content}

RECOMMANDATIONS MANUELLES DE L'UTILISATEUR:
{manual_recommendations}
"""
        
        # Retry logic avec délai progressif pour gérer le rate limiting
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_GENERATE_BREAKING_IMAGE_PROMPT_MANUAL},
                        {"role": "user", "content": user_input},
                    ],
                    temperature=0.6,
                    response_format={"type": "json_object"},
                    timeout=REQUEST_TIMEOUT,
                )
                
                raw_json = response.choices[0].message.content or ""
                data = json.loads(raw_json)
                
                break
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg and attempt < MAX_RETRIES - 1:
                    import time
                    delay = RETRY_DELAY * (attempt + 1)
                    time.sleep(delay)
                    continue
                elif attempt < MAX_RETRIES - 1:
                    import time
                    time.sleep(2)
                    continue
                else:
                    raise e
        
        # Validation
        if "image_prompt" not in data:
            return {
                "status": "error",
                "message": "Champ 'image_prompt' manquant dans la réponse IA",
                "image_prompt": None,
            }
        
        return {
            "status": "success",
            "image_prompt": data["image_prompt"],
            "message": "Prompt généré avec succès",
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur: {str(e)}",
            "image_prompt": None,
        }
