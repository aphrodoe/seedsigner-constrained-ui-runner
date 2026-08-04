"""
Hardware driver for SSD1306 OLED displays over I2C.

Handles PIL image buffering and luma.oled hardware communication.
All text rendering logic is delegated to the shared graphics utility
(src/utils/graphics.py) to ensure hardware-agnostic consistency.
"""
from PIL import Image, ImageDraw, ImageFont

try:
    # pyrefly: ignore [missing-import]
    from luma.core.interface.serial import i2c

    # pyrefly: ignore [missing-import]
    from luma.oled.device import ssd1306
    HAS_LUMA = True
except ImportError:
    HAS_LUMA = False

from src.utils.graphics import compute_text_grid, draw_text_line


class OledSSD1306:
    """
    Hardware driver for SSD1306 OLED displays over I2C.

    The text grid (cols, rows) is dynamically computed from the physical pixel
    dimensions and the loaded font metrics — no hardcoded values.
    """
    def __init__(self, i2c_port: int = 1, i2c_addr: int = 0x3C, width: int = 128, height: int = 32):
        if not HAS_LUMA:
            raise ImportError("luma.oled is required for OledSSD1306. Install with: pip install luma.oled")

        serial = i2c(port=i2c_port, address=i2c_addr)
        self.device = ssd1306(serial, width=width, height=height)

        self.width = width
        self.height = height
        import os
        font_path = os.path.join(os.path.dirname(__file__), '../utils/fonts/DejaVuSansMono.ttf')
        self.font = ImageFont.truetype(font_path, size=10)

        # Dynamically compute the text grid from pixel dimensions and font metrics
        self.cols, self.rows, self.line_height = compute_text_grid(width, height, self.font)

        self.clear()

    def write_lines(self, lines: list[str]):
        """Draw text lines to a monochrome buffer and flush to OLED."""
        image = Image.new("1", (self.width, self.height))
        draw = ImageDraw.Draw(image)

        for i, line in enumerate(lines):
            y = i * self.line_height
            if y + self.line_height > self.height:
                break  # Don't render rows that would clip
            draw_text_line(draw, image, line, y, self.font, self.width, fill="white")

        self.device.display(image)

    def clear(self):
        """Clear the OLED hardware."""
        self.device.clear()
