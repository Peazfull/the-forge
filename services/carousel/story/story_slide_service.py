"""
Génération des slides Story (1080x1920) via Pillow.
Stack: image 16:9 en haut (1/3) + fond blanc + logo + texte noir.
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
    "front", "layout", "assets", "carousel", "story",
)

CANVAS_SIZE = (1080, 1920)
IMAGE_SIDE = CANVAS_SIZE[0]  # carré 1:1 plein large
IMAGE_TOP_HEIGHT = IMAGE_SIDE  # 1080

LOGO_SIZE = (200, 65)
LOGO_TOP = 15

LEFT_MARGIN = 60
RIGHT_MARGIN = 60
TITLE_TOP_GAP = 40
CONTENT_TOP_GAP = 100
CONTENT_BOTTOM_MARGIN = 60
BOTTOM_BG_HEIGHT = 1043
BOTTOM_BG_MARGIN_BOTTOM = 20
BOTTOM_BG_MARGIN_LEFT = 0
OVERLAY_WIDTH = 1064
OVERLAY_HEIGHT = 1047

TITLE_FONT_SIZE = 42
CONTENT_FONT_SIZE = 38
TITLE_FONT_WEIGHT = 600
CONTENT_FONT_WEIGHT = 600

TITLE_COLOR = "#F6F6F6"
CONTENT_COLOR = "#F6F6F6"
HIGHLIGHT_BG_COLOR = "#5B2EFF"
HIGHLIGHT_TEXT_COLOR = "#F6F6F6"
HIGHLIGHT_PAD_X = 6
HIGHLIGHT_PAD_Y = -4
PARAGRAPH_EXTRA_LINE_GAP = 1

FONT_TITLE_PATH = os.path.join(ASSETS_DIR, "Manrope-Bold.ttf")
FONT_CONTENT_PATH = os.path.join(ASSETS_DIR, "Manrope-SemiBold.ttf")


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


def generate_story_slide(
    title: str,
    content: str,
    image_url: Optional[str] = None,
    image_bytes: Optional[bytes] = None
) -> bytes:
    if not image_url and not image_bytes:
        raise ValueError("Aucune image disponible pour la story.")

    if image_bytes:
        base_img = _load_image_from_bytes(image_bytes)
    else:
        base_img = _load_image_from_url(image_url)  # type: ignore[arg-type]

    top_img = _cover_resize(base_img, (IMAGE_SIDE, IMAGE_SIDE))
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

    bottom_bg_path = os.path.join(ASSETS_DIR, "story_bg_bas.png")
    if os.path.exists(bottom_bg_path):
        bottom_bg = Image.open(bottom_bg_path).convert("RGBA")
        if bottom_bg.size != (CANVAS_SIZE[0], 900):
            bottom_bg = bottom_bg.resize((CANVAS_SIZE[0], 900), Image.LANCZOS)
        paste_y = CANVAS_SIZE[1] - bottom_bg.size[1]
        canvas.alpha_composite(bottom_bg, (0, paste_y))

    # Suppression overlay/title_bg pour le nouveau design

    draw = ImageDraw.Draw(canvas)

    text_area_top = IMAGE_TOP_HEIGHT + TITLE_TOP_GAP
    text_area_height = CANVAS_SIZE[1] - text_area_top - CONTENT_BOTTOM_MARGIN
    content_max_width = CANVAS_SIZE[0] - LEFT_MARGIN - RIGHT_MARGIN

    title_max_width = content_max_width

    title_font, title_lines = _fit_text(
        draw,
        title,
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
                y - HIGHLIGHT_PAD_Y,
                x + token_width + HIGHLIGHT_PAD_X,
                y + title_line_height + HIGHLIGHT_PAD_Y
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
    content_line_height = int(content_font.size * 1.35)
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
                        y - HIGHLIGHT_PAD_Y,
                        x + token_width + HIGHLIGHT_PAD_X,
                        y + content_line_height + HIGHLIGHT_PAD_Y
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
