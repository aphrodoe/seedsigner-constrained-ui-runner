"""
BaseRenderer: Abstract base class for all display renderers.

All hardware and simulator renderers should inherit from this class
to ensure a consistent interface for the DisplayManager factory.
"""
from src.screen_state import ScreenState


class BaseRenderer:
    """Base class for all renderers in the constrained UI system."""

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.visible_rows = rows - 1  # Row 0 is always the title

    def render(self, state: ScreenState):
        """Render the current screen state to the output device."""
        raise NotImplementedError

    def clear(self):
        """Clear the output device."""
        raise NotImplementedError
