"""
Génération des slides Doss (1080x1350) via Pillow.
Stack: image + filter + doss_bg_bas + texte.
"""

from __future__ import annotations

from io import BytesIO
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import requests
import os


ASSETS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..",
    "front", "layout", "assets", "carousel", "doss",
)

CANVAS_SIZE = (1080, 1350)  # Changé de 1080 à 1350
COVER_IMAGE_SIZE = (1080, 864)  # Format 5:4 pour cover et slides
IMAGE_TOP_HEIGHT = 540  # 16:9 sur moitié haute (pour legacy)
IMAGE_TOP_SIZE = (CANVAS_SIZE[0], IMAGE_TOP_HEIGHT)

LOGO_SIZE = (200, 65)
LOGO_TOP = 15
TITLE_ZOOM_SIZE = (346, 114)
TITLE_ZOOM_LEFT = 53
TITLE_ZOOM_TOP = 420

LEFT_MARGIN = 60
RIGHT_MARGIN = 60
TITLE_TOP_GAP = 0
CONTENT_TOP_GAP = 50
CONTENT_BOTTOM_MARGIN = 60
BOTTOM_BG_HEIGHT = 1043
BOTTOM_BG_MARGIN_BOTTOM = 20
BOTTOM_BG_MARGIN_LEFT = 0
OVERLAY_WIDTH = 1064
OVERLAY_HEIGHT = 1047
SWIPE_SIZE = (56, 29)
SWIPE_MARGIN_RIGHT = 30
SWIPE_MARGIN_BOTTOM = 30

TITLE_FONT_SIZE = 42
CONTENT_FONT_SIZE = 38
TITLE_FONT_WEIGHT = 600
CONTENT_FONT_WEIGHT = 600

TITLE_COLOR = "#F6F6F6"
CONTENT_COLOR = "#F6F6F6"
HIGHLIGHT_BG_COLOR = "#5B2EFF"
HIGHLIGHT_TEXT_COLOR = "#F6F6F6"
HIGHLIGHT_PAD_X = 6
TITLE_HIGHLIGHT_PAD_Y = 0
CONTENT_HIGHLIGHT_PAD_Y = -4   
PARAGRAPH_EXTRA_LINE_GAP = 1

FONT_TITLE_PATH = os.path.join(ASSETS_DIR, "Manrope-Bold.ttf")
FONT_CONTENT_PATH = os.path.join(ASSETS_DIR, "Manrope-SemiBold.ttf")

# Polices pour la cover (slide 0) - comme Eco
FONT_HOOK_PATH = os.path.join(ASSETS_DIR, "Manrope-SemiBold.ttf")  # Hook lignes 2-3
FONT_HOOK_LINE1_PATH = os.path.join(ASSETS_DIR, "Inter_18pt-Bold.ttf")  # Hook ligne 1
HOOK_FONT_SIZE = 68
HOOK_FONT_WEIGHT = 600  # SemiBold
HOOK_LINE1_FONT_SIZE = 88  # Ligne 1 (sujet principal)
HOOK_LINE23_FONT_SIZE = 52  # Lignes 2-3 - Changé de 58 à 52
HOOK_LINE1_LETTER_SPACING = -0.09  # -9%
HOOK_LINE23_LETTER_SPACING = -0.01  # -1%


def _load_font(path: str, size: int, weight: int | None = None) -> ImageFont.ImageFont:
    if os.path.exists(path):
        try:
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


def _cover_resize_anchor(img: Image.Image, target: Tuple[int, int], anchor: str = "center") -> Image.Image:
    target_w, target_h = target
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    if anchor == "bottom":
        left = (new_w - target_w) // 2
        top = max(0, new_h - target_h)
    elif anchor == "top":
        left = (new_w - target_w) // 2
        top = 0
    else:
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
) -> tuple[ImageFont.ImageFont, list[str]]:
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


def _strip_highlight_markers(text: str) -> str:
    return text.replace("**", "")


def _tokenize_highlights(text: str) -> list[tuple[str, bool]]:
    tokens: list[tuple[str, bool]] = []
    if not text:
        return tokens
    parts = text.split("**")
    for idx, part in enumerate(parts):
        if not part:
            continue
        is_highlight = (idx % 2 == 1)
        words = part.split()
        for w in words:
            tokens.append((w, is_highlight))
    return tokens


def _wrap_highlight_tokens(
    tokens: list[tuple[str, bool]],
    draw: ImageDraw.ImageDraw,
    font: ImageFont.ImageFont,
    max_width: int
) -> list[list[tuple[str, bool]]]:
    lines: list[list[tuple[str, bool]]] = []
    current: list[tuple[str, bool]] = []
    current_width = 0.0
    for i, (word, is_highlight) in enumerate(tokens):
        token_text = word + " "
        token_width = draw.textlength(token_text, font=font)
        if current and current_width + token_width > max_width:
            lines.append(current)
            current = []
            current_width = 0.0
        current.append((word, is_highlight))
        current_width += token_width
    if current:
        lines.append(current)
    return lines


def generate_doss_slide(
    title: str,
    content: str,
    image_url: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    position: int | None = None
) -> bytes:
    """
    Génère une slide Doss (1-4) avec le style Eco :
    - Canvas 1080x1350, fond #F4F4EB
    - Image 5:4 en bas
    - Overlay au-dessus de l'image
    - Titre et contenu en haut (NOIR)
    """
    if not image_url and not image_bytes:
        raise ValueError("Aucune image disponible pour le doss.")

    if image_bytes:
        base_img = _load_image_from_bytes(image_bytes)
    else:
        base_img = _load_image_from_url(image_url)  # type: ignore[arg-type]

    # Redimensionner l'image en 5:4 (1080x864)
    base_img = _cover_resize(base_img, COVER_IMAGE_SIZE)
    
    # Canvas 1080x1350 avec fond #F4F4EB
    canvas = Image.new("RGBA", CANVAS_SIZE, (244, 244, 235, 255))
    
    # 1. Coller l'image en bas (Y = 1350 - 864 = 486)
    image_y_position = CANVAS_SIZE[1] - COVER_IMAGE_SIZE[1]
    if base_img.mode != 'RGBA':
        base_img = base_img.convert('RGBA')
    canvas.alpha_composite(base_img, (0, image_y_position))
    
    # 2. Overlay au-dessus de l'image (1100x600, clippé sur les côtés comme Eco)
    overlay_path = os.path.join(ASSETS_DIR, "Overlay_Slide0.png")
    overlay_y = image_y_position  # Au même niveau que l'image
    if os.path.exists(overlay_path):
        overlay = Image.open(overlay_path).convert("RGBA")
        # Redimensionner à 1100x600 (comme Eco)
        overlay = overlay.resize((1100, 600), Image.LANCZOS)
        # Position : X=-10 pour clipper 10px de chaque côté (comme Eco)
        overlay_x = -10
        canvas.alpha_composite(overlay, (overlay_x, overlay_y))
    
    # 3. Logo en haut (200x65, centré, -15px du top pour clip)
    logo_path = os.path.join(ASSETS_DIR, "Logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize(LOGO_SIZE, Image.LANCZOS)
        logo_x = (CANVAS_SIZE[0] - LOGO_SIZE[0]) // 2
        canvas.alpha_composite(logo, (logo_x, LOGO_TOP))
    
    # 4. Title_bg_doss.png à 87px du top
    title_bg_path = os.path.join(ASSETS_DIR, "Title_bg_doss.png")
    title_bg_top = 87
    title_bg_height = 0
    if os.path.exists(title_bg_path):
        title_bg = Image.open(title_bg_path).convert("RGBA")
        title_bg_height = title_bg.size[1]
        canvas.alpha_composite(title_bg, (0, title_bg_top))
    
    # 5. Swipe (1.2x, 50px du bas de l'overlay, 50px right)
    swipe_path = os.path.join(ASSETS_DIR, "swipe_doss.png")
    if os.path.exists(swipe_path):
        swipe = Image.open(swipe_path).convert("RGBA")
        # Scale x1.2
        new_width = int(swipe.size[0] * 1.2)
        new_height = int(swipe.size[1] * 1.2)
        swipe = swipe.resize((new_width, new_height), Image.LANCZOS)
        # Position : 50px du bas de l'overlay (overlay_y + 600 - 50 - swipe height)
        swipe_x = CANVAS_SIZE[0] - new_width - 50
        swipe_y = overlay_y + 600 - 50 - new_height
        canvas.alpha_composite(swipe, (swipe_x, swipe_y))
    
    draw = ImageDraw.Draw(canvas)
    
    # 6. TITRE
    # Slide 1 : title_bg_slide_1.png + Titre textuel en BLANC
    # Slide 2 : Asset title_slide_1.png
    # Slide 3 : Asset title_slide_2.png
    # Slide 4 : Asset title_slide_3.png
    
    if position == 1:
        # SLIDE 1 : title_bg_slide_1.png + Titre textuel en BLANC
        
        # D'abord, charger title_bg_slide_1.png
        title_bg_slide1_path = os.path.join(ASSETS_DIR, "title_bg_slide_1.png")
        if os.path.exists(title_bg_slide1_path):
            title_bg_slide1 = Image.open(title_bg_slide1_path).convert("RGBA")
            # Centrer horizontalement, positionner à 87px du top
            title_bg_slide1_x = (CANVAS_SIZE[0] - title_bg_slide1.size[0]) // 2
            canvas.alpha_composite(title_bg_slide1, (title_bg_slide1_x, title_bg_top))
        
        # Ensuite, afficher le titre en BLANC par-dessus
        title_font = _load_font(os.path.join(ASSETS_DIR, "Inter_18pt-Bold.ttf"), 46, weight=700)
        title_letter_spacing = int(46 * -0.01)
        
        # Wrap le titre
        title_max_width = CANVAS_SIZE[0] - (LEFT_MARGIN * 2)
        title_lines = _wrap_text(title, draw, title_font, title_max_width)
        title_line_height = int(46 * 1.2)
        
        # Position titre : centré verticalement dans title_bg
        title_block_height = title_line_height * len(title_lines[:2])
        title_y = title_bg_top + max(0, (title_bg_height - title_block_height) // 2)
        
        for line in title_lines[:2]:
            draw.text((LEFT_MARGIN, title_y), line, font=title_font, fill="white", spacing=title_letter_spacing)
            title_y += title_line_height
    
    elif position in [2, 3, 4]:
        # SLIDES 2, 3, 4 : Asset fixe
        title_asset_map = {
            2: "title_slide_1.png",
            3: "title_slide_2.png",
            4: "title_slide_3.png"
        }
        title_asset_path = os.path.join(ASSETS_DIR, title_asset_map[position])
        if os.path.exists(title_asset_path):
            title_asset = Image.open(title_asset_path).convert("RGBA")
            # Centrer l'asset horizontalement, positionner à 87px du top
            title_asset_x = (CANVAS_SIZE[0] - title_asset.size[0]) // 2
            canvas.alpha_composite(title_asset, (title_asset_x, title_bg_top))
    
    # 7. CONTENU (Inter Medium 39px, NOIR, letter spacing +1%)
    content_font = _load_font(os.path.join(ASSETS_DIR, "Inter_18pt-Medium.ttf"), 39, weight=500)
    content_letter_spacing = int(39 * 0.01)
    
    # Position contenu : après le titre
    content_y = title_bg_top + title_bg_height + 20  # 20px gap après title_bg
    content_max_width = CANVAS_SIZE[0] - (LEFT_MARGIN * 2)
    
    # Wrap le contenu
    content_lines = _wrap_text(content.replace("**", ""), draw, content_font, content_max_width)
    content_line_height = int(39 * 1.2)
    
    for line in content_lines[:6]:  # Max 6 lignes
        if content_y + content_line_height > image_y_position - 20:
            break
        draw.text((LEFT_MARGIN, content_y), line, font=content_font, fill="black", spacing=content_letter_spacing)
        content_y += content_line_height
    
    output = BytesIO()
    canvas.convert("RGB").save(output, format="PNG")
    return output.getvalue()


def generate_cover_slide(
    hook: str,
    image_url: Optional[str] = None,
    image_bytes: Optional[bytes] = None
) -> bytes:
    """
    Génère la slide de couverture (slide 0) pour Doss.
    Comme Eco : top_bar + Logo + Logo_slide0 + HOOK + image 5:4 en bas.
    """
    if not image_url and not image_bytes:
        raise ValueError("Aucune image disponible pour la cover.")
    if not hook:
        raise ValueError("Aucun hook disponible pour la cover.")
    
    if image_bytes:
        base_img = _load_image_from_bytes(image_bytes)
    else:
        base_img = _load_image_from_url(image_url)  # type: ignore[arg-type]
    
    # Redimensionner l'image de fond en 1080×864 (5:4)
    base_img = _cover_resize(base_img, COVER_IMAGE_SIZE)
    
    # Créer le canvas complet 1080×1350 avec fond #F4F4EB (beige/crème)
    canvas = Image.new("RGBA", CANVAS_SIZE, (244, 244, 235, 255))  # #F4F4EB
    
    # 1. Coller l'image de fond en BAS du canvas
    # Canvas height: 1350, Image height: 864 → Y position: 1350 - 864 = 486
    image_y_position = CANVAS_SIZE[1] - COVER_IMAGE_SIZE[1]
    if base_img.mode != 'RGBA':
        base_img = base_img.convert('RGBA')
    canvas.alpha_composite(base_img, (0, image_y_position))
    
    # 2. Overlay Slide0 - Force 1100px de large
    overlay_slide0_path = os.path.join(ASSETS_DIR, "Overlay_Slide0.png")
    overlay_height = 0  # Pour positionner le Swipe plus tard
    overlay_x_offset = 0
    if os.path.exists(overlay_slide0_path):
        overlay_slide0 = Image.open(overlay_slide0_path).convert("RGBA")
        original_width, original_height = overlay_slide0.size
        target_width = 1100
        scale = target_width / original_width
        target_height = int(original_height * scale)
        overlay_slide0 = overlay_slide0.resize((target_width, target_height), Image.LANCZOS)
        x_offset = (CANVAS_SIZE[0] - target_width) // 2
        overlay_x_offset = x_offset
        overlay_height = target_height
        canvas.alpha_composite(overlay_slide0, (x_offset, 0))
    
    # 3. Top bar collée en haut
    top_bar_path = os.path.join(ASSETS_DIR, "top_bar.png")
    if os.path.exists(top_bar_path):
        top_bar = Image.open(top_bar_path).convert("RGBA")
        if top_bar.size[0] != CANVAS_SIZE[0]:
            scale = CANVAS_SIZE[0] / top_bar.size[0]
            top_bar = top_bar.resize(
                (int(top_bar.size[0] * scale), int(top_bar.size[1] * scale)),
                Image.LANCZOS
            )
        canvas.alpha_composite(top_bar, (0, 0))
    
    draw = ImageDraw.Draw(canvas)
    
    # Logo principal (haut) - cover (scale x2 = 400×130) - collé en haut au centre
    logo_path = os.path.join(ASSETS_DIR, "Logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_size = (LOGO_SIZE[0] * 2, LOGO_SIZE[1] * 2)  # 400×130
        logo = logo.resize(logo_size, Image.LANCZOS)
        logo_x = (CANVAS_SIZE[0] - logo_size[0]) // 2
        canvas.alpha_composite(logo, (logo_x, 0))
    
    # Logo slide 0 - "Le Doss'" (213px top, 45px left)
    cover_logo_path = os.path.join(ASSETS_DIR, "Logo_slide_0.png")
    cover_logo_height = 0
    if os.path.exists(cover_logo_path):
        cover_logo = Image.open(cover_logo_path).convert("RGBA")
        cover_logo_height = cover_logo.size[1]
        canvas.alpha_composite(cover_logo, (45, 213))
    
    # Hook en 3 lignes : 51px sous le logo, 50px left
    # Format : "LIGNE1|Ligne 2 et 3" (séparateur |)
    # Ligne 1 : Inter Bold 100px, letter spacing -9%, MAJUSCULES
    # Lignes 2-3 : Manrope SemiBold 58px, letter spacing -1%
    
    hook_text = hook.strip()
    
    # Parser le hook : séparation par "|"
    if "|" in hook_text:
        hook_line1_text = hook_text.split("|")[0].strip().upper()
        hook_line23_text = hook_text.split("|")[1].strip()
    else:
        # Fallback si pas de séparateur
        words = hook_text.split()
        hook_line1_text = words[0].upper() if words else ""
        hook_line23_text = " ".join(words[1:]) if len(words) > 1 else ""
    
    # Position de départ : 213px (logo top) + hauteur du logo + 51px
    hook_y = 213 + cover_logo_height + 51
    hook_x = 50
    
    # LIGNE 1 : Sujet principal (Inter Bold 100px, -9%)
    if hook_line1_text:
        hook_line1_font = _load_font(FONT_HOOK_LINE1_PATH, HOOK_LINE1_FONT_SIZE, weight=700)
        line1_letter_spacing = int(HOOK_LINE1_FONT_SIZE * HOOK_LINE1_LETTER_SPACING)
        draw.text((hook_x, hook_y), hook_line1_text, font=hook_line1_font, fill="#000000", spacing=line1_letter_spacing)
        hook_y += int(HOOK_LINE1_FONT_SIZE * 1.2)
    
    # LIGNES 2-3 : Reste du hook (Manrope SemiBold 58px, -1%)
    if hook_line23_text:
        hook_line23_font = _load_font(FONT_HOOK_PATH, HOOK_LINE23_FONT_SIZE, weight=HOOK_FONT_WEIGHT)
        line23_letter_spacing = int(HOOK_LINE23_FONT_SIZE * HOOK_LINE23_LETTER_SPACING)
        
        # Wrap sur 2 lignes max
        hook_max_width = CANVAS_SIZE[0] - 100  # Marges 50px de chaque côté
        hook_lines_23 = _wrap_text(hook_line23_text, draw, hook_line23_font, hook_max_width)
        hook_line23_height = int(HOOK_LINE23_FONT_SIZE * 1.2)
        
        for line in hook_lines_23[:2]:  # Max 2 lignes
            draw.text((hook_x, hook_y), line, font=hook_line23_font, fill="#000000", spacing=line23_letter_spacing)
            hook_y += hook_line23_height
    
    # Swipe (cover) - 84px de large, en bas à droite de l'Overlay_Slide0
    # Position : 50px du bas de l'overlay, 50px de margin right (par rapport à l'overlay)
    swipe_path = os.path.join(ASSETS_DIR, "Swipe.png")
    if os.path.exists(swipe_path) and overlay_height > 0:
        swipe = Image.open(swipe_path).convert("RGBA")
        original_width, original_height = swipe.size
        target_width = 84
        scale = target_width / original_width
        target_height = int(original_height * scale)
        swipe = swipe.resize((target_width, target_height), Image.LANCZOS)
        
        # Position par rapport à l'overlay (1100px de large, centré avec offset)
        # Overlay right edge = overlay_x_offset + 1100
        # Swipe X = (overlay right edge) - 50 (margin) - swipe width
        swipe_x = overlay_x_offset + 1100 - 50 - swipe.size[0]
        # Swipe Y = overlay_height - 50 (du bas) - swipe height
        swipe_y = overlay_height - 50 - swipe.size[1]
        
        canvas.alpha_composite(swipe, (swipe_x, swipe_y))
    
    output = BytesIO()
    canvas.convert("RGB").save(output, format="PNG")
    return output.getvalue()

