"""
Génération des slides carousel (1080x1080) via Pillow.
Stack: image de fond + filtre + logo + title_bg + texte + swipe.
"""

from __future__ import annotations

from io import BytesIO
from typing import Optional, Tuple, Set
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import requests
import os
from db.supabase_client import get_supabase


ASSETS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..",
    "front", "layout", "assets", "carousel", "pea"
)

SLIDES_BUCKET = "carousel-pea-slides"

CANVAS_SIZE = (1080, 1080)
LOGO_SIZE = (200, 65)
LOGO_TOP = 15
TITLE_BG_TOP_FROM_BOTTOM = 490  # px depuis le bas (590px du haut)
TITLE_BG_SIDE_MARGIN = 50
SWIPE_MARGIN = 20
SWIPE_SIZE = (56, 29)
COVER_SWIPE_SCALE = 0.49
LEFT_MARGIN = 60
RIGHT_MARGIN = 60
CONTENT_TOP_GAP = 20
CONTENT_BOTTOM_MARGIN = 20
DATE_FONT_SIZE = 49
COVER_LOGO_WIDTH = 760
DATE_TOP_GAP = 12

# Polices (fallback sur PIL par défaut si fichier absent)
FONT_TITLE_PATH = os.path.join(ASSETS_DIR, "Manrope-Bold.ttf")
FONT_CONTENT_PATH = os.path.join(ASSETS_DIR, "Manrope-SemiBold.ttf")
TITLE_FONT_WEIGHT = 600
CONTENT_FONT_WEIGHT = 600
TITLE_FONT_SIZE = 40
CONTENT_FONT_SIZE = 38


def _load_font(path: str, size: int, weight: int | None = None) -> ImageFont.ImageFont:
    if os.path.exists(path):
        try:
            # Variable font support if available
            axis = {"wght": weight} if weight else None
            return ImageFont.truetype(path, size=size, layout_engine=ImageFont.Layout.RAQM, axis=axis)
        except Exception:
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _load_image_from_url(image_url: str) -> Image.Image:
    response = requests.get(image_url, timeout=20)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGBA")


def _load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    return Image.open(BytesIO(image_bytes)).convert("RGBA")


def _cover_resize(img: Image.Image, target: Tuple[int, int]) -> Image.Image:
    target_w, target_h = target
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _wrap_text(text: str, draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = []
    for word in words:
        candidate = " ".join(current + [word])
        if draw.textlength(candidate, font=font) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_height: int,
    start_size: int,
    font_path: str,
    weight: int | None = None
) -> Tuple[ImageFont.ImageFont, list[str]]:
    size = start_size
    while size > 12:
        font = _load_font(font_path, size, weight=weight)
        lines = _wrap_text(text, draw, font, max_width)
        line_height = int(size * 1.2)
        total_height = line_height * len(lines)
        if total_height <= max_height:
            return font, lines
        size -= 2
    font = _load_font(font_path, 12, weight=weight)
    return font, _wrap_text(text, draw, font, max_width)


def _sentence_case(text: str) -> str:
    """Met une majuscule au début de chaque phrase."""
    parts = []
    for part in text.strip().split(". "):
        part = part.strip()
        if not part:
            continue
        part = part[0].upper() + part[1:]
        parts.append(part)
    return ". ".join(parts)


def generate_carousel_slide(
    title: str,
    content: str,
    image_url: Optional[str] = None,
    image_bytes: Optional[bytes] = None
) -> bytes:
    """
    Retourne un PNG (bytes) de la slide finale.
    """
    if not image_url and not image_bytes:
        raise ValueError("Aucune image disponible pour la slide.")

    if image_bytes:
        base_img = _load_image_from_bytes(image_bytes)
    else:
        base_img = _load_image_from_url(image_url)  # type: ignore[arg-type]

    base_img = _cover_resize(base_img, CANVAS_SIZE)
    canvas = base_img.copy()

    # Overlay filtre principal
    filter_path = os.path.join(ASSETS_DIR, "filter_main.png")
    if os.path.exists(filter_path):
        overlay = Image.open(filter_path).convert("RGBA")
        canvas.alpha_composite(overlay)

    draw = ImageDraw.Draw(canvas)

    # Logo
    logo_path = os.path.join(ASSETS_DIR, "Logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize(LOGO_SIZE, Image.LANCZOS)
        logo_x = (CANVAS_SIZE[0] - LOGO_SIZE[0]) // 2
        canvas.alpha_composite(logo, (logo_x, LOGO_TOP))

    # Title background
    title_bg_path = os.path.join(ASSETS_DIR, "Title_bg_pea.png")
    title_bg_top = CANVAS_SIZE[1] - TITLE_BG_TOP_FROM_BOTTOM
    if os.path.exists(title_bg_path):
        title_bg = Image.open(title_bg_path).convert("RGBA")
        title_bg_width = CANVAS_SIZE[0] - (TITLE_BG_SIDE_MARGIN * 2)
        title_bg = title_bg.resize((title_bg_width, title_bg.size[1]), Image.LANCZOS)
        canvas.alpha_composite(title_bg, (TITLE_BG_SIDE_MARGIN, title_bg_top))
        title_bg_height = title_bg.size[1]
    else:
        title_bg_height = 0

    # Title text
    title_max_width = CANVAS_SIZE[0] - LEFT_MARGIN - RIGHT_MARGIN
    title_font, title_lines = _fit_text(
        draw, title, title_max_width, 80, start_size=TITLE_FONT_SIZE, font_path=FONT_TITLE_PATH, weight=TITLE_FONT_WEIGHT
    )
    title_block_height = int(title_font.size * 1.2) * len(title_lines[:2])
    title_y = title_bg_top + max(0, (title_bg_height - title_block_height) // 2) - 5
    for line in title_lines[:2]:
        draw.text((LEFT_MARGIN, title_y), line, font=title_font, fill="white")
        title_y += int(title_font.size * 1.2)

    # Content text
    content_top = title_bg_top + title_bg_height + CONTENT_TOP_GAP
    content_max_height = CANVAS_SIZE[1] - content_top - CONTENT_BOTTOM_MARGIN
    content = _sentence_case(content)
    content_font, content_lines = _fit_text(
        draw, content, title_max_width, content_max_height, start_size=CONTENT_FONT_SIZE, font_path=FONT_CONTENT_PATH, weight=CONTENT_FONT_WEIGHT
    )
    line_height = int(content_font.size * 1.25)
    y = content_top
    for line in content_lines:
        if y + line_height > CANVAS_SIZE[1] - CONTENT_BOTTOM_MARGIN:
            break
        draw.text((LEFT_MARGIN, y), line, font=content_font, fill="white")
        y += line_height

    # Swipe
    swipe_path = os.path.join(ASSETS_DIR, "Swipe.png")
    if os.path.exists(swipe_path):
        swipe = Image.open(swipe_path).convert("RGBA")
        swipe = swipe.resize(SWIPE_SIZE, Image.LANCZOS)
        x = CANVAS_SIZE[0] - swipe.size[0] - SWIPE_MARGIN
        y = CANVAS_SIZE[1] - swipe.size[1] - SWIPE_MARGIN
        canvas.alpha_composite(swipe, (x, y))

    # Export
    output = BytesIO()
    canvas.convert("RGB").save(output, format="PNG")
    return output.getvalue()


def _format_french_date(dt: Optional[datetime] = None) -> str:
    """Format date en FR majuscules (ex: DU LUNDI 10 FEVRIER 2026)."""
    if dt is None:
        dt = datetime.now()
    days = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI", "DIMANCHE"]
    months = [
        "JANVIER", "FEVRIER", "MARS", "AVRIL", "MAI", "JUIN",
        "JUILLET", "AOUT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DECEMBRE"
    ]
    day = days[dt.weekday()]
    month = months[dt.month - 1]
    return f"DU {day} {dt.day} {month} {dt.year}"


def generate_cover_slide(
    image_url: Optional[str] = None,
    image_bytes: Optional[bytes] = None
) -> bytes:
    """
    Génère la slide de couverture (position 0).
    """
    if not image_url and not image_bytes:
        raise ValueError("Aucune image disponible pour la cover.")
    
    if image_bytes:
        base_img = _load_image_from_bytes(image_bytes)
    else:
        base_img = _load_image_from_url(image_url)  # type: ignore[arg-type]
    
    base_img = _cover_resize(base_img, CANVAS_SIZE)
    canvas = base_img.copy()
    
    # Overlay filtre principal
    filter_path = os.path.join(ASSETS_DIR, "filter_main.png")
    if os.path.exists(filter_path):
        overlay = Image.open(filter_path).convert("RGBA")
        canvas.alpha_composite(overlay)
    
    draw = ImageDraw.Draw(canvas)
    
    # Logo principal (haut) - cover (scale x2)
    logo_path = os.path.join(ASSETS_DIR, "Logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_size = (LOGO_SIZE[0] * 2, LOGO_SIZE[1] * 2)
        logo = logo.resize(logo_size, Image.LANCZOS)
        logo_x = (CANVAS_SIZE[0] - logo_size[0]) // 2
        canvas.alpha_composite(logo, (logo_x, LOGO_TOP))
    
    # Logo slide 0 (plein centre)
    cover_logo_path = os.path.join(ASSETS_DIR, "Logo_slide_0_pea.png")
    if os.path.exists(cover_logo_path):
        cover_logo = Image.open(cover_logo_path).convert("RGBA")
        scale = (COVER_LOGO_WIDTH / cover_logo.size[0]) * 1.3
        cover_logo = cover_logo.resize(
            (int(cover_logo.size[0] * scale), int(cover_logo.size[1] * scale)),
            Image.LANCZOS
        )
        cover_logo_height = cover_logo.size[1]
    else:
        cover_logo_height = 0
    
    # Date
    date_str = _format_french_date()
    date_font = _load_font(FONT_CONTENT_PATH, DATE_FONT_SIZE, weight=CONTENT_FONT_WEIGHT)
    date_w = draw.textlength(date_str, font=date_font)
    date_h = int(DATE_FONT_SIZE * 1.2)
    
    # Date positionnée à 680px du haut
    date_y = 680
    
    # Logo positionné AU-DESSUS de la date avec un gap de 12px
    if cover_logo_height:
        logo_y = date_y - DATE_TOP_GAP - cover_logo_height
        cover_x = (CANVAS_SIZE[0] - cover_logo.size[0]) // 2
        canvas.alpha_composite(cover_logo, (cover_x, logo_y))
    
    # Date
    date_x = (CANVAS_SIZE[0] - int(date_w)) // 2
    draw.text((date_x, date_y), date_str, font=date_font, fill="white")
    
    # Swipe (cover)
    swipe_path = os.path.join(ASSETS_DIR, "Swipe.png")
    if os.path.exists(swipe_path):
        swipe = Image.open(swipe_path).convert("RGBA")
        swipe = swipe.resize(
            (int(swipe.size[0] * COVER_SWIPE_SCALE), int(swipe.size[1] * COVER_SWIPE_SCALE)),
            Image.LANCZOS
        )
        x = CANVAS_SIZE[0] - swipe.size[0] - SWIPE_MARGIN
        y = CANVAS_SIZE[1] - swipe.size[1] - SWIPE_MARGIN
        canvas.alpha_composite(swipe, (x, y))
    
    output = BytesIO()
    canvas.convert("RGB").save(output, format="PNG")
    return output.getvalue()


def upload_slide_bytes(filename: str, image_bytes: bytes) -> Optional[str]:
    """Upload un slide dans le bucket carousel-pea-slides avec upsert."""
    try:
        supabase = get_supabase()
        supabase.storage.from_(SLIDES_BUCKET).upload(
            filename,
            image_bytes,
            file_options={"content-type": "image/png", "upsert": True}
        )
        return get_slide_public_url(filename)
    except Exception:
        return None


def get_slide_public_url(filename: str) -> str:
    """Retourne l'URL publique avec un cache buster pour forcer le refresh."""
    import time
    supabase = get_supabase()
    base_url = supabase.storage.from_(SLIDES_BUCKET).get_public_url(filename)
    # Ajouter un timestamp pour éviter le cache navigateur
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}t={int(time.time())}"


def list_slide_files() -> Set[str]:
    """Liste les fichiers présents dans le bucket carousel-pea-slides."""
    try:
        supabase = get_supabase()
        items = supabase.storage.from_(SLIDES_BUCKET).list()
        return {item.get("name") for item in items if item.get("name")}
    except Exception:
        return set()


def clear_slide_files() -> bool:
    """Supprime tous les fichiers du bucket carousel-pea-slides."""
    try:
        supabase = get_supabase()
        files = list_slide_files()
        if not files:
            return True
        supabase.storage.from_(SLIDES_BUCKET).remove(list(files))
        return True
    except Exception:
        return False
