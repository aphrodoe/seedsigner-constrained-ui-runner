"""
Hardware-agnostic graphical text rendering utilities.

This module provides shared functions for rendering proportionally-spaced text
with icon substitution onto PIL Image objects. It is used by all graphical
display drivers (OLED, E-Paper) to ensure consistent, pixel-perfect rendering
regardless of the underlying hardware.

Key design decisions:
  - Font metrics are measured dynamically from the actual loaded font, so that
    changing fonts in the future does not require any code edits.
  - Column/row calculations are derived from pixel dimensions and measured font
    metrics, ensuring true hardware agnosticism.
  - Right-alignment of pagination indicators (e.g. "3/4") is handled globally
    here, so every graphical driver benefits uniformly.
"""

import re
from PIL import Image, ImageDraw, ImageFont


# ── Icon Bitmaps ────────────────────────────────────────────────────────────
# Pixel art bitmaps for SeedSigner Unicode icons. Stored globally so that both
# the OLED and E-Paper drivers share the exact same artwork.

def _create_bitmap(pattern: list[str]) -> Image.Image:
    """Create an 8x8 monochrome PIL Image from a text pattern."""
    img = Image.new("1", (8, 8))
    draw = ImageDraw.Draw(img)
    for y, row in enumerate(pattern):
        for x, char in enumerate(row):
            if char == '#':
                draw.point((x, y), fill="white")
    return img

ICON_WIDTH = 8  # Each icon bitmap is 8px wide

ICONS = {
    "▦": _create_bitmap([" ###### ", " #    # ", " # ## # ", " # ## # ", " #    # ", " ###### ", "        ", "        "]),
    "⚿": _create_bitmap(["   ##   ", "  #  #  ", "  #  #  ", "   ##   ", "   ##   ", "  ###   ", "   ##   ", "  ###   "]),
    "⚒": _create_bitmap([" ##  ## ", "  ####  ", "   ##   ", "  ####  ", " #    # ", "        ", "        ", "        "]),
    "⚙": _create_bitmap(["  #  #  ", "   ##   ", " ###### ", " ##  ## ", " ###### ", "   ##   ", "  #  #  ", "        "]),
    "✓": _create_bitmap(["       #", "      # ", "     #  ", "#   #   ", " # #    ", "  #     ", "        ", "        "]),
    "✗": _create_bitmap(["#      #", " #    # ", "  #  #  ", "   ##   ", "  #  #  ", " #    # ", "#      #", "        "]),
    "✎": _create_bitmap(["      ##", "     # #", "    #  #", "   #  # ", "  #  #  ", " ## #   ", " ###    ", "        "]),
    "⌨": _create_bitmap(["        ", " ###### ", " # # ## ", " ### ## ", " ###### ", "        ", "        ", "        "]),
}


# ── Font Metrics ────────────────────────────────────────────────────────────

def measure_font(font: ImageFont.ImageFont) -> dict:
    """
    Measure the loaded font and return a metrics dictionary.

    Returns:
        dict with keys:
            line_height: int  — vertical spacing per row (ascent only, tight packing)
            avg_char_width: float — average width across printable ASCII
    """
    import string

    ascent, _descent = font.getmetrics()
    chars = string.ascii_letters + string.digits + " "
    widths = [font.getlength(c) for c in chars]
    avg = sum(widths) / len(widths)

    return {
        "line_height": ascent,
        "avg_char_width": avg,
    }


def compute_text_grid(pixel_width: int, pixel_height: int, font: ImageFont.ImageFont) -> tuple[int, int, int]:
    """
    Given the physical pixel dimensions of a graphical display and a loaded
    PIL font, dynamically compute the text grid dimensions.

    Returns:
        (cols, rows, line_height) — the number of character columns, the number
        of text rows that fit without clipping, and the pixel height per row.
    """
    metrics = measure_font(font)
    line_height = metrics["line_height"]
    avg_char_width = metrics["avg_char_width"]

    cols = int(pixel_width // avg_char_width)
    rows = int(pixel_height // line_height)

    return cols, rows, line_height


# ── Proportional Text Drawing ──────────────────────────────────────────────

def draw_text_line(draw: ImageDraw.Draw, image: Image.Image, line: str,
                   y: int, font: ImageFont.ImageFont, screen_width: int,
                   fill="white"):
    """
    Draw a single text line onto an image with proportional kerning and
    automatic right-alignment of spaced trailing text (e.g. page indicators).

    This is the single source of truth for how graphical displays render text.
    All graphical drivers must call this instead of implementing their own
    character loop.

    Args:
        draw: PIL ImageDraw object bound to `image`.
        image: PIL Image to paste icon bitmaps onto.
        line: The text string to render (may contain icon Unicode characters).
        y: Vertical pixel offset for this line.
        font: Loaded PIL ImageFont.
        screen_width: Physical pixel width of the display.
        fill: Text colour ("white" for OLED, 0 for E-Paper).
    """
    # Detect right-aligned text (e.g. "Settings        3/4")
    # Pattern: non-whitespace left part, 2+ spaces gap, non-whitespace right part
    m = re.match(r'^(\S.*?)\s{2,}(\S.*?)\s*$', line)

    if m:
        left_part = m.group(1)
        right_part = m.group(2)

        # Draw left part
        _draw_chars(draw, image, left_part, 0, y, font, fill)

        # Measure right part and right-align it flush against the display edge
        right_width = _measure_width(right_part, font)
        _draw_chars(draw, image, right_part, screen_width - right_width, y, font, fill)
    else:
        _draw_chars(draw, image, line, 0, y, font, fill)


def _draw_chars(draw: ImageDraw.Draw, image: Image.Image, text: str,
                x: int, y: int, font: ImageFont.ImageFont, fill="white"):
    """Draw a string character-by-character with icon substitution."""
    for char in text:
        if char in ICONS:
            # For dark-on-light displays (fill=0), invert the icon
            icon = ICONS[char]
            if fill == 0:
                from PIL import ImageOps
                icon = ImageOps.invert(icon.convert("L")).convert("1")
            image.paste(icon, (x, y))
            x += ICON_WIDTH
        else:
            draw.text((x, y), char, font=font, fill=fill)
            x += int(font.getlength(char))


def _measure_width(text: str, font: ImageFont.ImageFont) -> int:
    """Measure the pixel width of a string including icon substitutions."""
    w = 0
    for char in text:
        w += ICON_WIDTH if char in ICONS else int(font.getlength(char))
    return w
