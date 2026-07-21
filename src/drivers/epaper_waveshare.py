from PIL import Image, ImageDraw, ImageFont

try:
    # pyrefly: ignore [missing-import]
    from waveshare_epd import epd1in54_V2
    HAS_EPD = True
except ImportError:
    HAS_EPD = False

class EpaperWaveshare:
    """
    Hardware driver for the Waveshare 1.54" E-Paper display over SPI.
    Handles PIL image buffering and epd1in54_V2 hardware communication.
    """
    def __init__(self):
        if not HAS_EPD:
            raise ImportError("waveshare-epaper is required for EpaperWaveshare. Install with: pip install waveshare-epaper")
            
        self.device = epd1in54_V2.EPD()
        self.device.init(0) # 0 for full refresh, 1 for partial
        self.width = self.device.width
        self.height = self.device.height
        
        # Default PIL font is 6x8 pixels
        self.font = ImageFont.load_default()
        self.clear()

    def write_lines(self, lines: list[str]):
        """Draw text lines to a monochrome buffer and flush to E-Paper."""
        # Create a new blank 1-bit image (white background for E-Paper)
        image = Image.new("1", (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)
        
        # Draw the text lines (black text)
        for i, line in enumerate(lines):
            y = i * 8
            draw.text((0, y), line, font=self.font, fill=0)
            
        # Send buffer to E-Paper hardware
        self.device.display(self.device.getbuffer(image))
        self.device.sleep()

    def clear(self):
        """Clear the E-Paper hardware."""
        self.device.Clear(0xFF)
        self.device.sleep()
