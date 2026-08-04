from src.screen_state import ScreenState

class BaseRenderer:
    def __init__(self, visible_rows: int):
        self.visible_rows = visible_rows
        
    def render(self, state: ScreenState):
        """Render the current screen state to the output device."""
        raise NotImplementedError
        
    def clear(self):
        """Clear the output device."""
        raise NotImplementedError
