import io
import os
import re
import time
import zipfile
from datetime import datetime

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from services.utils.email_service import send_email_with_attachments
from services.marketbrewery.market_close_service import get_close_top_flop, get_close_performances
from services.marketbrewery.listes_market import (
    EU_TOP_200,
    FR_SBF_120,
    EU_INDICES,
    COMMODITIES_MAJOR,
    EU_FX_PAIRS,
    CRYPTO_MAJOR,
)


ASSETS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "layout", "assets", "carousel", "close"
)
FONT_BOLD_PATH = os.path.join(ASSETS_DIR, "Manrope-Bold.ttf")
FONT_SEMI_BOLD_PATH = os.path.join(ASSETS_DIR, "Manrope-SemiBold.ttf")
DATE_FONT_SIZE = 58  # Augmenté ×1.2 (était 42)
DATE_TOP = 550  # Ajusté pour 1080x1350 (était 640)
DATE_FILL = "#F6F6F6"
DATE_HIGHLIGHT_BG = "#5B2EFF"
DATE_HIGHLIGHT_PAD_X = 10
DATE_HIGHLIGHT_PAD_Y = 6
SLIDE2_MARGIN_X = 140  # Réduit de 165 à 140 pour plus d'espace
SLIDE2_HEADER_SIZE = 29  # Augmenté ×1.2 (était 24)
SLIDE2_ROW_SIZE = 31  # Augmenté ×1.2 (était 26)
SLIDE2_HEADER_GAP = 14
SLIDE2_LINE_HEIGHT_MULT = 2
SLIDE2_HEADER_COLOR = "#E6FF4B"
SLIDE2_TEXT_COLOR = "#F6F6F6"
SLIDE2_POS_COLOR = "#00BF63"
SLIDE2_NEG_COLOR = "#FF5757"
SLIDE2_START_Y = 500  # Ajusté pour 1080x1350 (était 400)
SLIDE2_ROW_SEPARATOR_COLOR = (255, 255, 255, 200)
SLIDE2_ROW_SEPARATOR_INSET = 0
SLIDE2_TITLE_ASSET = os.path.join(ASSETS_DIR, "Top_10_eur.png")
SLIDE2_TITLE_ASSET_TOP = 388  # Ajusté pour 1080x1350 (était 310)
SLIDE3_TITLE_ASSET = os.path.join(ASSETS_DIR, "Flop_10_eur.png")
SLIDE3_TITLE_ASSET_TOP = 388  # Ajusté pour 1080x1350 (était 310)
SLIDE4_TITLE_ASSET = os.path.join(ASSETS_DIR, "Top_10_fr.png")
SLIDE4_TITLE_ASSET_TOP = 388  # Ajusté pour 1080x1350 (était 310)
SLIDE5_TITLE_ASSET = os.path.join(ASSETS_DIR, "Flop_10_fr.png")
SLIDE5_TITLE_ASSET_TOP = 388  # Ajusté pour 1080x1350 (était 310)
SLIDE6_TITLE_ASSET = os.path.join(ASSETS_DIR, "Indices_eur.png")
SLIDE6_TITLE_ASSET_TOP = 388  # Ajusté pour 1080x1350 (était 310)
SLIDE7_TITLE_ASSET = os.path.join(ASSETS_DIR, "Como_eur.png")
SLIDE7_TITLE_ASSET_TOP = 388  # Ajusté pour 1080x1350 (était 310)
SLIDE8_TITLE_ASSET = os.path.join(ASSETS_DIR, "Devises_eur.png")
SLIDE8_TITLE_ASSET_TOP = 388  # Ajusté pour 1080x1350 (était 310)
SLIDE9_TITLE_ASSET = os.path.join(ASSETS_DIR, "Cryptos_eur.png")
SLIDE9_TITLE_ASSET_TOP = 388  # Ajusté pour 1080x1350 (était 310)
CAPTION_FILE = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "prompts", "close", "fixed_caption.txt"
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
    result = [(name, os.path.join(ASSETS_DIR, name)) for name in files]
    
    # Ajouter Outro.png en dernière slide
    outro_path = os.path.join(ASSETS_DIR, "Outro.png")
    if os.path.exists(outro_path):
        result.append(("Outro.png", outro_path))
    
    return result


def _format_french_date(dt: datetime | None = None) -> str:
    if dt is None:
        dt = datetime.now()
    months = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]
    return f"Le Close Europe du {dt.day:02d} {months[dt.month - 1]} {dt.year}"


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


def _format_usd(value: float) -> str:
    try:
        return f"{value:,.2f} $".replace(",", " ")
    except Exception:
        return f"{value} $"


def _format_points(value: float) -> str:
    try:
        return f"{value:,.2f}".replace(",", " ")
    except Exception:
        return f"{value}"


def _get_top10_close_eu() -> list[dict]:
    try:
        data = get_close_top_flop(EU_TOP_200, limit=10)
        if data.get("status") == "success":
            return data.get("top", []) or []
        return []
    except Exception:
        return []


def _get_flop10_close_eu() -> list[dict]:
    try:
        data = get_close_top_flop(EU_TOP_200, limit=10)
        if data.get("status") == "success":
            return data.get("flop", []) or []
        return []
    except Exception:
        return []


def _get_top10_close_fr() -> list[dict]:
    try:
        data = get_close_top_flop(FR_SBF_120, limit=10)
        if data.get("status") == "success":
            return data.get("top", []) or []
        return []
    except Exception:
        return []


def _get_indices_close_eu() -> list[dict]:
    try:
        data = get_close_performances(EU_INDICES)
        if data.get("status") == "success":
            return data.get("items", []) or []
        return []
    except Exception:
        return []


def _get_commodities_close() -> list[dict]:
    try:
        data = get_close_performances(COMMODITIES_MAJOR)
        if data.get("status") == "success":
            return data.get("items", []) or []
        return []
    except Exception:
        return []


def _get_fx_close_eu() -> list[dict]:
    try:
        data = get_close_performances(EU_FX_PAIRS)
        if data.get("status") == "success":
            items = data.get("items", []) or []
            preferred = ["EURUSD=X", "EURGBP=X", "EURCHF=X"]
            preferred_order = {sym: idx for idx, sym in enumerate(preferred)}
            items.sort(
                key=lambda item: (
                    0 if item.get("symbol") in preferred_order else 1,
                    preferred_order.get(item.get("symbol"), 999),
                    item.get("symbol", "")
                )
            )
            return items
        return []
    except Exception:
        return []


def _get_crypto_close() -> list[dict]:
    try:
        data = get_close_performances(CRYPTO_MAJOR)
        if data.get("status") == "success":
            items = data.get("items", []) or []
            preferred = ["BTC-USD", "ETH-USD", "SOL-USD"]
            preferred_order = {sym: idx for idx, sym in enumerate(preferred)}
            items.sort(
                key=lambda item: (
                    0 if item.get("symbol") in preferred_order else 1,
                    preferred_order.get(item.get("symbol"), 999),
                    item.get("symbol", "")
                )
            )
            return items
        return []
    except Exception:
        return []


def _get_flop10_close_fr() -> list[dict]:
    try:
        data = get_close_top_flop(FR_SBF_120, limit=10)
        if data.get("status") == "success":
            return data.get("flop", []) or []
        return []
    except Exception:
        return []


def _render_close_table(
    draw: ImageDraw.ImageDraw,
    img_w: int,
    img_h: int,
    rows: list[dict],
    name_label: str = "Entreprise",
    close_label: str = "Close",
    format_close=None
) -> None:
    header_font = _load_font(FONT_BOLD_PATH, SLIDE2_HEADER_SIZE)
    row_font = _load_font(FONT_SEMI_BOLD_PATH, SLIDE2_ROW_SIZE)
    header_height = int(SLIDE2_HEADER_SIZE * SLIDE2_LINE_HEIGHT_MULT)
    row_height = int(SLIDE2_ROW_SIZE * SLIDE2_LINE_HEIGHT_MULT)

    total_rows = len(rows) if rows else 1

    block_height = header_height + SLIDE2_HEADER_GAP + (row_height * total_rows)
    start_y = SLIDE2_START_Y

    # Header row
    header_y = start_y
    name_x = SLIDE2_MARGIN_X
    change_center_x = img_w // 2
    close_right_x = img_w - SLIDE2_MARGIN_X
    draw.text((name_x, header_y), name_label, font=header_font, fill=SLIDE2_HEADER_COLOR)
    change_label = "Change"
    change_width = draw.textlength(change_label, font=header_font)
    draw.text((change_center_x - change_width / 2, header_y), change_label, font=header_font, fill=SLIDE2_HEADER_COLOR)
    close_width = draw.textlength(close_label, font=header_font)
    draw.text((close_right_x - close_width, header_y), close_label, font=header_font, fill=SLIDE2_HEADER_COLOR)

    # Rows
    row_y = header_y + header_height + SLIDE2_HEADER_GAP
    if not rows:
        empty_text = "Données indisponibles"
        empty_width = draw.textlength(empty_text, font=row_font)
        draw.text(((img_w - empty_width) // 2, row_y), empty_text, font=row_font, fill=SLIDE2_TEXT_COLOR)
        return

    for row in rows:
        name = (row.get("name") or row.get("symbol") or "").strip()
        pct = row.get("pct_change")
        close_value = row.get("close")
        try:
            pct_value = float(pct)
        except Exception:
            pct_value = 0.0
        pct_text = f"{pct_value:+.2f}%"
        pct_color = SLIDE2_POS_COLOR if pct_value >= 0 else SLIDE2_NEG_COLOR
        if close_value is not None:
            formatter = format_close or _format_eur
            close_text = formatter(float(close_value))
        else:
            close_text = "—"

        draw.text((name_x, row_y), name, font=row_font, fill=SLIDE2_TEXT_COLOR)
        pct_width = draw.textlength(pct_text, font=row_font)
        draw.text((change_center_x - pct_width / 2, row_y), pct_text, font=row_font, fill=pct_color)
        close_width = draw.textlength(close_text, font=row_font)
        draw.text((close_right_x - close_width, row_y), close_text, font=row_font, fill=SLIDE2_TEXT_COLOR)

        # Separator line between rows
        separator_y = row_y + row_height - int(row_height * 0.15)
        draw.line(
            (name_x + SLIDE2_ROW_SEPARATOR_INSET, separator_y,
            close_right_x - SLIDE2_ROW_SEPARATOR_INSET, separator_y),
            fill=SLIDE2_ROW_SEPARATOR_COLOR,
            width=1
        )

        row_y += row_height


def _render_slide_bytes(filename: str, path: str) -> bytes:
    img = Image.open(path).convert("RGBA")
    match = re.search(r"slide[_\s-]?(\d+)", filename, re.IGNORECASE)
    slide_number = int(match.group(1)) if match else None
    
    # Ajouter Swipe.png pour les slides 1-9
    swipe_path = os.path.join(ASSETS_DIR, "Swipe.png")
    should_add_swipe = slide_number is not None and 1 <= slide_number <= 9
    
    if slide_number == 1:
        draw = ImageDraw.Draw(img)
        date_text = _format_french_date()
        font = _load_font(FONT_BOLD_PATH, DATE_FONT_SIZE)
        text_width = draw.textlength(date_text, font=font)
        text_height = int(DATE_FONT_SIZE * 1.2)
        x = (img.size[0] - text_width) // 2
        draw.text((x, DATE_TOP), date_text, font=font, fill=DATE_FILL)
    elif slide_number == 2:
        draw = ImageDraw.Draw(img)
        if os.path.exists(SLIDE2_TITLE_ASSET):
            title_asset = Image.open(SLIDE2_TITLE_ASSET).convert("RGBA")
            img.alpha_composite(title_asset, (SLIDE2_MARGIN_X, SLIDE2_TITLE_ASSET_TOP))
        _render_close_table(draw, img.size[0], img.size[1], _get_top10_close_eu())
    elif slide_number == 3:
        draw = ImageDraw.Draw(img)
        if os.path.exists(SLIDE3_TITLE_ASSET):
            title_asset = Image.open(SLIDE3_TITLE_ASSET).convert("RGBA")
            img.alpha_composite(title_asset, (SLIDE2_MARGIN_X, SLIDE3_TITLE_ASSET_TOP))
        _render_close_table(draw, img.size[0], img.size[1], _get_flop10_close_eu())
    elif slide_number == 4:
        draw = ImageDraw.Draw(img)
        if os.path.exists(SLIDE4_TITLE_ASSET):
            title_asset = Image.open(SLIDE4_TITLE_ASSET).convert("RGBA")
            img.alpha_composite(title_asset, (SLIDE2_MARGIN_X, SLIDE4_TITLE_ASSET_TOP))
        _render_close_table(draw, img.size[0], img.size[1], _get_top10_close_fr())
    elif slide_number == 5:
        draw = ImageDraw.Draw(img)
        if os.path.exists(SLIDE5_TITLE_ASSET):
            title_asset = Image.open(SLIDE5_TITLE_ASSET).convert("RGBA")
            img.alpha_composite(title_asset, (SLIDE2_MARGIN_X, SLIDE5_TITLE_ASSET_TOP))
        _render_close_table(draw, img.size[0], img.size[1], _get_flop10_close_fr())
    elif slide_number == 6:
        draw = ImageDraw.Draw(img)
        if os.path.exists(SLIDE6_TITLE_ASSET):
            title_asset = Image.open(SLIDE6_TITLE_ASSET).convert("RGBA")
            img.alpha_composite(title_asset, (SLIDE2_MARGIN_X, SLIDE6_TITLE_ASSET_TOP))
        _render_close_table(
            draw,
            img.size[0],
            img.size[1],
            _get_indices_close_eu(),
            name_label="Indice",
            close_label="Close",
            format_close=_format_points
        )
    elif slide_number == 7:
        draw = ImageDraw.Draw(img)
        if os.path.exists(SLIDE7_TITLE_ASSET):
            title_asset = Image.open(SLIDE7_TITLE_ASSET).convert("RGBA")
            img.alpha_composite(title_asset, (SLIDE2_MARGIN_X, SLIDE7_TITLE_ASSET_TOP))
        _render_close_table(
            draw,
            img.size[0],
            img.size[1],
            _get_commodities_close(),
            name_label="Asset",
            close_label="Close",
            format_close=_format_usd
        )
    elif slide_number == 8:
        draw = ImageDraw.Draw(img)
        if os.path.exists(SLIDE8_TITLE_ASSET):
            title_asset = Image.open(SLIDE8_TITLE_ASSET).convert("RGBA")
            img.alpha_composite(title_asset, (SLIDE2_MARGIN_X, SLIDE8_TITLE_ASSET_TOP))
        _render_close_table(
            draw,
            img.size[0],
            img.size[1],
            _get_fx_close_eu(),
            name_label="Currency",
            close_label="Close",
            format_close=_format_usd
        )
    elif slide_number == 9:
        draw = ImageDraw.Draw(img)
        if os.path.exists(SLIDE9_TITLE_ASSET):
            title_asset = Image.open(SLIDE9_TITLE_ASSET).convert("RGBA")
            img.alpha_composite(title_asset, (SLIDE2_MARGIN_X, SLIDE9_TITLE_ASSET_TOP))
        _render_close_table(
            draw,
            img.size[0],
            img.size[1],
            _get_crypto_close(),
            name_label="Crypto",
            close_label="Close",
            format_close=_format_usd
        )
    
    # Ajouter Swipe.png en bas à droite pour les slides 1-9
    if should_add_swipe and os.path.exists(swipe_path):
        try:
            swipe = Image.open(swipe_path).convert("RGBA")
            swipe_x = img.width - swipe.width - 50  # 50px de marge droite
            swipe_y = img.height - swipe.height - 50  # 50px de marge bas
            img.alpha_composite(swipe, (swipe_x, swipe_y))
        except Exception:
            pass  # Si erreur, on continue sans le swipe
    
    output = io.BytesIO()
    img.convert("RGB").save(output, format="PNG")
    return output.getvalue()


def build_close_exports(slide_paths: list[tuple[str, str]]) -> dict[str, object]:
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


def refresh_close_slides() -> None:
    """Force un refresh des données et un rerun pour la preview/export."""
    st.cache_data.clear()
    st.session_state.close_refresh_token = str(time.time())


st.title("TheArtist - Close")
st.divider()

slide_files = _sorted_slide_files()
if not slide_files:
    st.warning("Aucune slide trouvée dans les assets (fichiers slide_*.png).")

if st.button("🖼️ Générer les slides", type="primary", use_container_width=True):
    refresh_close_slides()
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
            except Exception as e:
                st.error(f"Erreur rendu {filename}: {str(e)}")
                try:
                    st.image(path, use_container_width=True)
                except Exception as e2:
                    st.error(f"Erreur chargement {filename}: {str(e2)}")

st.divider()
if st.button("📦 Préparer export Close", use_container_width=True):
    export_data = build_close_exports(slide_files)
    st.session_state.close_export_zip = export_data["zip"]
    st.session_state.close_export_pdf = export_data["pdf"]
    st.session_state.close_export_count = export_data["count"]

if st.session_state.get("close_export_zip"):
    if st.session_state.get("close_export_count", 0) == 0:
        st.warning("Aucune slide disponible pour l'export.")
    else:
        st.caption(f"{st.session_state.get('close_export_count', 0)} slides prêtes")
        st.download_button(
            "⬇️ Télécharger PNG (ZIP)",
            data=st.session_state.close_export_zip,
            file_name="close_slides.zip",
            mime="application/zip",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Télécharger PDF",
            data=st.session_state.close_export_pdf,
            file_name="close_slides.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

st.markdown("#### Export Email")
if st.button("✉️ Envoyer par email", use_container_width=True):
    try:
        export_data = build_close_exports(slide_files)
        if export_data.get("count", 0) == 0:
            st.warning("Aucune slide disponible pour l'envoi.")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            subject = f"Close - {date_str}"
            caption_text = _load_fixed_caption() or "Caption non disponible."
            attachments = [
                ("close_slides.zip", export_data["zip"], "application/zip"),
                ("close_slides.pdf", export_data["pdf"], "application/pdf"),
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
        st.warning("Caption fixe manquante : utilise le fichier prompts/close/fixed_caption.txt")

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
