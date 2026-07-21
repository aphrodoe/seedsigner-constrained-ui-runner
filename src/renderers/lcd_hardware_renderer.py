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
        
        # Translate Unicode icons to CGRAM byte locations or ASCII fallbacks.
        # The HD44780 LCD has only 8 CGRAM slots (0-7), already occupied by
        # the status icons loaded in lcd_i2c.py. Additional Unicode chars
        # used by Week 8+ screens are mapped to ASCII approximations.
        translated_lines = []
        cgram_map = {
            # CGRAM slot 0-7 (actual custom bitmaps on the LCD)
            "✓": chr(0), "⚠": chr(1), "‼": chr(2), "✕": chr(3),
            "▦": chr(4), "⚿": chr(5), "⚒": chr(6), "⚙": chr(7),
            # ASCII fallbacks for icons without CGRAM slots
            "⎇": "*",     # Derivation (branch)
            "@": "@",     # Fingerprint (already ASCII)
            "₿": "B",     # Bitcoin
            "●": "o",     # Radio button filled
            "⌨": "K",     # Keyboard mode indicator
            "✎": "E",     # Edit
            "✗": "x",     # Alternative cross
            "ℹ": "i",     # Info
            "·": ".",     # Middle dot
        }
        for line in lines:
            for uni, replacement in cgram_map.items():
                line = line.replace(uni, replacement)
            translated_lines.append(line)
        
        # Write them to the hardware
        self.lcd.write_lines(translated_lines)
        return translated_lines

    def clear(self):
        """Clear the hardware LCD."""
        self.lcd.clear()
