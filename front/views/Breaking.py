import base64
import json
import os
from io import BytesIO
from typing import Dict, Optional

import streamlit as st
from openai import OpenAI
from db.supabase_client import get_supabase
from prompts.breaking.generate_breaking_texts import PROMPT_GENERATE_BREAKING_TEXTS
from prompts.breaking.generate_breaking_image_prompts import PROMPT_GENERATE_BREAKING_IMAGE_PROMPT
from services.carousel.image_generation_service import generate_carousel_image
from services.carousel.breaking.carousel_slide_service import generate_cover_slide, generate_carousel_slide


BREAKING_BUCKET = "carousel-breaking"
BREAKING_SLIDES_BUCKET = "carousel-breaking-slides"
BREAKING_STATE_FILE = "breaking_state.json"


def _load_breaking_state() -> Dict[str, object]:
    supabase = get_supabase()
    try:
        data = supabase.storage.from_(BREAKING_SLIDES_BUCKET).download(BREAKING_STATE_FILE)
        if isinstance(data, bytes):
            return json.loads(data.decode("utf-8"))
    except Exception:
        pass
    return {
        "raw_text": "",
        "title_carou": "",
        "content_carou": "",
        "prompt_image_0": "",
        "prompt_image_1": "",
        "image_url_0": "",
        "image_url_1": "",
    }


def _save_breaking_state(state: Dict[str, object]) -> None:
    supabase = get_supabase()
    payload = json.dumps(state, ensure_ascii=False).encode("utf-8")
    supabase.storage.from_(BREAKING_SLIDES_BUCKET).upload(
        BREAKING_STATE_FILE,
        payload,
        file_options={"content-type": "application/json; charset=utf-8", "upsert": "true"},
    )


def _generate_breaking_text(raw_text: str) -> Dict[str, object]:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PROMPT_GENERATE_BREAKING_TEXTS},
            {"role": "user", "content": raw_text},
        ],
        temperature=0.6,
        response_format={"type": "json_object"},
        timeout=30,
    )
    content = response.choices[0].message.content or ""
    return json.loads(content)


def _generate_breaking_image_prompt(title: str, content: str) -> Dict[str, object]:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    user_input = f"TITRE: {title}\n\nCONTENU: {content}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PROMPT_GENERATE_BREAKING_IMAGE_PROMPT},
            {"role": "user", "content": user_input},
        ],
        temperature=0.6,
        response_format={"type": "json_object"},
        timeout=30,
    )
    content = response.choices[0].message.content or ""
    return json.loads(content)


def _upload_breaking_image(position: int, image_bytes: bytes) -> Optional[str]:
    supabase = get_supabase()
    filename = f"breaking_image_{position}.png"
    supabase.storage.from_(BREAKING_BUCKET).upload(
        filename,
        image_bytes,
        file_options={"content-type": "image/png", "upsert": "true"},
    )
    return supabase.storage.from_(BREAKING_BUCKET).get_public_url(filename)


def _with_cache_buster(url: str, token: str) -> str:
    if not url:
        return url
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}v={token}"


def _upload_breaking_slide(filename: str, image_bytes: bytes) -> Optional[str]:
    supabase = get_supabase()
    supabase.storage.from_(BREAKING_SLIDES_BUCKET).upload(
        filename,
        image_bytes,
        file_options={"content-type": "image/png", "upsert": "true"},
    )
    return supabase.storage.from_(BREAKING_SLIDES_BUCKET).get_public_url(filename)


def _generate_breaking_slides(state: Dict[str, object], title: str, content: str) -> None:
    if not state.get("image_url_0") or not state.get("image_url_1"):
        st.warning("Il faut générer les 2 images.")
        return
    if not title or not content:
        st.warning("Il faut un titre et un contenu.")
        return
    with st.spinner("Génération des slides..."):
        cover_bytes = generate_cover_slide(image_url=state["image_url_0"])
        slide1_bytes = generate_carousel_slide(
            title=title,
            content=content,
            image_url=state["image_url_1"],
        )
        _upload_breaking_slide("slide_0.png", cover_bytes)
        _upload_breaking_slide("slide_1.png", slide1_bytes)

        outro_path = os.path.join(
            os.path.dirname(__file__),
            "..", "layout", "assets", "carousel", "breaking", "outro.png",
        )
        if os.path.exists(outro_path):
            with open(outro_path, "rb") as f:
                _upload_breaking_slide("slide_outro.png", f.read())
    st.success("✅ Slides générées")


def _auto_generate_slides_if_ready(state: Dict[str, object], title: str, content: str) -> None:
    if state.get("image_url_0") and state.get("image_url_1") and title and content:
        _generate_breaking_slides(state, title, content)


st.title("⚡ Breaking")
st.divider()

# Charger l'état depuis storage
state = _load_breaking_state()

st.markdown("### Texte brut")
raw_text = st.text_area("Colle ton article", value=state.get("raw_text", ""), height=200)
state["raw_text"] = raw_text

if st.button("✨ Générer titre + contenu", use_container_width=True):
    if not raw_text.strip():
        st.warning("Colle un article d'abord.")
    else:
        with st.spinner("Génération en cours..."):
            result = _generate_breaking_text(raw_text)
        state["title_carou"] = result.get("title_carou", "")
        state["content_carou"] = result.get("content_carou", "")
        _save_breaking_state(state)
        st.success("✅ Titre + contenu générés")

        # Générer prompts + images automatiquement
        if state["title_carou"] and state["content_carou"]:
            with st.spinner("Génération des prompts + images..."):
                p = _generate_breaking_image_prompt(state["title_carou"], state["content_carou"])
                prompt = p.get("image_prompt", "")
                state["prompt_image_0"] = prompt
                state["prompt_image_1"] = prompt

                if prompt:
                    img0 = generate_carousel_image(prompt)
                    if img0.get("status") == "success":
                        image_bytes = base64.b64decode(img0["image_data"])
                        url0 = _upload_breaking_image(0, image_bytes) or ""
                        state["image_url_0"] = _with_cache_buster(url0, str(time.time()))
                    img1 = generate_carousel_image(prompt)
                    if img1.get("status") == "success":
                        image_bytes = base64.b64decode(img1["image_data"])
                        url1 = _upload_breaking_image(1, image_bytes) or ""
                        state["image_url_1"] = _with_cache_buster(url1, str(time.time()))
                _save_breaking_state(state)

            # Générer les slides automatiquement si images OK
            if state.get("image_url_0") and state.get("image_url_1"):
                _generate_breaking_slides(state, state["title_carou"], state["content_carou"])

st.markdown("### Résumé Breaking (éditable)")
title = st.text_input("Titre (clickbait)", value=state.get("title_carou", ""))
content = st.text_area("Content (2-3 phrases)", value=state.get("content_carou", ""), height=120)
if st.button("💾 Sauvegarder texte", use_container_width=True):
    state["title_carou"] = title
    state["content_carou"] = content
    _save_breaking_state(state)
    st.success("✅ Texte sauvegardé")
if st.button("🔄 Régénérer prompts + images", use_container_width=True):
    if not title or not content:
        st.warning("Il faut un titre et un contenu.")
    else:
        with st.spinner("Génération des prompts + images..."):
            p = _generate_breaking_image_prompt(title, content)
            prompt = p.get("image_prompt", "")
            state["prompt_image_0"] = prompt
            state["prompt_image_1"] = prompt
            if prompt:
                img0 = generate_carousel_image(prompt)
                if img0.get("status") == "success":
                    image_bytes = base64.b64decode(img0["image_data"])
                    state["image_url_0"] = _upload_breaking_image(0, image_bytes) or ""
                img1 = generate_carousel_image(prompt)
                if img1.get("status") == "success":
                    image_bytes = base64.b64decode(img1["image_data"])
                    state["image_url_1"] = _upload_breaking_image(1, image_bytes) or ""
            _save_breaking_state(state)
        _auto_generate_slides_if_ready(state, title, content)

st.divider()

st.markdown("### Prompts images")
st.caption("Prompts auto basés sur le titre + contenu.")
with st.expander("✍️ Voir/éditer les prompts (optionnel)", expanded=False):
    prompt0 = st.text_area("Prompt image 0 (cover)", value=state.get("prompt_image_0", ""), height=120)
    prompt1 = st.text_area("Prompt image 1 (slide)", value=state.get("prompt_image_1", ""), height=120)
    if st.button("💾 Sauvegarder prompts", use_container_width=True):
        state["prompt_image_0"] = prompt0
        state["prompt_image_1"] = prompt1
        _save_breaking_state(state)
        st.success("✅ Prompts sauvegardés")

st.divider()

st.markdown("### Images")
col_img0, col_img1 = st.columns(2)
with col_img0:
    if state.get("image_url_0"):
        st.image(state["image_url_0"], use_container_width=True)
    if st.button("🎨 Générer image 0", use_container_width=True):
        prompt0 = state.get("prompt_image_0", "")
        if not prompt0.strip():
            if not title or not content:
                st.warning("Il faut un titre et un contenu.")
                st.stop()
            with st.spinner("Génération du prompt 0..."):
                p0 = _generate_breaking_image_prompt(title, content)
            prompt0 = p0.get("image_prompt", "")
            state["prompt_image_0"] = prompt0
            _save_breaking_state(state)
        if not prompt0.strip():
            st.warning("Prompt image 0 vide.")
        else:
            with st.spinner("Génération image 0..."):
                result = generate_carousel_image(prompt0)
            if result.get("status") == "success":
                image_bytes = base64.b64decode(result["image_data"])
                url = _upload_breaking_image(0, image_bytes) or ""
                state["image_url_0"] = _with_cache_buster(url, str(time.time()))
                _save_breaking_state(state)
                st.success("✅ Image 0 générée")
                _auto_generate_slides_if_ready(state, title, content)
                st.rerun()
            else:
                st.error(result.get("message", "Erreur image 0"))
    with st.expander("✍️ Re-prompt image 0", expanded=False):
        manual_prompt_0 = st.text_area("Prompt manuel 0", key="breaking_manual_prompt_0", height=80)
        if st.button("🔄 Générer via prompt manuel 0", use_container_width=True):
            if not manual_prompt_0.strip():
                st.warning("Prompt manuel vide.")
            else:
                state["prompt_image_0"] = manual_prompt_0
                _save_breaking_state(state)
                with st.spinner("Génération image 0..."):
                    result = generate_carousel_image(manual_prompt_0)
                if result.get("status") == "success":
                    image_bytes = base64.b64decode(result["image_data"])
                    url = _upload_breaking_image(0, image_bytes) or ""
                    state["image_url_0"] = _with_cache_buster(url, str(time.time()))
                    _save_breaking_state(state)
                    st.success("✅ Image 0 générée")
                    _auto_generate_slides_if_ready(state, title, content)
                    st.rerun()
                else:
                    st.error(result.get("message", "Erreur image 0"))
    uploaded_0 = st.file_uploader("Charger une image 0", type=["png", "jpg", "jpeg"], key="breaking_upload_0")
    if uploaded_0 is not None:
        image_bytes = uploaded_0.read()
        url = _upload_breaking_image(0, image_bytes) or ""
        state["image_url_0"] = _with_cache_buster(url, str(time.time()))
        _save_breaking_state(state)
        st.success("✅ Image 0 chargée")
        _auto_generate_slides_if_ready(state, title, content)
        st.rerun()

with col_img1:
    if state.get("image_url_1"):
        st.image(state["image_url_1"], use_container_width=True)
    if st.button("🎨 Générer image 1", use_container_width=True):
        prompt1 = state.get("prompt_image_1", "")
        if not prompt1.strip():
            if not title or not content:
                st.warning("Il faut un titre et un contenu.")
                st.stop()
            with st.spinner("Génération du prompt 1..."):
                p1 = _generate_breaking_image_prompt(title, content)
            prompt1 = p1.get("image_prompt", "")
            state["prompt_image_1"] = prompt1
            _save_breaking_state(state)
        if not prompt1.strip():
            st.warning("Prompt image 1 vide.")
        else:
            with st.spinner("Génération image 1..."):
                result = generate_carousel_image(prompt1)
            if result.get("status") == "success":
                image_bytes = base64.b64decode(result["image_data"])
                url = _upload_breaking_image(1, image_bytes) or ""
                state["image_url_1"] = _with_cache_buster(url, str(time.time()))
                _save_breaking_state(state)
                st.success("✅ Image 1 générée")
                _auto_generate_slides_if_ready(state, title, content)
                st.rerun()
            else:
                st.error(result.get("message", "Erreur image 1"))
    with st.expander("✍️ Re-prompt image 1", expanded=False):
        manual_prompt_1 = st.text_area("Prompt manuel 1", key="breaking_manual_prompt_1", height=80)
        if st.button("🔄 Générer via prompt manuel 1", use_container_width=True):
            if not manual_prompt_1.strip():
                st.warning("Prompt manuel vide.")
            else:
                state["prompt_image_1"] = manual_prompt_1
                _save_breaking_state(state)
                with st.spinner("Génération image 1..."):
                    result = generate_carousel_image(manual_prompt_1)
                if result.get("status") == "success":
                    image_bytes = base64.b64decode(result["image_data"])
                    url = _upload_breaking_image(1, image_bytes) or ""
                    state["image_url_1"] = _with_cache_buster(url, str(time.time()))
                    _save_breaking_state(state)
                    st.success("✅ Image 1 générée")
                    _auto_generate_slides_if_ready(state, title, content)
                    st.rerun()
                else:
                    st.error(result.get("message", "Erreur image 1"))
    uploaded_1 = st.file_uploader("Charger une image 1", type=["png", "jpg", "jpeg"], key="breaking_upload_1")
    if uploaded_1 is not None:
        image_bytes = uploaded_1.read()
        url = _upload_breaking_image(1, image_bytes) or ""
        state["image_url_1"] = _with_cache_buster(url, str(time.time()))
        _save_breaking_state(state)
        st.success("✅ Image 1 chargée")
        _auto_generate_slides_if_ready(state, title, content)
        st.rerun()

st.divider()

st.markdown("### Slides")
if st.button("🖼️ Générer slides", use_container_width=True):
    _generate_breaking_slides(state, title, content)
    st.session_state["breaking_slides_cache_buster"] = str(time.time())
    st.rerun()

st.markdown("### Preview slides")
col_p0, col_p1, col_p2 = st.columns(3)
supabase = get_supabase()
slides_cache_buster = st.session_state.get("breaking_slides_cache_buster", "")
with col_p0:
    st.caption("Slide 0")
    url = supabase.storage.from_(BREAKING_SLIDES_BUCKET).get_public_url("slide_0.png")
    if url:
        st.image(_with_cache_buster(url, slides_cache_buster), use_container_width=True)
with col_p1:
    st.caption("Slide 1")
    url = supabase.storage.from_(BREAKING_SLIDES_BUCKET).get_public_url("slide_1.png")
    if url:
        st.image(_with_cache_buster(url, slides_cache_buster), use_container_width=True)
with col_p2:
    st.caption("Outro")
    url = supabase.storage.from_(BREAKING_SLIDES_BUCKET).get_public_url("slide_outro.png")
    if url:
        st.image(_with_cache_buster(url, slides_cache_buster), use_container_width=True)
