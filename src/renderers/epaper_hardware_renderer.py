from typing import Any
from src.renderers.base_renderer import BaseRenderer
from src.renderers.text_renderer import TextRenderer
from src.screen_state import ScreenState
from src.drivers.epaper_waveshare import EpaperWaveshare

class EpaperHardwareRenderer(BaseRenderer):
    """
    Renders the Constrained UI onto a Waveshare E-Paper display.
    Passes a text grid to the E-Paper hardware driver.
    """
    def __init__(self):
        self.epaper = EpaperWaveshare()
        
        # 6x8 font on a 200x200 screen -> 33 cols, 25 rows
        self.cols = self.epaper.width // 6
        self.rows = self.epaper.height // 8
        
        super().__init__(visible_rows=self.rows - 1)
        self.text_renderer = TextRenderer(rows=self.rows, cols=self.cols)

    def render(self, state: ScreenState) -> Any:
        # Get the formatted lines from the TextRenderer
        lines = self.text_renderer.render(state)
        
        # Write them to the hardware
        self.epaper.write_lines(lines)
        return lines

    def clear(self):
        """Clear the E-Paper hardware."""
        self.epaper.clear()
