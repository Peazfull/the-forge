import json
import streamlit as st
from openai import OpenAI

from prompts.doss.generate_doss_texts import PROMPT_GENERATE_DOSS_TEXTS
from prompts.doss.rewrite_doss_article import PROMPT_REWRITE_DOSS_ARTICLE
from prompts.doss.generate_doss_image_prompts import PROMPT_GENERATE_DOSS_IMAGE_PROMPT

REQUEST_TIMEOUT = 30


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
