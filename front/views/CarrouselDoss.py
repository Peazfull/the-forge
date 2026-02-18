import base64
import time
import json
import os
import io
import zipfile
import hashlib
from io import BytesIO
from typing import Dict, Optional
import re
from datetime import datetime

import streamlit as st
from PIL import Image
from db.supabase_client import get_supabase
from services.carousel.doss.generate_doss_texts_service import generate_doss_image
from services.carousel.doss.generate_doss_texts_service import (
    generate_doss_texts,
    generate_doss_image_prompt,
    generate_doss_images_parallel,
)
from services.carousel.doss.doss_slide_service import generate_doss_slide, generate_cover_slide
from services.carousel.doss.generate_doss_caption_service import (
    generate_caption_from_doss,
    upload_caption_text,
    read_caption_text,
    generate_linkedin_from_doss,
    upload_linkedin_text,
    read_linkedin_text,
)
from services.utils.email_service import send_email_with_attachments


DOSS_BUCKET = "carousel-doss"
DOSS_SLIDES_BUCKET = "carousel-doss-slides"
DOSS_STATE_FILE = "doss_state.json"


def _load_doss_state() -> Dict[str, object]:
    supabase = get_supabase()
    try:
        data = supabase.storage.from_(DOSS_SLIDES_BUCKET).download(DOSS_STATE_FILE)
        if isinstance(data, bytes):
            return json.loads(data.decode("utf-8"))
    except Exception:
        pass
    return {
        "raw_text": "",
        "slide0_hook": "",
        "slide1_title": "",
        "slide1_content": "",
        "slide2_content": "",
        "slide3_content": "",
        "slide4_content": "",
        "prompt_image_0": "",
        "prompt_image_1": "",
        "prompt_image_2": "",
        "prompt_image_3": "",
        "prompt_image_4": "",
        "image_url_0": "",
        "image_url_1": "",
        "image_url_2": "",
        "image_url_3": "",
        "image_url_4": "",
    }


def _save_doss_state(state: Dict[str, object]) -> None:
    supabase = get_supabase()
    payload = json.dumps(state, ensure_ascii=False).encode("utf-8")
    supabase.storage.from_(DOSS_SLIDES_BUCKET).upload(
        DOSS_STATE_FILE,
        payload,
        file_options={"content-type": "application/json; charset=utf-8", "upsert": "true"},
    )


def _with_cache_buster(url: str, token: str) -> str:
    if not url:
        return url
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}v={token}"


def _compute_doss_texts_hash(
    raw_text: str,
    slide0_hook: str,
    slide1_title: str,
    slide1_content: str,
    slide2_content: str,
    slide3_content: str,
    slide4_content: str,
) -> str:
    payload = "|".join([
        raw_text or "",
        slide0_hook or "",
        slide1_title or "",
        slide1_content or "",
        slide2_content or "",
        slide3_content or "",
        slide4_content or "",
    ])
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def _strip_fixed_title_prefix(text: str, fixed_title: str) -> str:
    if not text:
        return ""
    pattern = rf"^\s*{re.escape(fixed_title)}\s*[:\-–—]?\s*"
    return re.sub(pattern, "", text, flags=re.IGNORECASE).strip()


def _ensure_highlight(text: str, max_words: int = 3) -> str:
    if not text or "**" in text:
        return text
    words = text.split()
    if len(words) < 2:
        return text
    take = min(max_words, len(words))
    highlighted = " ".join(words[:take])
    return f"**{highlighted}** " + " ".join(words[take:])


def _sync_doss_texts(
    state: Dict[str, object],
    slide0_hook: str,
    slide1_title: str,
    slide1_content: str,
    slide2_content: str,
    slide3_content: str,
    slide4_content: str,
) -> None:
    state["slide0_hook"] = slide0_hook
    state["slide1_title"] = slide1_title
    state["slide1_content"] = slide1_content
    state["slide2_content"] = _strip_fixed_title_prefix(slide2_content, "DANS LES FAITS")
    state["slide3_content"] = _strip_fixed_title_prefix(slide3_content, "CE QU'IL FAUT SAVOIR")
    state["slide4_content"] = _strip_fixed_title_prefix(slide4_content, "CE QUE ÇA CHANGE")


def _upload_doss_image(position: int, image_bytes: bytes) -> Optional[str]:
    supabase = get_supabase()
    filename = f"doss_image_{position}.png"
    try:
        supabase.storage.from_(DOSS_BUCKET).upload(
            filename,
            image_bytes,
            file_options={"content-type": "image/png", "upsert": "true"},
        )
        return supabase.storage.from_(DOSS_BUCKET).get_public_url(filename)
    except Exception:
        return None


def _upload_doss_slide(filename: str, image_bytes: bytes) -> Optional[str]:
    supabase = get_supabase()
    supabase.storage.from_(DOSS_SLIDES_BUCKET).upload(
        filename,
        image_bytes,
        file_options={"content-type": "image/png", "upsert": "true"},
    )
    return supabase.storage.from_(DOSS_SLIDES_BUCKET).get_public_url(filename)


def _get_doss_image_url(position: int) -> str:
    supabase = get_supabase()
    filename = f"doss_image_{position}.png"
    return supabase.storage.from_(DOSS_BUCKET).get_public_url(filename)


def _clear_doss_slide_files() -> None:
    supabase = get_supabase()
    try:
        items = supabase.storage.from_(DOSS_SLIDES_BUCKET).list()
        files = [
            item.get("name")
            for item in items
            if item.get("name") and item.get("name") != DOSS_STATE_FILE
        ]
        if files:
            supabase.storage.from_(DOSS_SLIDES_BUCKET).remove(files)
    except Exception:
        pass


def _download_doss_slide(filename: str) -> Optional[bytes]:
    supabase = get_supabase()
    try:
        data = supabase.storage.from_(DOSS_SLIDES_BUCKET).download(filename)
        if isinstance(data, bytes):
            return data
        return None
    except Exception:
        return None


def build_doss_exports() -> Dict[str, object]:
    slides = []
    for name in ["slide_0.png", "slide_1.png", "slide_2.png", "slide_3.png", "slide_4.png", "slide_outro.png"]:
        data = _download_doss_slide(name)
        if data:
            slides.append((name, data))
    if not slides:
        return {"zip": b"", "pdf": b"", "count": 0}

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, data in slides:
            zf.writestr(filename, data)
    zip_buffer.seek(0)

    images = []
    for _, data in slides:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        images.append(img)
    pdf_buffer = io.BytesIO()
    if images:
        images[0].save(
            pdf_buffer,
            format="PDF",
            save_all=True,
            append_images=images[1:],
            resolution=300,
            quality=95,
            subsampling=0,
            dpi=(300, 300),
        )
    pdf_buffer.seek(0)

    return {
        "zip": zip_buffer.getvalue(),
        "pdf": pdf_buffer.getvalue(),
        "count": len(slides),
    }


def _generate_doss_slides(state: Dict[str, object]) -> None:
    # Fallback: recharger les URLs images depuis le storage si elles manquent
    for idx in range(0, 5):
        key = f"image_url_{idx}"
        if not state.get(key):
            state[key] = _get_doss_image_url(idx)
    required = ["image_url_0", "image_url_1", "image_url_2", "image_url_3", "image_url_4"]
    if any(not state.get(k) for k in required):
        st.warning("Il faut générer les 5 images (cover + 4 slides).")
        return

    with st.spinner("Génération des slides..."):
        _clear_doss_slide_files()
        
        # Slide 0 (cover) avec hook
        hook = state.get("slide0_hook", "")
        image_url_0 = state.get("image_url_0")
        if hook and image_url_0:
            cover_bytes = generate_cover_slide(hook=hook, image_url=image_url_0)
            _upload_doss_slide("slide_0.png", cover_bytes)
        
        # Slides 1-4
        slide_data = [
            (1, "slide_1.png", state.get("slide1_title", ""), state.get("slide1_content", ""), state.get("image_url_1")),
            (2, "slide_2.png", "DANS LES FAITS", state.get("slide2_content", ""), state.get("image_url_2")),
            (3, "slide_3.png", "CE QU'IL FAUT SAVOIR", state.get("slide3_content", ""), state.get("image_url_3")),
            (4, "slide_4.png", "CE QUE ÇA CHANGE", state.get("slide4_content", ""), state.get("image_url_4")),
        ]

        for position, filename, title, content, image_url in slide_data:
            if not title or not content or not image_url:
                continue
            slide_bytes = generate_doss_slide(title=title, content=content, image_url=image_url, position=position)
            _upload_doss_slide(filename, slide_bytes)
        
        # Outro
        assets_dir = os.path.join(
            os.path.dirname(__file__), "..", "layout", "assets", "carousel", "doss"
        )
        outro_path = os.path.join(assets_dir, "outro_doss.png")
        if os.path.exists(outro_path):
            with open(outro_path, "rb") as f:
                outro_bytes = f.read()
            _upload_doss_slide("slide_outro.png", outro_bytes)
            
    st.success("✅ Slides générées (cover + 4 slides + outro)")


st.title("TheArtist - Doss")
st.divider()

state = _load_doss_state()

st.markdown("### Texte brut")
raw_text = st.text_area("Colle ton article", value=state.get("raw_text", ""), height=200)
state["raw_text"] = raw_text

if st.button("✨ Générer titres + contenus", use_container_width=True):
    if not raw_text.strip():
        st.warning("Colle un article d'abord.")
    else:
        with st.spinner("Génération en cours..."):
            result = generate_doss_texts(raw_text)
        if result.get("status") == "success":
            data = result["data"]
            state["slide0_hook"] = data.get("slide0_hook", "")
            state["slide1_title"] = data.get("slide1_title", "")
            state["slide1_content"] = _ensure_highlight(data.get("slide1_content", ""))
            state["slide2_content"] = _strip_fixed_title_prefix(
                _ensure_highlight(data.get("slide2_content", "")), "DANS LES FAITS"
            )
            state["slide3_content"] = _strip_fixed_title_prefix(
                _ensure_highlight(data.get("slide3_content", "")), "CE QU'IL FAUT SAVOIR"
            )
            state["slide4_content"] = _strip_fixed_title_prefix(
                _ensure_highlight(data.get("slide4_content", "")), "CE QUE ÇA CHANGE"
            )
            _save_doss_state(state)
            st.success("✅ Textes générés")

            with st.spinner("Génération des prompts images..."):
                p = generate_doss_image_prompt(state["slide1_title"], state["slide1_content"])
                prompt = p.get("image_prompt", "")
                for idx in range(0, 5):
                    state[f"prompt_image_{idx}"] = prompt
                _save_doss_state(state)
            st.success("✅ Prompts images générés")
        else:
            st.error(result.get("message", "Erreur de génération"))

st.markdown("### Textes Doss (éditables)")
slide0_hook = st.text_input("Slide 0 · Hook (6-8 mots)", value=state.get("slide0_hook", ""))
slide1_title = st.text_input("Slide 1 · Titre clickbait", value=state.get("slide1_title", ""))
slide1_content = st.text_area("Slide 1 · Content", value=state.get("slide1_content", ""), height=120)
slide2_content = st.text_area(
    "Slide 2 · Content (On vous explique)",
    value=_strip_fixed_title_prefix(state.get("slide2_content", ""), "DANS LES FAITS"),
    height=120
)
slide3_content = st.text_area(
    "Slide 3 · Content (De plus)",
    value=_strip_fixed_title_prefix(state.get("slide3_content", ""), "CE QU'IL FAUT SAVOIR"),
    height=120
)
slide4_content = st.text_area(
    "Slide 4 · Content (En gros)",
    value=_strip_fixed_title_prefix(state.get("slide4_content", ""), "CE QUE ÇA CHANGE"),
    height=120
)

# Autosave textes pour éviter la perte après refresh
autosave_hash = _compute_doss_texts_hash(
    raw_text,
    slide0_hook,
    slide1_title,
    slide1_content,
    slide2_content,
    slide3_content,
    slide4_content,
)
if st.session_state.get("doss_autosave_hash") != autosave_hash:
    _sync_doss_texts(
        state,
        slide0_hook,
        slide1_title,
        slide1_content,
        slide2_content,
        slide3_content,
        slide4_content,
    )
    state["raw_text"] = raw_text
    _save_doss_state(state)
    st.session_state.doss_autosave_hash = autosave_hash

if st.button("💾 Sauvegarder textes", use_container_width=True):
    _sync_doss_texts(
        state,
        slide0_hook,
        slide1_title,
        slide1_content,
        slide2_content,
        slide3_content,
        slide4_content,
    )
    _save_doss_state(state)
    st.success("✅ Textes sauvegardés")

if st.button("🔄 Regénérer les prompts images", use_container_width=True):
    if not state.get("slide1_title") or not state.get("slide1_content"):
        st.warning("⚠️ Génère d'abord les textes ou saisis un titre et contenu pour Slide 1.")
    else:
        with st.spinner("Régénération des prompts images..."):
            p = generate_doss_image_prompt(state["slide1_title"], state["slide1_content"])
            prompt = p.get("image_prompt", "")
            for idx in range(0, 5):
                state[f"prompt_image_{idx}"] = prompt
            _save_doss_state(state)
        st.success("✅ Prompts images régénérés avec le nouveau système !")
        st.rerun()

with st.expander("✍️ Prompts images (éditables)", expanded=False):
    p0 = st.text_area("Prompt image 0 (cover)", value=state.get("prompt_image_0", ""), height=100)
    p1 = st.text_area("Prompt image 1", value=state.get("prompt_image_1", ""), height=100)
    p2 = st.text_area("Prompt image 2", value=state.get("prompt_image_2", ""), height=100)
    p3 = st.text_area("Prompt image 3", value=state.get("prompt_image_3", ""), height=100)
    p4 = st.text_area("Prompt image 4", value=state.get("prompt_image_4", ""), height=100)

    col_save_prompts, col_regen_prompts = st.columns(2)
    with col_save_prompts:
        if st.button("💾 Sauvegarder prompts", use_container_width=True):
            state["prompt_image_0"] = p0
            state["prompt_image_1"] = p1
            state["prompt_image_2"] = p2
            state["prompt_image_3"] = p3
            state["prompt_image_4"] = p4
            _save_doss_state(state)
            st.success("✅ Prompts sauvegardés")
    with col_regen_prompts:
        if st.button("✨ Régénérer prompts", use_container_width=True):
            with st.spinner("Génération du prompt global..."):
                p = generate_doss_image_prompt(slide1_title, slide1_content)
                prompt = p.get("image_prompt", "")
                for idx in range(0, 5):
                    state[f"prompt_image_{idx}"] = prompt
                _save_doss_state(state)
            st.success("✅ Prompts régénérés")

st.divider()
st.markdown("### Images")

if st.button("🚀 Générer images + slides", use_container_width=True):
    _sync_doss_texts(
        state,
        slide0_hook,
        slide1_title,
        slide1_content,
        slide2_content,
        slide3_content,
        slide4_content,
    )
    _save_doss_state(state)
    
    slides = [
        (0, "HOOK", slide0_hook),
        (1, slide1_title, slide1_content),
        (2, "DANS LES FAITS", slide2_content),
        (3, "CE QU'IL FAUT SAVOIR", slide3_content),
        (4, "CE QUE ÇA CHANGE", slide4_content),
    ]
    
    # Conteneur pour afficher la progression
    progress_placeholder = st.empty()
    progress_bar = st.progress(0.0)
    
    def progress_callback(current: int, total: int):
        """Callback pour afficher la progression en temps réel"""
        progress = current / total
        progress_bar.progress(progress)
        progress_placeholder.info(f"⚡ Génération en parallèle : {current}/{total} images générées")
    
    with st.spinner("⚡ Génération des 5 images en parallèle..."):
        image_results = generate_doss_images_parallel(
            state=state,
            slide_data=slides,
            upload_callback=_upload_doss_image,
            progress_callback=progress_callback
        )
    
    # Mettre à jour les URLs dans le state
    cache_buster_value = str(time.time())
    for idx, url in image_results.items():
        if url:
            state[f"image_url_{idx}"] = _with_cache_buster(url, cache_buster_value)
    
    st.session_state.doss_images_cache_buster = cache_buster_value
    _save_doss_state(state)
    
    # Générer les slides
    progress_placeholder.empty()
    progress_bar.empty()
    _generate_doss_slides(state)
    st.session_state["doss_slides_cache_buster"] = str(time.time())
    st.success(f"✅ {len(image_results)} images + slides générées en parallèle !")
    st.rerun()

image_cards = [
    (0, "Slide 0 (Cover)", slide0_hook, ""),
    (1, "Slide 1", slide1_title, slide1_content),
    (2, "Slide 2", "DANS LES FAITS", slide2_content),
    (3, "Slide 3", "CE QU'IL FAUT SAVOIR", slide3_content),
    (4, "Slide 4", "CE QUE ÇA CHANGE", slide4_content),
]

for row_idx in range(0, len(image_cards), 2):
    cols = st.columns(2)
    for col, (idx, label, title, content) in zip(cols, image_cards[row_idx:row_idx + 2]):
        with col:
            st.markdown(f"#### {label}")
            image_url = state.get(f"image_url_{idx}") or _get_doss_image_url(idx)
            cache_buster = st.session_state.get("doss_images_cache_buster", "")
            if image_url:
                st.image(_with_cache_buster(image_url, cache_buster), use_container_width=True)

            if st.button(f"🎨 Générer image {idx}", use_container_width=True, key=f"gen_image_{idx}"):
                _sync_doss_texts(
                    state,
                    slide1_title,
                    slide1_content,
                    slide2_content,
                    slide3_content,
                    slide4_content,
                )
                _save_doss_state(state)
                prompt = state.get(f"prompt_image_{idx}", "")
                if not prompt:
                    p = generate_doss_image_prompt(title, content)
                    prompt = p.get("image_prompt", "")
                    state[f"prompt_image_{idx}"] = prompt
                if prompt:
                    with st.spinner(f"Génération image {idx}..."):
                        result = generate_doss_image(prompt)
                    if result.get("status") == "success":
                        image_bytes = base64.b64decode(result["image_data"])
                        url = _upload_doss_image(idx, image_bytes)
                        if url:
                            state[f"image_url_{idx}"] = _with_cache_buster(url, str(time.time()))
                            _save_doss_state(state)
                            st.session_state.doss_images_cache_buster = str(time.time())
                            st.success(f"✅ Image {idx} générée")
                            st.rerun()
                        else:
                            st.error("❌ Upload storage échoué")
                            st.warning("Upload non persisté : l'image sera perdue au refresh.")
                    else:
                        st.error(result.get("message", f"Erreur image {idx}"))
                else:
                    st.warning("Prompt image vide.")

            uploaded = st.file_uploader(
                f"Charger une image {idx}",
                type=["png", "jpg", "jpeg"],
                key=f"upload_doss_{idx}",
            )
            if uploaded is not None:
                _sync_doss_texts(
                    state,
                    slide0_hook,
                    slide1_title,
                    slide1_content,
                    slide2_content,
                    slide3_content,
                    slide4_content,
                )
                _save_doss_state(state)
                image_bytes = uploaded.read()
                url = _upload_doss_image(idx, image_bytes)
                if url:
                    state[f"image_url_{idx}"] = _with_cache_buster(url, str(time.time()))
                    _save_doss_state(state)
                    st.session_state.doss_images_cache_buster = str(time.time())
                    st.success(f"✅ Image {idx} chargée")
                    st.rerun()
                else:
                    st.error("❌ Upload storage échoué")
                    st.warning("Upload non persisté : l'image sera perdue au refresh.")

st.divider()
st.markdown("### Slides")

col_clear, col_gen = st.columns(2)
with col_clear:
    if st.button("🗑️ Clear slides", use_container_width=True):
        _clear_doss_slide_files()
        st.session_state["doss_slides_cache_buster"] = str(time.time())
        st.success("✅ Slides supprimées")
        st.rerun()

with col_gen:
    if st.button("🖼️ Générer slides", use_container_width=True):
        _generate_doss_slides(state)
        st.session_state["doss_slides_cache_buster"] = str(time.time())
        st.rerun()

st.markdown("### Preview slides")
slides_cache_buster = st.session_state.get("doss_slides_cache_buster", "")
col_a, col_b = st.columns(2)
with col_a:
    st.caption("Slide 0 (Cover)")
    url = get_supabase().storage.from_(DOSS_SLIDES_BUCKET).get_public_url("slide_0.png")
    if url:
        st.image(_with_cache_buster(url, slides_cache_buster), use_container_width=True)
    st.caption("Slide 2")
    url = get_supabase().storage.from_(DOSS_SLIDES_BUCKET).get_public_url("slide_2.png")
    if url:
        st.image(_with_cache_buster(url, slides_cache_buster), use_container_width=True)
    st.caption("Slide 4")
    url = get_supabase().storage.from_(DOSS_SLIDES_BUCKET).get_public_url("slide_4.png")
    if url:
        st.image(_with_cache_buster(url, slides_cache_buster), use_container_width=True)
with col_b:
    st.caption("Slide 1")
    url = get_supabase().storage.from_(DOSS_SLIDES_BUCKET).get_public_url("slide_1.png")
    if url:
        st.image(_with_cache_buster(url, slides_cache_buster), use_container_width=True)
    st.caption("Slide 3")
    url = get_supabase().storage.from_(DOSS_SLIDES_BUCKET).get_public_url("slide_3.png")
    if url:
        st.image(_with_cache_buster(url, slides_cache_buster), use_container_width=True)
    st.caption("Outro")
    url = get_supabase().storage.from_(DOSS_SLIDES_BUCKET).get_public_url("slide_outro.png")
    if url:
        st.image(_with_cache_buster(url, slides_cache_buster), use_container_width=True)

st.divider()
if st.button("📦 Préparer export Doss", use_container_width=True):
    with st.spinner("Préparation de l'export..."):
        export_data = build_doss_exports()
    st.session_state.doss_export_zip = export_data["zip"]
    st.session_state.doss_export_pdf = export_data["pdf"]
    st.session_state.doss_export_count = export_data["count"]

if st.session_state.get("doss_export_zip"):
    if st.session_state.get("doss_export_count", 0) == 0:
        st.warning("Aucune slide disponible pour l'export.")
    else:
        st.caption(f"{st.session_state.get('doss_export_count', 0)} slides prêtes")
        st.download_button(
            "⬇️ Télécharger PNG (ZIP)",
            data=st.session_state.doss_export_zip,
            file_name="doss_slides.zip",
            mime="application/zip",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Télécharger PDF",
            data=st.session_state.doss_export_pdf,
            file_name="doss_slides.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

st.markdown("#### Export Email")
if st.button("✉️ Envoyer par email", use_container_width=True):
    try:
        export_data = build_doss_exports()
        if export_data.get("count", 0) == 0:
            st.warning("Aucune slide disponible pour l'envoi.")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            subject = f"Doss - {date_str}"
            caption_text = st.session_state.get("doss_caption_text_area", "").strip() or read_caption_text()
            body = caption_text or "Caption non disponible."
            attachments = [
                ("doss_slides.zip", export_data["zip"], "application/zip"),
                ("doss_slides.pdf", export_data["pdf"], "application/pdf"),
            ]
            send_email_with_attachments(
                to_email="gaelpons@hotmail.com",
                subject=subject,
                body=body,
                attachments=attachments,
            )
            st.success("✅ Email envoyé")
    except Exception as e:
        st.error(f"Erreur email : {str(e)[:120]}")

with st.expander("📝 Caption Instagram", expanded=False):
    if "doss_caption_text_area" not in st.session_state:
        st.session_state.doss_caption_text_area = read_caption_text() or ""

    col_gen, col_save = st.columns(2)
    with col_gen:
        if st.button("✨ Générer caption", use_container_width=True):
            if not slide1_title or not slide1_content:
                st.warning("Il faut un titre et un contenu.")
            else:
                with st.spinner("Génération de la caption..."):
                    result = generate_caption_from_doss(slide1_title, slide1_content)
                if result.get("status") == "success":
                    st.session_state.doss_caption_text_area = result["caption"]
                    upload_caption_text(st.session_state.doss_caption_text_area)
                else:
                    st.error(f"Erreur : {result.get('message', 'Erreur inconnue')}")
    with col_save:
        if st.button("💾 Sauvegarder caption", use_container_width=True):
            if st.session_state.doss_caption_text_area.strip():
                upload_caption_text(st.session_state.doss_caption_text_area)
                st.success("✅ Caption sauvegardée")
            else:
                st.warning("Caption vide.")

    caption_value = st.session_state.get("doss_caption_text_area", "")
    char_count = len(caption_value)
    st.text_area(
        label=f"Caption Instagram · {char_count} caractères",
        height=220,
        key="doss_caption_text_area",
        placeholder="Clique sur 'Générer caption' pour démarrer...",
    )

    safe_caption = caption_value.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    st.components.v1.html(
        f"""
        <button style="width:100%;padding:0.4rem;border-radius:8px;border:1px solid #ddd;cursor:pointer;">
          📋 Copier la caption
        </button>
        <script>
          const btn = document.currentScript.previousElementSibling;
          btn.addEventListener('click', async () => {{
            try {{
              await navigator.clipboard.writeText(`{safe_caption}`);
              btn.innerText = "✅ Caption copiée";
              setTimeout(() => btn.innerText = "📋 Copier la caption", 1500);
            }} catch (e) {{
              btn.innerText = "❌ Copie impossible";
              setTimeout(() => btn.innerText = "📋 Copier la caption", 1500);
            }}
          }});
        </script>
        """,
        height=55,
    )

with st.expander("💼 Post LinkedIn", expanded=False):
    if "doss_linkedin_text_area" not in st.session_state:
        st.session_state.doss_linkedin_text_area = read_linkedin_text() or ""

    col_gen, col_save = st.columns(2)
    with col_gen:
        if st.button("✨ Générer post LinkedIn", use_container_width=True):
            if not slide1_title or not slide1_content:
                st.warning("Il faut un titre et un contenu.")
            else:
                with st.spinner("Génération du post LinkedIn..."):
                    result = generate_linkedin_from_doss(slide1_title, slide1_content)
                if result.get("status") == "success":
                    st.session_state.doss_linkedin_text_area = result["text"]
                    upload_linkedin_text(st.session_state.doss_linkedin_text_area)
                else:
                    st.error(f"Erreur : {result.get('message', 'Erreur inconnue')}")
    with col_save:
        if st.button("💾 Sauvegarder post LinkedIn", use_container_width=True):
            if st.session_state.doss_linkedin_text_area.strip():
                upload_linkedin_text(st.session_state.doss_linkedin_text_area)
                st.success("✅ Post LinkedIn sauvegardé")
            else:
                st.warning("Post LinkedIn vide.")

    linkedin_value = st.session_state.get("doss_linkedin_text_area", "")
    linkedin_char_count = len(linkedin_value)
    st.text_area(
        label=f"Post LinkedIn · {linkedin_char_count} caractères",
        height=220,
        key="doss_linkedin_text_area",
        placeholder="Clique sur 'Générer post LinkedIn' pour démarrer...",
    )

    safe_linkedin = linkedin_value.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    st.components.v1.html(
        f"""
        <button style="width:100%;padding:0.4rem;border-radius:8px;border:1px solid #ddd;cursor:pointer;">
          📋 Copier le post LinkedIn
        </button>
        <script>
          const btn = document.currentScript.previousElementSibling;
          btn.addEventListener('click', async () => {{
            try {{
              await navigator.clipboard.writeText(`{safe_linkedin}`);
              btn.innerText = "✅ Post copié";
              setTimeout(() => btn.innerText = "📋 Copier le post LinkedIn", 1500);
            }} catch (e) {{
              btn.innerText = "❌ Copie impossible";
              setTimeout(() => btn.innerText = "📋 Copier le post LinkedIn", 1500);
            }}
          }});
        </script>
        """,
        height=55,
    )
