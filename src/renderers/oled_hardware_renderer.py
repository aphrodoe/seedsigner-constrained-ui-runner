from typing import Any
from src.renderers.base_renderer import BaseRenderer
from src.renderers.text_renderer import TextRenderer
from src.screen_state import ScreenState
from src.drivers.oled_ssd1306 import OledSSD1306

class OledHardwareRenderer(BaseRenderer):
    """
    Renders the Constrained UI onto a 128x64 SSD1306 OLED display.
    Uses the TextRenderer to generate a Tier 2 (21 cols x 8 rows) layout
    and passes it to the OLED hardware driver.
    """
    def __init__(self, i2c_port: int = 1, i2c_addr: int = 0x3C, width: int = 128, height: int = 64):
        # 6x8 font -> width // 6, height // 8
        self.cols = width // 6
        self.rows = height // 8
        super().__init__(visible_rows=self.rows - 1)
        self.text_renderer = TextRenderer(rows=self.rows, cols=self.cols)
        self.oled = OledSSD1306(i2c_port=i2c_port, i2c_addr=i2c_addr, width=width, height=height)

    def render(self, state: ScreenState) -> Any:
        # Get the formatted lines from the TextRenderer
        lines = self.text_renderer.render(state)
        
        # Write them to the hardware
        self.oled.write_lines(lines)
        return lines

    def clear(self):
        """Clear the hardware OLED."""
        self.oled.clear()
