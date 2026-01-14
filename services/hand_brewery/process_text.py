import streamlit as st
from openai import OpenAI
from services.prompts.process_text_prompt import PROMPT_PROCESS_TEXT


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

    return {
        "status": "success",
        "items": [
            {
                "title": "Preview OpenAI brute",
                "content": ai_text,
                "tags": ["openai"],
                "labels": [],
                "zone": [],
                "country": [],
                "score": 0.0
            }
        ]
    }

