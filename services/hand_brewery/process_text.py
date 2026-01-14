import streamlit as st
from openai import OpenAI

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
                "content": "Tu es un assistant qui reformule un texte de façon claire."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0.3,
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

