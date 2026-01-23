import json
import streamlit as st
from openai import OpenAI
from typing import Dict
from prompts.theministry.score.score_eco_geopol import PROMPT_SCORE_ECO_GEOPOL
from prompts.theministry.score.score_marches import PROMPT_SCORE_MARCHES
from prompts.theministry.score.score_pea import PROMPT_SCORE_PEA
from prompts.theministry.score.score_action_usa import PROMPT_SCORE_ACTION_USA
from prompts.theministry.score.score_action import PROMPT_SCORE_ACTION
from prompts.theministry.score.score_crypto import PROMPT_SCORE_CRYPTO


REQUEST_TIMEOUT = 60
MAX_RETRIES = 2
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def get_prompt_by_label(labels: str) -> str:
    """
    Retourne le prompt de scoring adapté selon le label.
    
    Args:
        labels: Le label de l'item (Eco_GeoPol, Marchés, PEA, Action_USA, Action, Crypto)
    
    Returns:
        Le prompt approprié
    """
    
    prompts_map = {
        "Eco_GeoPol": PROMPT_SCORE_ECO_GEOPOL,
        "Marchés": PROMPT_SCORE_MARCHES,
        "PEA": PROMPT_SCORE_PEA,
        "Action_USA": PROMPT_SCORE_ACTION_USA,
        "Action": PROMPT_SCORE_ACTION,
        "Crypto": PROMPT_SCORE_CRYPTO
    }
    
    # Retourner le prompt correspondant ou Eco_GeoPol par défaut
    return prompts_map.get(labels, PROMPT_SCORE_ECO_GEOPOL)


def analyze_score(
    title: str,
    content: str,
    tags: str = None,
    labels: str = None,
    entities: str = None,
    source_type: str = None
) -> Dict[str, object]:
    """
    Analyse un item et retourne un score de 0 à 100.
    
    Args:
        title: Titre de l'actualité
        content: Contenu de l'actualité
        tags: Tag (ECO, BOURSE, ACTION, CRYPTO)
        labels: Label (Eco_GeoPol, Marchés, PEA, etc.)
        entities: Entités nommées
        source_type: Type de source (newsletter, manual, rss, etc.)
    
    Returns:
        {
            "status": "success" | "error",
            "score": int (0-100),
            "message": str (si erreur)
        }
    """
    
    if not title or not content:
        return {
            "status": "error",
            "message": "Titre ou contenu manquant",
            "score": None
        }
    
    # Sélectionner le bon prompt selon le label
    prompt = get_prompt_by_label(labels)
    
    # Construire l'input pour l'IA avec contexte
    user_input = f"""TITRE: {title}

CONTENU: {content}

TAG: {tags or "Non renseigné"}
LABEL: {labels or "Non renseigné"}
ENTITIES: {entities or "Non renseigné"}
SOURCE: {source_type or "Non renseigné"}
"""
    
    try:
        # Retry logic pour gérer les timeouts
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": prompt},
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
        
        # Validation du score
        if "score" not in data:
            return {
                "status": "error",
                "message": "Champ 'score' manquant dans la réponse IA",
                "score": None
            }
        
        score = data["score"]
        
        # Vérifier que le score est valide (0-100, entier)
        if not isinstance(score, int) or score < 0 or score > 100:
            return {
                "status": "error",
                "message": f"Score invalide: {score} (doit être un entier entre 0 et 100)",
                "score": None
            }
        
        return {
            "status": "success",
            "score": score
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Erreur JSON: {str(e)}",
            "score": None
        }
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            error_msg = f"Timeout ({REQUEST_TIMEOUT}s dépassé)"
        return {
            "status": "error",
            "message": f"Erreur: {error_msg}",
            "score": None
        }
