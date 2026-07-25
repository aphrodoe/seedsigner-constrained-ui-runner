from PIL import Image, ImageDraw, ImageFont
import os

try:
    # pyrefly: ignore [missing-import]
    from luma.core.interface.serial import i2c
    
    # pyrefly: ignore [missing-import]
    from luma.oled.device import ssd1306
    HAS_LUMA = True
except ImportError:
    HAS_LUMA = False

class OledSSD1306:
    """
    Hardware driver for the 128x64 SSD1306 OLED display over I2C.
    Handles PIL image buffering and luma.oled hardware communication.
    """
    def __init__(self, i2c_port: int = 1, i2c_addr: int = 0x3C, width: int = 128, height: int = 64):
        if not HAS_LUMA:
            raise ImportError("luma.oled is required for OledSSD1306. Install with: pip install luma.oled")
            
        serial = i2c(port=i2c_port, address=i2c_addr)
        self.device = ssd1306(serial, width=width, height=height)
        
        # Use 8px Cozette bitmap font instead of default to fix bottom clipping
        font_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'fonts', 'cozette.bdf')
        self.font = ImageFont.load(font_path)
        self.clear()

    def write_lines(self, lines: list[str]):
        """Draw text lines to a monochrome buffer and flush to OLED."""
        # Create a new blank 1-bit image (black background)
        image = Image.new("1", (self.device.width, self.device.height))
        draw = ImageDraw.Draw(image)
        
        # Draw the text lines (8 rows * 8px height = 64px)
        for i, line in enumerate(lines):
            y = i * 8
            draw.text((0, y), line, font=self.font, fill="white")
            
        # Send buffer to OLED hardware
        self.device.display(image)

    def clear(self):
        """Clear the OLED hardware."""
        self.device.clear()
