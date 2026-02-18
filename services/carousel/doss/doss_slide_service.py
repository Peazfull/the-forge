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
FONT_HOOK_PATH = os.path.join(ASSETS_DIR, "Manrope-SemiBold.ttf")  # Hook slide 0
HOOK_FONT_SIZE = 68
HOOK_FONT_WEIGHT = 600  # SemiBold


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
    if not image_url and not image_bytes:
        raise ValueError("Aucune image disponible pour le doss.")

    if image_bytes:
        base_img = _load_image_from_bytes(image_bytes)
    else:
        base_img = _load_image_from_url(image_url)  # type: ignore[arg-type]

    top_img = _cover_resize(base_img, IMAGE_TOP_SIZE)
    canvas = Image.new("RGBA", CANVAS_SIZE, "white")
    canvas.alpha_composite(top_img, (0, 0))

    filter_path = os.path.join(ASSETS_DIR, "filter_main.png")
    if os.path.exists(filter_path):
        overlay = Image.open(filter_path).convert("RGBA")
        if overlay.size != CANVAS_SIZE:
            overlay = overlay.resize(CANVAS_SIZE, Image.LANCZOS)
        canvas.alpha_composite(overlay, (0, 0))

    logo_path = os.path.join(ASSETS_DIR, "Logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize(LOGO_SIZE, Image.LANCZOS)
        logo_x = (CANVAS_SIZE[0] - LOGO_SIZE[0]) // 2
        canvas.alpha_composite(logo, (logo_x, LOGO_TOP))

    if position == 1:
        title_zoom_path = os.path.join(ASSETS_DIR, "Title_zoom.png")
        if os.path.exists(title_zoom_path):
            title_zoom = Image.open(title_zoom_path).convert("RGBA")
            if title_zoom.size != TITLE_ZOOM_SIZE:
                title_zoom = title_zoom.resize(TITLE_ZOOM_SIZE, Image.LANCZOS)
            canvas.alpha_composite(title_zoom, (TITLE_ZOOM_LEFT, TITLE_ZOOM_TOP))

    bottom_bg_path = os.path.join(ASSETS_DIR, "doss_bg_bas.png")
    if os.path.exists(bottom_bg_path):
        bottom_bg = Image.open(bottom_bg_path).convert("RGBA")
        if bottom_bg.size != (CANVAS_SIZE[0], IMAGE_TOP_HEIGHT):
            bottom_bg = bottom_bg.resize((CANVAS_SIZE[0], IMAGE_TOP_HEIGHT), Image.LANCZOS)
        canvas.alpha_composite(bottom_bg, (0, IMAGE_TOP_HEIGHT))

    swipe_path = os.path.join(ASSETS_DIR, "Swipe.png")
    if os.path.exists(swipe_path):
        swipe = Image.open(swipe_path).convert("RGBA")
        if swipe.size != SWIPE_SIZE:
            swipe = swipe.resize(SWIPE_SIZE, Image.LANCZOS)
        swipe_x = CANVAS_SIZE[0] - SWIPE_SIZE[0] - SWIPE_MARGIN_RIGHT
        swipe_y = CANVAS_SIZE[1] - SWIPE_SIZE[1] - SWIPE_MARGIN_BOTTOM
        canvas.alpha_composite(swipe, (swipe_x, swipe_y))

    # Suppression overlay/title_bg pour le nouveau design

    draw = ImageDraw.Draw(canvas)

    text_area_top = 570
    text_area_height = CANVAS_SIZE[1] - text_area_top - CONTENT_BOTTOM_MARGIN
    content_max_width = CANVAS_SIZE[0] - LEFT_MARGIN - RIGHT_MARGIN

    title_max_width = content_max_width
    if title.strip() == title.strip().upper():
        title_text = title
    else:
        title_text = title.upper()

    title_font, title_lines = _fit_text(
        draw,
        title_text,
        title_max_width,
        120,
        start_size=TITLE_FONT_SIZE,
        font_path=FONT_TITLE_PATH,
        weight=TITLE_FONT_WEIGHT,
    )
    title_line_height = int(title_font.size * 1.2)

    y = text_area_top
    for line in title_lines[:2]:
        x = LEFT_MARGIN
        words = line.split()
        for word in words:
            token_width = draw.textlength(word, font=title_font)
            rect = (
                x - HIGHLIGHT_PAD_X,
                y - TITLE_HIGHLIGHT_PAD_Y,
                x + token_width + HIGHLIGHT_PAD_X,
                y + title_line_height + TITLE_HIGHLIGHT_PAD_Y
            )
            draw.rectangle(rect, fill=HIGHLIGHT_BG_COLOR)
            draw.text((x, y), word, font=title_font, fill=HIGHLIGHT_TEXT_COLOR)
            space_width = draw.textlength(" ", font=title_font)
            x += token_width + space_width
        y += title_line_height

    content_y = y + CONTENT_TOP_GAP
    content_max_height = (text_area_top + text_area_height) - content_y
    content_plain = _strip_highlight_markers(content)
    content_font, content_lines_plain = _fit_text(
        draw,
        content_plain,
        content_max_width,
        content_max_height,
        start_size=CONTENT_FONT_SIZE,
        font_path=FONT_CONTENT_PATH,
        weight=CONTENT_FONT_WEIGHT,
    )
    content_line_height = int(content_font.size * 1.2)
    y = content_y
    blocks = content.splitlines()
    for idx, block in enumerate(blocks):
        if y + content_line_height > CANVAS_SIZE[1] - CONTENT_BOTTOM_MARGIN:
            break
        if not block.strip():
            y += content_line_height * (1 + PARAGRAPH_EXTRA_LINE_GAP)
            continue
        content_tokens = _tokenize_highlights(block)
        content_lines = _wrap_highlight_tokens(content_tokens, draw, content_font, content_max_width)
        for line_tokens in content_lines:
            if y + content_line_height > CANVAS_SIZE[1] - CONTENT_BOTTOM_MARGIN:
                break
            x = LEFT_MARGIN
            for word, is_highlight in line_tokens:
                token_text = word
                token_width = draw.textlength(token_text, font=content_font)
                if is_highlight:
                    rect = (
                        x - HIGHLIGHT_PAD_X,
                        y - CONTENT_HIGHLIGHT_PAD_Y,
                        x + token_width + HIGHLIGHT_PAD_X,
                        y + content_line_height + CONTENT_HIGHLIGHT_PAD_Y
                    )
                    draw.rectangle(rect, fill=HIGHLIGHT_BG_COLOR)
                    draw.text((x, y), token_text, font=content_font, fill=HIGHLIGHT_TEXT_COLOR)
                else:
                    draw.text((x, y), token_text, font=content_font, fill=CONTENT_COLOR)
                space_width = draw.textlength(" ", font=content_font)
                x += token_width + space_width
            y += content_line_height
        if idx < len(blocks) - 1:
            y += content_line_height * PARAGRAPH_EXTRA_LINE_GAP

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
    
    # Logo slide 0 - "Le Doss'" (168px top, 45px left)
    cover_logo_path = os.path.join(ASSETS_DIR, "Logo_slide0.png")
    cover_logo_height = 0
    if os.path.exists(cover_logo_path):
        cover_logo = Image.open(cover_logo_path).convert("RGBA")
        cover_logo_height = cover_logo.size[1]
        canvas.alpha_composite(cover_logo, (45, 168))
    
    # Hook - 51px sous le logo, 50px left, taille 68, noir, letter spacing -1%
    hook_text = hook.strip()
    hook_font = _load_font(FONT_HOOK_PATH, HOOK_FONT_SIZE, weight=HOOK_FONT_WEIGHT)
    
    # Position : 168px (logo top) + hauteur du logo + 51px
    hook_y = 168 + cover_logo_height + 51
    hook_x = 50
    
    # Letter spacing -1%
    letter_spacing = int(HOOK_FONT_SIZE * -0.01)
    
    # Wrap le hook si trop long (max 2 lignes)
    hook_max_width = CANVAS_SIZE[0] - 100  # Marges 50px de chaque côté
    hook_lines = _wrap_text(hook_text, draw, hook_font, hook_max_width)
    hook_line_height = int(HOOK_FONT_SIZE * 1.2)
    
    # Première lettre en majuscule
    if hook_lines:
        first_line = hook_lines[0]
        if first_line:
            hook_lines[0] = first_line[0].upper() + first_line[1:]
    
    # Afficher le hook (max 2 lignes)
    for line in hook_lines[:2]:
        draw.text((hook_x, hook_y), line, font=hook_font, fill="#363636", spacing=letter_spacing)
        hook_y += hook_line_height
    
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

