import json
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Callable, Optional
import streamlit as st
from openai import OpenAI

from prompts.doss.generate_doss_texts import PROMPT_GENERATE_DOSS_TEXTS
from prompts.doss.rewrite_doss_article import PROMPT_REWRITE_DOSS_ARTICLE
from prompts.doss.generate_doss_image_prompts import PROMPT_GENERATE_DOSS_IMAGE_PROMPT

REQUEST_TIMEOUT = 30
MAX_WORKERS_IMAGES = 6  # Paralléliser jusqu'à 6 images en même temps


def generate_doss_texts(raw_text: str) -> dict:
    if not raw_text.strip():
        return {"status": "error", "message": "Texte brut manquant"}

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    rewrite = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PROMPT_REWRITE_DOSS_ARTICLE},
            {"role": "user", "content": raw_text},
        ],
        temperature=0.6,
        timeout=REQUEST_TIMEOUT,
    )
    rewritten_text = (rewrite.choices[0].message.content or "").strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PROMPT_GENERATE_DOSS_TEXTS},
            {"role": "user", "content": rewritten_text},
        ],
        temperature=0.6,
        response_format={"type": "json_object"},
        timeout=REQUEST_TIMEOUT,
    )
    content = response.choices[0].message.content or ""
    data = json.loads(content)
    return {"status": "success", "data": data}


def generate_doss_image_prompt(title: str, content: str) -> dict:
    user_input = f"TITRE: {title}\n\nCONTENU: {content}"
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PROMPT_GENERATE_DOSS_IMAGE_PROMPT},
            {"role": "user", "content": user_input},
        ],
        temperature=0.6,
        response_format={"type": "json_object"},
        timeout=REQUEST_TIMEOUT,
    )
    content = response.choices[0].message.content or ""
    return json.loads(content)


def generate_doss_image(prompt: str) -> dict:
    from services.carousel.image_generation_service import generate_carousel_image
    return generate_carousel_image(prompt, aspect_ratio="5:4")


def generate_doss_images_parallel(
    state: Dict,
    slide_data: list,
    upload_callback: Callable[[int, bytes], Optional[str]],
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[int, str]:
    """
    Génère les 5 images de Doss en parallèle.
    
    Args:
        state: Le state dict contenant les prompts
        slide_data: Liste de tuples (idx, title, content)
        upload_callback: Fonction pour uploader l'image (idx, image_bytes) -> url
        progress_callback: Fonction appelée à chaque image générée (current, total)
    
    Returns:
        Dict[int, str]: Mapping idx -> image_url
    """
    results = {}
    total = len(slide_data)
    current = 0
    
    def generate_single_image(idx: int, title: str, content: str) -> tuple:
        """Génère une seule image et retourne (idx, url ou None)"""
        try:
            # Récupérer le prompt depuis le state
            prompt = state.get(f"prompt_image_{idx}", "")
            
            # Si pas de prompt, le générer
            if not prompt:
                if idx == 0:
                    # Pour la cover, on utilise slide1
                    p = generate_doss_image_prompt(
                        state.get("slide1_title", ""),
                        state.get("slide1_content", "")
                    )
                else:
                    p = generate_doss_image_prompt(title, content)
                prompt = p.get("image_prompt", "")
                state[f"prompt_image_{idx}"] = prompt
            
            if not prompt:
                return (idx, None, "Prompt vide")
            
            # Générer l'image
            result = generate_doss_image(prompt)
            
            if result.get("status") == "success":
                image_bytes = base64.b64decode(result["image_data"])
                url = upload_callback(idx, image_bytes)
                return (idx, url, None)
            else:
                return (idx, None, result.get("message", "Erreur inconnue"))
        except Exception as e:
            return (idx, None, str(e))
    
    # Lancer la génération en parallèle
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_IMAGES) as executor:
        futures = {
            executor.submit(generate_single_image, idx, title, content): idx
            for idx, title, content in slide_data
        }
        
        for future in as_completed(futures):
            idx, url, error = future.result()
            current += 1
            
            if url:
                results[idx] = url
            
            # Callback pour le progrès
            if progress_callback:
                progress_callback(current, total)
    
    return results

