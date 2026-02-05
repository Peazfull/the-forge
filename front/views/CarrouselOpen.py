import io
import os
import re
import time
import zipfile
from datetime import datetime

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from services.utils.email_service import send_email_with_attachments
from services.marketbrewery.market_opens_service import get_open_top_flop
from services.marketbrewery.listes_market import EU_TOP_200


ASSETS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "layout", "assets", "carousel", "open"
)
FONT_BOLD_PATH = os.path.join(ASSETS_DIR, "Manrope-Bold.ttf")
FONT_SEMI_BOLD_PATH = os.path.join(ASSETS_DIR, "Manrope-SemiBold.ttf")
DATE_FONT_SIZE = 46
DATE_TOP = 850
DATE_FILL = "#F6F6F6"
DATE_HIGHLIGHT_BG = "#5B2EFF"
DATE_HIGHLIGHT_PAD_X = 10
DATE_HIGHLIGHT_PAD_Y = 6
SLIDE2_MARGIN_X = 165
SLIDE2_HEADER_SIZE = 24
SLIDE2_ROW_SIZE = 26
SLIDE2_HEADER_GAP = 14
SLIDE2_LINE_HEIGHT_MULT = 2
SLIDE2_HEADER_COLOR = "#E6FF4B"
SLIDE2_TEXT_COLOR = "#F6F6F6"
SLIDE2_POS_COLOR = "#00BF63"
SLIDE2_NEG_COLOR = "#FF5757"
SLIDE2_START_Y = 400
SLIDE2_TITLE_TEXT = "Top 10 actions Européennes"
SLIDE2_TITLE_SIZE = 36
SLIDE2_TITLE_GAP = 30
SLIDE2_TITLE_COLOR = "#F6F6F6"
SLIDE2_TITLE_HIGHLIGHT_BG = "#5B2EFF"
SLIDE2_TITLE_PAD_X = 5
SLIDE2_TITLE_PAD_Y = 0
SLIDE2_TITLE_ASSET = os.path.join(ASSETS_DIR, "Top_10_eur.png")
SLIDE2_TITLE_ASSET_TOP = 275
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
        and re.search(r"(?:^|[_\s-])slide[_\s-]*\d+", name, re.IGNORECASE)
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


def _format_eur(value: float) -> str:
    try:
        return f"{value:,.2f}€".replace(",", " ")
    except Exception:
        return f"{value}€"


def _get_top10_open_eu() -> list[dict]:
    try:
        data = get_open_top_flop(EU_TOP_200, limit=10)
        if data.get("status") == "success":
            return data.get("top", []) or []
        return []
    except Exception:
        return []


def _get_flop10_open_eu() -> list[dict]:
    try:
        data = get_open_top_flop(EU_TOP_200, limit=10)
        if data.get("status") == "success":
            return data.get("flop", []) or []
        return []
    except Exception:
        return []


def _render_open_table(
    draw: ImageDraw.ImageDraw,
    img_w: int,
    img_h: int,
    rows: list[dict],
    title_text: str | None = None
) -> None:
    title_font = _load_font(FONT_BOLD_PATH, SLIDE2_TITLE_SIZE)
    header_font = _load_font(FONT_BOLD_PATH, SLIDE2_HEADER_SIZE)
    row_font = _load_font(FONT_SEMI_BOLD_PATH, SLIDE2_ROW_SIZE)
    title_height = int(SLIDE2_TITLE_SIZE * SLIDE2_LINE_HEIGHT_MULT)
    header_height = int(SLIDE2_HEADER_SIZE * SLIDE2_LINE_HEIGHT_MULT)
    row_height = int(SLIDE2_ROW_SIZE * SLIDE2_LINE_HEIGHT_MULT)

    total_rows = len(rows) if rows else 1

    block_height = header_height + SLIDE2_HEADER_GAP + (row_height * total_rows)
    start_y = SLIDE2_START_Y

    # Optional title (aligned with table)
    header_y = start_y
    if title_text:
        title_y = max(0, start_y - SLIDE2_TITLE_GAP - title_height)
        title_x = SLIDE2_MARGIN_X
        title_width = draw.textlength(title_text, font=title_font)
        rect = (
            title_x - SLIDE2_TITLE_PAD_X,
            title_y - SLIDE2_TITLE_PAD_Y,
            title_x + title_width + SLIDE2_TITLE_PAD_X,
            title_y + title_height + SLIDE2_TITLE_PAD_Y,
        )
        draw.rectangle(rect, fill=SLIDE2_TITLE_HIGHLIGHT_BG)
        draw.text((title_x, title_y), title_text, font=title_font, fill=SLIDE2_TITLE_COLOR)

    # Header row
    name_x = SLIDE2_MARGIN_X
    change_center_x = img_w // 2
    open_right_x = img_w - SLIDE2_MARGIN_X
    draw.text((name_x, header_y), "Entreprise", font=header_font, fill=SLIDE2_HEADER_COLOR)
    change_label = "Change"
    change_width = draw.textlength(change_label, font=header_font)
    draw.text((change_center_x - change_width / 2, header_y), change_label, font=header_font, fill=SLIDE2_HEADER_COLOR)
    open_label = "Prix d'Open"
    open_width = draw.textlength(open_label, font=header_font)
    draw.text((open_right_x - open_width, header_y), open_label, font=header_font, fill=SLIDE2_HEADER_COLOR)

    # Rows
    row_y = header_y + header_height + SLIDE2_HEADER_GAP
    if not rows:
        empty_text = "Données indisponibles"
        empty_width = draw.textlength(empty_text, font=row_font)
        draw.text(((img_w - empty_width) // 2, row_y), empty_text, font=row_font, fill=SLIDE2_TEXT_COLOR)
        return

    for row in rows:
        name = (row.get("name") or "").strip()
        pct = row.get("pct_change")
        open_value = row.get("open")
        try:
            pct_value = float(pct)
        except Exception:
            pct_value = 0.0
        pct_text = f"{pct_value:+.2f}%"
        pct_color = SLIDE2_POS_COLOR if pct_value >= 0 else SLIDE2_NEG_COLOR
        open_text = _format_eur(float(open_value)) if open_value is not None else "—"

        draw.text((name_x, row_y), name, font=row_font, fill=SLIDE2_TEXT_COLOR)
        pct_width = draw.textlength(pct_text, font=row_font)
        draw.text((change_center_x - pct_width / 2, row_y), pct_text, font=row_font, fill=pct_color)
        open_width = draw.textlength(open_text, font=row_font)
        draw.text((open_right_x - open_width, row_y), open_text, font=row_font, fill=SLIDE2_TEXT_COLOR)

        row_y += row_height


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
    elif slide_number == 2:
        draw = ImageDraw.Draw(img)
        if os.path.exists(SLIDE2_TITLE_ASSET):
            title_asset = Image.open(SLIDE2_TITLE_ASSET).convert("RGBA")
            img.alpha_composite(title_asset, (SLIDE2_MARGIN_X, SLIDE2_TITLE_ASSET_TOP))
        _render_open_table(
            draw,
            img.size[0],
            img.size[1],
            _get_top10_open_eu(),
            title_text=SLIDE2_TITLE_TEXT
        )
    elif slide_number == 3:
        draw = ImageDraw.Draw(img)
        _render_open_table(draw, img.size[0], img.size[1], _get_flop10_open_eu())
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


def refresh_open_slides() -> None:
    """Force un refresh des données et un rerun pour la preview/export."""
    st.cache_data.clear()
    st.session_state.open_refresh_token = str(time.time())


st.title("TheArtist - Open")
st.divider()

slide_files = _sorted_slide_files()
if not slide_files:
    st.warning("Aucune slide trouvée dans les assets (fichiers slide_*.png).")

if st.button("🖼️ Générer les slides", type="primary", use_container_width=True):
    refresh_open_slides()
    st.success("✅ Slides régénérées")
    st.rerun()

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
