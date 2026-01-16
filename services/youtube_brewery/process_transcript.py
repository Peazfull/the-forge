import json

import streamlit as st
from openai import OpenAI

from prompts.youtube_brewery.clean_text import PROMPT_CLEAN_TEXT
from prompts.youtube_brewery.jsonfy import PROMPT_JSONFY
from prompts.youtube_brewery.json_secure import PROMPT_JSON_SECURE


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def process_transcript(text: str) -> dict:
    if not text or not text.strip():
        return {
            "status": "error",
            "message": "Empty transcript",
            "items": []
        }

    try:
        response_clean = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_CLEAN_TEXT},
                {"role": "user", "content": text}
            ],
            temperature=0.4
        )

        clean_text = response_clean.choices[0].message.content

        response_jsonfy = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_JSONFY},
                {"role": "user", "content": clean_text}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        raw_json = response_jsonfy.choices[0].message.content

        response_secure = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_JSON_SECURE},
                {"role": "user", "content": raw_json}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        secure_json = response_secure.choices[0].message.content
        data = json.loads(secure_json)

        return {
            "status": "success",
            "items": data.get("items", [])
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "items": []
        }
