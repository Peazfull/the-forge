import json
import streamlit as st
from openai import OpenAI
from typing import Dict, Optional
from prompts.theministry.enrich_metadata import PROMPT_ENRICH_METADATA


REQUEST_TIMEOUT = 60
MAX_RETRIES = 2
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def analyze_metadata(title: str, content: str) -> Dict[str, object]:
    """
    Analyse un item (title + content) et retourne les métadonnées enrichies.
    
    Args:
        title: Titre de l'actualité
        content: Contenu de l'actualité
    
    Returns:
        {
            "status": "success" | "error",
            "tags": str,
            "labels": str,
            "entities": str,
            "zone": str,
            "country": str,
            "message": str (si erreur)
        }
    """
    
    if not title or not content:
        return {
            "status": "error",
            "message": "Titre ou contenu manquant",
            "tags": None,
            "labels": None,
            "entities": None,
            "zone": None,
            "country": None,
        }
    
    # Construire l'input pour l'IA
    user_input = f"TITRE: {title}\n\nCONTENU: {content}"
    
    try:
        # Retry logic pour gérer les timeouts
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_ENRICH_METADATA},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0,
                    response_format={"type": "json_object"},
                    timeout=REQUEST_TIMEOUT
                )
                
                raw_json = response.choices[0].message.content or ""
                data = json.loads(raw_json)
                
                # Si succès, sortir de la boucle
                break
                
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    # Retry sur timeout ou erreur réseau
                    continue
                else:
                    # Dernière tentative échouée, lever l'erreur
                    raise e
        
        # Validation des champs
        required_fields = ["tags", "labels", "entities", "zone", "country"]
        for field in required_fields:
            if field not in data:
                return {
                    "status": "error",
                    "message": f"Champ manquant: {field}",
                    "tags": None,
                    "labels": None,
                    "entities": None,
                    "zone": None,
                    "country": None,
                }
        
        return {
            "status": "success",
            "tags": data["tags"],
            "labels": data["labels"],
            "entities": data["entities"],
            "zone": data["zone"],
            "country": data["country"],
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Erreur JSON: {str(e)}",
            "tags": None,
            "labels": None,
            "entities": None,
            "zone": None,
            "country": None,
        }
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            error_msg = f"Timeout ({REQUEST_TIMEOUT}s dépassé)"
        return {
            "status": "error",
            "message": f"Erreur: {error_msg}",
            "tags": None,
            "labels": None,
            "entities": None,
            "zone": None,
            "country": None,
        }
