#!/usr/bin/env python3
"""Draw golden snapshots as character-LCD images for the README.

    python3 tools/readme_lcd_images.py   -> docs/readme/<screen>_<size>.png

Each character sits in its own cell, as on an HD44780, so the grid stays exact
whatever the glyph widths. Re-run after a layout change (and --update-golden).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "readme"
SCREENS = ["main_menu_screen", "seed_words_screen", "psbt_overview_screen"]
SIZES = ["16x2", "20x4"]

CELL_W, CELL_H, GAP, PAD = 22, 34, 3, 22
BG, OFF, ON = (26, 58, 196), (36, 72, 214), (232, 240, 255)
# ponytail: system font paths (Debian/Ubuntu); DejaVu lacks U+26BF, FreeSerif has it.
FONTS = [ImageFont.truetype(p, 26) for p in (
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf")]


def font_for(ch):
    # A font without the glyph draws its "missing" box; compare against that.
    for f in FONTS:
        if bytes(f.getmask(ch)) != bytes(f.getmask("\U0010FFFD")):
            return f
    return FONTS[0]


def draw(lines, cols, rows):
    w = PAD * 2 + cols * CELL_W + (cols - 1) * GAP
    h = PAD * 2 + rows * CELL_H + (rows - 1) * GAP
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    for r in range(rows):
        line = (lines[r] if r < len(lines) else "").ljust(cols)[:cols]
        for c, ch in enumerate(line):
            x, y = PAD + c * (CELL_W + GAP), PAD + r * (CELL_H + GAP)
            d.rectangle((x, y, x + CELL_W - 1, y + CELL_H - 1), fill=OFF)
            if ch != " ":
                d.text((x + CELL_W / 2, y + CELL_H / 2), ch, font=font_for(ch), fill=ON, anchor="mm")
    return img


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for screen in SCREENS:
        for size in SIZES:
            cols, rows = map(int, size.split("x"))
            text = (ROOT / "tests" / "golden" / screen / "(default)" / f"{size}.txt").read_text()
            draw(text.split("\n"), cols, rows).save(OUT / f"{screen}_{size}.png", optimize=True)
            print(OUT / f"{screen}_{size}.png")
