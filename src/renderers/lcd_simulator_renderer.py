"""
LCDSimulatorRenderer: Wraps TextRenderer output in an ASCII box
and prints it to the terminal, simulating a physical character LCD.
"""

from src.renderers.base_renderer import BaseRenderer
from src.renderers.text_renderer import TextRenderer
from src.screen_state import ScreenState


class LCDSimulatorRenderer(BaseRenderer):
    def __init__(self, rows: int, cols: int):
        super().__init__(visible_rows=rows - 1)  # row 0 is the title
        self.rows = rows
        self.cols = cols
        self.text_renderer = TextRenderer(rows, cols)

    def render(self, state: ScreenState):
        self.clear()
        lines = self.text_renderer.render(state)

        # Draw ASCII frame
        print(f"┌{'─' * self.cols}┐")
        for line in lines:
            print(f"│{line}│")
        print(f"└{'─' * self.cols}┘")

    def clear(self):
        print("\033[H\033[J", end="")
