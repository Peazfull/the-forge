import streamlit as st
import json
from openai import OpenAI
from prompts.process_text_prompt import PROMPT_PROCESS_TEXT


# Création du client OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def process_text(text: str) -> dict:
    if not text or not text.strip():
        return {
            "status": "error",
            "message": "Empty text input",
            "items": []
        }

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": PROMPT_PROCESS_TEXT
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    ai_text = response.choices[0].message.content
    
    # Parser le JSON retourné par l'IA
    try:
        ai_data = json.loads(ai_text)
        return {
            "status": "success",
            "items": ai_data.get("items", [])
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Erreur de parsing JSON: {str(e)}",
            "items": []
        }

