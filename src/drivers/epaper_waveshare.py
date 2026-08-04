"""
Hardware driver for Waveshare 1.54" E-Paper display over SPI.

Handles PIL image buffering and epd1in54_V2 hardware communication.
All text rendering logic is delegated to the shared graphics utility
(src/utils/graphics.py) to ensure hardware-agnostic consistency.
"""
from PIL import Image, ImageDraw, ImageFont

try:
    # pyrefly: ignore [missing-import]
    import epaper
    HAS_EPD = True
    EPD_ERROR = None
except Exception as e:
    HAS_EPD = False
    EPD_ERROR = repr(e)

from src.utils.graphics import compute_text_grid, draw_text_line


class EpaperWaveshare:
    """
    Hardware driver for the Waveshare 1.54" E-Paper display over SPI.

    The text grid (cols, rows) is dynamically computed from the physical pixel
    dimensions and the loaded font metrics — no hardcoded values.
    """
    def __init__(self):
        if not HAS_EPD:
            raise ImportError(f"waveshare-epaper failed to load. Underlying error: {EPD_ERROR}")

        self.device = epaper.epaper('epd1in54_V2').EPD()
        self.device.init(0)  # 0 for full refresh, 1 for partial
        self.width = self.device.width
        self.height = self.device.height

        import os
        font_path = os.path.join(os.path.dirname(__file__), '../utils/fonts/DejaVuSansMono.ttf')
        self.font = ImageFont.truetype(font_path, size=14)

        # Dynamically compute the text grid from pixel dimensions and font metrics
        self.cols, self.rows, self.line_height = compute_text_grid(self.width, self.height, self.font)

        self.clear()

    def write_lines(self, lines: list[str]):
        """Draw text lines to a monochrome buffer and flush to E-Paper."""
        # E-Paper: white background, black text
        image = Image.new("1", (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)

        for i, line in enumerate(lines):
            y = i * self.line_height
            if y + self.line_height > self.height:
                break
            draw_text_line(draw, image, line, y, self.font, self.width, fill=0)

        buffer = self.device.getbuffer(image)

        # E-paper sleep() closes the SPI bus. We must re-init before waking up.
        if not hasattr(self, "is_first_frame") or self.is_first_frame:
            self.device.init(0)  # 0 for full refresh
            self.device.displayPartBaseImage(buffer)
            self.is_first_frame = False
        else:
            self.device.init(1)  # 1 for fast partial refresh
            self.device.displayPart(buffer)

        self.device.sleep()

    def clear(self):
        """Clear the E-Paper hardware."""
        self.device.init(0)
        self.device.Clear(0xFF)
        self.device.sleep()
