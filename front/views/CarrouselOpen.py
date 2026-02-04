import io
import os
import re
import zipfile
from datetime import datetime

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from services.utils.email_service import send_email_with_attachments


ASSETS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "layout", "assets", "carousel", "open"
)
FONT_BOLD_PATH = os.path.join(ASSETS_DIR, "Manrope-Bold.ttf")
DATE_FONT_SIZE = 46
DATE_TOP = 850
DATE_FILL = "#F6F6F6"
DATE_HIGHLIGHT_BG = "#5B2EFF"
DATE_HIGHLIGHT_PAD_X = 10
DATE_HIGHLIGHT_PAD_Y = 6
CAPTION_FILE = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "prompts", "open", "fixed_caption.txt"
)


def _load_fixed_caption() -> str:
    try:
        with open(CAPTION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def _sorted_slide_files() -> list[tuple[str, str]]:
    if not os.path.exists(ASSETS_DIR):
        return []
    files = [
        name for name in os.listdir(ASSETS_DIR)
        if name.lower().endswith(".png")
        and re.search(r"(?:^|[_\s-])slide\s*\d+", name, re.IGNORECASE)
    ]
    if not files:
        return []

    def _key(name: str) -> tuple[int, str]:
        match = re.search(r"slide[_\s-]?(\d+)", name, re.IGNORECASE)
        num = int(match.group(1)) if match else 999
        return (num, name)

    files.sort(key=_key)
    return [(name, os.path.join(ASSETS_DIR, name)) for name in files]


def _format_french_date(dt: datetime | None = None) -> str:
    if dt is None:
        dt = datetime.now()
    months = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]
    return f"{dt.day:02d} {months[dt.month - 1]} {dt.year}"


def _load_font(path: str, size: int) -> ImageFont.ImageFont:
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            return ImageFont.load_default()
    return ImageFont.load_default()


def _render_slide_bytes(filename: str, path: str) -> bytes:
    img = Image.open(path).convert("RGBA")
    match = re.search(r"slide[_\s-]?(\d+)", filename, re.IGNORECASE)
    slide_number = int(match.group(1)) if match else None
    if slide_number == 1:
        draw = ImageDraw.Draw(img)
        date_text = _format_french_date()
        font = _load_font(FONT_BOLD_PATH, DATE_FONT_SIZE)
        text_width = draw.textlength(date_text, font=font)
        text_height = int(DATE_FONT_SIZE * 1.2)
        x = (img.size[0] - text_width) // 2
        rect = (
            x - DATE_HIGHLIGHT_PAD_X,
            DATE_TOP - DATE_HIGHLIGHT_PAD_Y,
            x + text_width + DATE_HIGHLIGHT_PAD_X,
            DATE_TOP + text_height + DATE_HIGHLIGHT_PAD_Y,
        )
        draw.rectangle(rect, fill=DATE_HIGHLIGHT_BG)
        draw.text((x, DATE_TOP), date_text, font=font, fill=DATE_FILL)
    output = io.BytesIO()
    img.convert("RGB").save(output, format="PNG")
    return output.getvalue()


def build_open_exports(slide_paths: list[tuple[str, str]]) -> dict[str, object]:
    slides = []
    for filename, path in slide_paths:
        try:
            slide_bytes = _render_slide_bytes(filename, path)
            slides.append((filename, slide_bytes))
        except Exception:
            continue

    # ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, data in slides:
            zf.writestr(filename, data)
    zip_buffer.seek(0)

    # PDF
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


st.title("TheArtist - Open")
st.divider()

slide_files = _sorted_slide_files()
if not slide_files:
    st.warning("Aucune slide trouvée dans les assets (fichiers slide_*.png).")

st.markdown("### Preview slides")
if slide_files:
    cols = None
    for idx, (filename, path) in enumerate(slide_files):
        if idx % 3 == 0:
            cols = st.columns(3)
        col = cols[idx % 3]
        with col:
            st.caption(filename)
            try:
                slide_bytes = _render_slide_bytes(filename, path)
                st.image(slide_bytes, use_container_width=True)
            except Exception:
                st.image(path, use_container_width=True)

st.divider()
if st.button("📦 Préparer export Open", use_container_width=True):
    export_data = build_open_exports(slide_files)
    st.session_state.open_export_zip = export_data["zip"]
    st.session_state.open_export_pdf = export_data["pdf"]
    st.session_state.open_export_count = export_data["count"]

if st.session_state.get("open_export_zip"):
    if st.session_state.get("open_export_count", 0) == 0:
        st.warning("Aucune slide disponible pour l'export.")
    else:
        st.caption(f"{st.session_state.get('open_export_count', 0)} slides prêtes")
        st.download_button(
            "⬇️ Télécharger PNG (ZIP)",
            data=st.session_state.open_export_zip,
            file_name="open_slides.zip",
            mime="application/zip",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Télécharger PDF",
            data=st.session_state.open_export_pdf,
            file_name="open_slides.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

st.markdown("#### Export Email")
if st.button("✉️ Envoyer par email", use_container_width=True):
    try:
        export_data = build_open_exports(slide_files)
        if export_data.get("count", 0) == 0:
            st.warning("Aucune slide disponible pour l'envoi.")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            subject = f"Open - {date_str}"
            caption_text = _load_fixed_caption() or "Caption non disponible."
            attachments = [
                ("open_slides.zip", export_data["zip"], "application/zip"),
                ("open_slides.pdf", export_data["pdf"], "application/pdf"),
            ]
            send_email_with_attachments(
                to_email="gaelpons@hotmail.com",
                subject=subject,
                body=caption_text,
                attachments=attachments,
            )
            st.success("✅ Email envoyé")
    except Exception as e:
        st.error(f"Erreur email : {str(e)[:120]}")

with st.expander("📝 Caption Instagram", expanded=False):
    caption_text = _load_fixed_caption()
    if not caption_text:
        caption_text = "CAPTION OPEN - A REMPLACER"
        st.warning("Caption fixe manquante : utilise le fichier prompts/open/fixed_caption.txt")

    st.text_area(
        label=f"Caption Instagram · {len(caption_text)} caractères",
        height=220,
        value=caption_text,
        disabled=True,
    )

    safe_caption = caption_text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
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
