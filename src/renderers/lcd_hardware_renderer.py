from typing import Any
from src.renderers.base_renderer import BaseRenderer
from src.renderers.text_renderer import TextRenderer
from src.drivers.lcd_i2c import LCDI2C
from src.screen_state import ScreenState

class LCDHardwareRenderer(BaseRenderer):
    def __init__(self, rows: int, cols: int, i2c_addr: int = 0x27, bus_num: int = 1):
        super().__init__(visible_rows=rows - 1)
        self.rows = rows
        self.cols = cols
        self.text_renderer = TextRenderer(rows=rows, cols=cols)
        
        # Initialize hardware
        self.lcd = LCDI2C(i2c_addr=i2c_addr, bus_num=bus_num, rows=rows, cols=cols)
        self.clear()

    def render(self, state: ScreenState) -> Any:
        """Render the state to the physical LCD display."""
        # Get the formatted lines from the TextRenderer
        lines = self.text_renderer.render(state)
        
        # Translate Unicode icons to CGRAM byte locations
        translated_lines = []
        cgram_map = {"✓": chr(0), "⚠": chr(1), "‼": chr(2), "✕": chr(3)}
        for line in lines:
            for uni, cgram in cgram_map.items():
                line = line.replace(uni, cgram)
            translated_lines.append(line)
        
        # Write them to the hardware
        self.lcd.write_lines(translated_lines)
        return translated_lines

    def clear(self):
        """Clear the hardware LCD."""
        self.lcd.clear()
