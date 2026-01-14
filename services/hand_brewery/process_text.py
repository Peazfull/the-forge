import streamlit as st
import openai   

def process_text(text: str) -> dict:
    """
    Étape 1 du Hand Brewery (TEXTE)

    - Reçoit du texte brut
    - (plus tard) enverra le texte à l'IA
    - Retourne un JSON structuré (mock pour l’instant)
    """
    

    if "OPENAI_API_KEY" not in st.secrets:
        return {
            "status": "error",
            "message": "OPENAI_API_KEY missing in secrets",
            "items": []
        }

