"""
Génération des slides carousel (1080x1350) via Pillow.
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

CANVAS_SIZE = (1080, 1350)
COVER_IMAGE_SIZE = (1080, 864)  # Format 5:4 pour l'image de fond de la slide 0
LOGO_SIZE = (200, 65)
LOGO_TOP = -15  # Négatif pour clipper le haut du logo
TITLE_BG_TOP_FROM_BOTTOM = 490  # px depuis le bas (590px du haut)
TITLE_BG_SIDE_MARGIN = 50
SWIPE_MARGIN = 20
SWIPE_SIZE = (56, 29)
COVER_SWIPE_SCALE = 0.5
LEFT_MARGIN = 60
RIGHT_MARGIN = 60
CONTENT_TOP_GAP = 20
CONTENT_BOTTOM_MARGIN = 20
DATE_FONT_SIZE = 38
COVER_LOGO_WIDTH = 760
DATE_TOP_GAP = 12

# Polices (fallback sur PIL par défaut si fichier absent)
FONT_TITLE_PATH = os.path.join(ASSETS_DIR, "Inter_18pt-Bold.ttf")
FONT_CONTENT_PATH = os.path.join(ASSETS_DIR, "Inter_18pt-Medium.ttf")
FONT_DATE_PATH = os.path.join(ASSETS_DIR, "Manrope-SemiBold.ttf")  # Date slide 0
TITLE_FONT_WEIGHT = 700  # Bold
CONTENT_FONT_WEIGHT = 500  # Medium
DATE_FONT_WEIGHT = 600  # SemiBold
TITLE_FONT_SIZE = 46
CONTENT_FONT_SIZE = 39


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
    Canvas 1080×1350 avec fond #F4F4EB, image 5:4 (1080×864) collée en bas.
    """
    if not image_url and not image_bytes:
        raise ValueError("Aucune image disponible pour la slide.")

    if image_bytes:
        base_img = _load_image_from_bytes(image_bytes)
    else:
        base_img = _load_image_from_url(image_url)  # type: ignore[arg-type]

    # Redimensionner l'image de fond en 1080×864 (5:4)
    base_img = _cover_resize(base_img, COVER_IMAGE_SIZE)
    
    # Créer le canvas complet 1080×1350 avec fond #F4F4EB (beige/crème)
    canvas = Image.new("RGBA", CANVAS_SIZE, (244, 244, 235, 255))  # #F4F4EB
    
    # Coller l'image de fond en BAS du canvas (bas de l'image aligné avec bas du canvas)
    # Canvas height: 1350, Image height: 864 → Y position: 1350 - 864 = 486
    image_y_position = CANVAS_SIZE[1] - COVER_IMAGE_SIZE[1]
    if base_img.mode != 'RGBA':
        base_img = base_img.convert('RGBA')
    canvas.alpha_composite(base_img, (0, image_y_position))

    # Overlay Slide0 - Force 1100x600 pour les slides 1-N
    # Les 10px de chaque côté seront clippés automatiquement par le canvas
    overlay_slide0_path = os.path.join(ASSETS_DIR, "Overlay_Slide0.png")
    overlay_width = 1100
    overlay_height = 600
    overlay_x = -10  # Centré avec clipping
    if os.path.exists(overlay_slide0_path):
        overlay_slide0 = Image.open(overlay_slide0_path).convert("RGBA")
        # Forcer à 1100x600 (pas de ratio, taille fixe)
        overlay_slide0 = overlay_slide0.resize((overlay_width, overlay_height), Image.LANCZOS)
        canvas.alpha_composite(overlay_slide0, (overlay_x, 0))

    draw = ImageDraw.Draw(canvas)

    # Logo
    logo_path = os.path.join(ASSETS_DIR, "Logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize(LOGO_SIZE, Image.LANCZOS)
        logo_x = (CANVAS_SIZE[0] - LOGO_SIZE[0]) // 2
        canvas.alpha_composite(logo, (logo_x, LOGO_TOP))

    # swipe_pea.png - En bas à droite de l'overlay : 50px du bas, 50px margin right
    swipe_pea_path = os.path.join(ASSETS_DIR, "swipe_pea.png")
    if os.path.exists(swipe_pea_path):
        swipe_pea = Image.open(swipe_pea_path).convert("RGBA")
        # Augmenter la taille x1.2
        new_width = int(swipe_pea.size[0] * 1.2)
        new_height = int(swipe_pea.size[1] * 1.2)
        swipe_pea = swipe_pea.resize((new_width, new_height), Image.LANCZOS)
        # Position: 50px du bas de l'overlay (overlay fait 600px de haut)
        swipe_pea_y = overlay_height - 50 - swipe_pea.size[1]
        # Position X: 50px du bord droit de l'overlay (overlay_x = -10, largeur = 1100)
        # Bord droit de l'overlay: -10 + 1100 = 1090
        swipe_pea_x = overlay_x + overlay_width - 50 - swipe_pea.size[0]
        canvas.alpha_composite(swipe_pea, (swipe_pea_x, swipe_pea_y))

    # Title background - positionné à 92px du top (87 + 5px)
    title_bg_path = os.path.join(ASSETS_DIR, "Title_bg_pea.png")
    title_bg_top = 92
    if os.path.exists(title_bg_path):
        title_bg = Image.open(title_bg_path).convert("RGBA")
        title_bg_width = CANVAS_SIZE[0] - (TITLE_BG_SIDE_MARGIN * 2)
        title_bg = title_bg.resize((title_bg_width, title_bg.size[1]), Image.LANCZOS)
        canvas.alpha_composite(title_bg, (TITLE_BG_SIDE_MARGIN, title_bg_top))
        title_bg_height = title_bg.size[1]
    else:
        title_bg_height = 0

    # Title text - Inter Bold 48, blanc, letter spacing -1%
    title_max_width = CANVAS_SIZE[0] - LEFT_MARGIN - RIGHT_MARGIN
    title_font, title_lines = _fit_text(
        draw, title, title_max_width, 80, start_size=TITLE_FONT_SIZE, font_path=FONT_TITLE_PATH, weight=TITLE_FONT_WEIGHT
    )
    title_block_height = int(title_font.size * 1.2) * len(title_lines[:2])
    title_y = title_bg_top + max(0, (title_bg_height - title_block_height) // 2)
    title_letter_spacing = int(title_font.size * -0.01)  # -1%
    for line in title_lines[:2]:
        draw.text((LEFT_MARGIN, title_y), line, font=title_font, fill="white", spacing=title_letter_spacing)
        title_y += int(title_font.size * 1.2)

    # Content text - Inter Medium 40, noir, letter spacing +1%
    content_top = title_bg_top + title_bg_height + CONTENT_TOP_GAP
    content_max_height = CANVAS_SIZE[1] - content_top - CONTENT_BOTTOM_MARGIN
    content = _sentence_case(content)
    content_font, content_lines = _fit_text(
        draw, content, title_max_width, content_max_height, start_size=CONTENT_FONT_SIZE, font_path=FONT_CONTENT_PATH, weight=CONTENT_FONT_WEIGHT
    )
    line_height = int(content_font.size * 1.25)
    content_letter_spacing = int(content_font.size * 0.01)  # +1%
    y = content_top
    for line in content_lines:
        if y + line_height > CANVAS_SIZE[1] - CONTENT_BOTTOM_MARGIN:
            break
        draw.text((LEFT_MARGIN, y), line, font=content_font, fill="black", spacing=content_letter_spacing)
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
    """Format date en FR avec première lettre majuscule (ex: Du lundi 10 février 2026)."""
    if dt is None:
        dt = datetime.now()
    days = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    months = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"
    ]
    day = days[dt.weekday()]
    month = months[dt.month - 1]
    date_string = f"du {day} {dt.day} {month} {dt.year}"
    # Première lettre en majuscule
    return date_string[0].upper() + date_string[1:]


def generate_cover_slide(
    image_url: Optional[str] = None,
    image_bytes: Optional[bytes] = None
) -> bytes:
    """
    Génère la slide de couverture (position 0).
    Image de fond en 5:4 (1080×864), canvas total 1080×1350.
    """
    if not image_url and not image_bytes:
        raise ValueError("Aucune image disponible pour la cover.")
    
    if image_bytes:
        base_img = _load_image_from_bytes(image_bytes)
    else:
        base_img = _load_image_from_url(image_url)  # type: ignore[arg-type]
    
    # Redimensionner l'image de fond en 1080×864 (5:4)
    base_img = _cover_resize(base_img, COVER_IMAGE_SIZE)
    
    # Créer le canvas complet 1080×1350 avec fond #F4F4EB (beige/crème)
    canvas = Image.new("RGBA", CANVAS_SIZE, (244, 244, 235, 255))  # #F4F4EB
    
    # 1. Coller l'image de fond en BAS du canvas (bas de l'image aligné avec bas du canvas)
    # Canvas height: 1350, Image height: 864 → Y position: 1350 - 864 = 486
    image_y_position = CANVAS_SIZE[1] - COVER_IMAGE_SIZE[1]
    # Convertir en RGBA pour alpha_composite
    if base_img.mode != 'RGBA':
        base_img = base_img.convert('RGBA')
    canvas.alpha_composite(base_img, (0, image_y_position))
    
    # 2. Overlay Slide0 - Force 1100px de large pour couvrir les strokes/patterns
    # Les 10px de chaque côté seront clippés automatiquement par le canvas
    overlay_slide0_path = os.path.join(ASSETS_DIR, "Overlay_Slide0.png")
    if os.path.exists(overlay_slide0_path):
        overlay_slide0 = Image.open(overlay_slide0_path).convert("RGBA")
        # Forcer le redimensionnement à 1100px de large (20px de plus que le canvas)
        original_width, original_height = overlay_slide0.size
        target_width = 1100  # 20px de plus pour gérer les strokes/patterns
        scale = target_width / original_width
        target_height = int(original_height * scale)
        overlay_slide0 = overlay_slide0.resize((target_width, target_height), Image.LANCZOS)
        # Centrer : (1080 - 1100) / 2 = -10px (déborde de 10px de chaque côté)
        x_offset = (CANVAS_SIZE[0] - target_width) // 2
        canvas.alpha_composite(overlay_slide0, (x_offset, 0))
    
    # 3. Top bar collée en haut, AU-DESSUS de l'overlay (0 margin)
    top_bar_path = os.path.join(ASSETS_DIR, "top_bar.png")
    if os.path.exists(top_bar_path):
        top_bar = Image.open(top_bar_path).convert("RGBA")
        # Redimensionner pour correspondre à la largeur du canvas si nécessaire
        if top_bar.size[0] != CANVAS_SIZE[0]:
            scale = CANVAS_SIZE[0] / top_bar.size[0]
            top_bar = top_bar.resize(
                (int(top_bar.size[0] * scale), int(top_bar.size[1] * scale)),
                Image.LANCZOS
            )
        canvas.alpha_composite(top_bar, (0, 0))
    
    draw = ImageDraw.Draw(canvas)
    
    # Logo principal (haut) - cover (scale x2) - collé en haut au centre (0px)
    logo_path = os.path.join(ASSETS_DIR, "Logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_size = (LOGO_SIZE[0] * 2, LOGO_SIZE[1] * 2)  # 400×130
        logo = logo.resize(logo_size, Image.LANCZOS)
        logo_x = (CANVAS_SIZE[0] - logo_size[0]) // 2
        canvas.alpha_composite(logo, (logo_x, 0))  # 0px du haut
    
    # Logo slide 0 - "Le roll PEA" (168px top, 45px left)
    cover_logo_path = os.path.join(ASSETS_DIR, "Logo_slide0.png")
    cover_logo_height = 0
    if os.path.exists(cover_logo_path):
        cover_logo = Image.open(cover_logo_path).convert("RGBA")
        cover_logo_height = cover_logo.size[1]
        # Pas de scale, utiliser la taille originale de l'asset
        canvas.alpha_composite(cover_logo, (45, 168))
    
    # Date - 51px sous le logo, 50px left, taille 68, letter spacing -1%
    date_str = _format_french_date()
    date_font_size = 68
    date_font = _load_font(FONT_DATE_PATH, date_font_size, weight=DATE_FONT_WEIGHT)
    
    # Position : 168px (logo top) + hauteur du logo + 51px
    date_y = 168 + cover_logo_height + 51
    date_x = 50
    
    # Letter spacing -1% (approximé à -0.6px pour font 60)
    letter_spacing = int(date_font_size * -0.01)
    draw.text((date_x, date_y), date_str, font=date_font, fill="#363636", spacing=letter_spacing)
    
    # Calcul hauteur de la date pour positionnement du Swipe
    date_height = int(date_font_size * 1.2)
    
    # Swipe (cover) - 84px de large, centré avec la date + 5px vers le bas, à droite avec 50px margin
    swipe_path = os.path.join(ASSETS_DIR, "Swipe.png")
    if os.path.exists(swipe_path):
        swipe = Image.open(swipe_path).convert("RGBA")
        # Forcer largeur à 84px, hauteur proportionnelle
        original_width, original_height = swipe.size
        target_width = 84
        scale = target_width / original_width
        target_height = int(original_height * scale)
        swipe = swipe.resize((target_width, target_height), Image.LANCZOS)
        # Position X : à droite avec 50px de margin
        swipe_x = CANVAS_SIZE[0] - swipe.size[0] - 50
        # Position Y : centré avec la date + 5px vers le bas
        swipe_y = date_y + (date_height - swipe.size[1]) // 2 + 5
        canvas.alpha_composite(swipe, (swipe_x, swipe_y))
    
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
