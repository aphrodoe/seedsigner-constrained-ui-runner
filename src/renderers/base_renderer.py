from abc import ABC, abstractmethod
from src.screen_state import ScreenState

class BaseRenderer(ABC):
    def __init__(self, visible_rows: int):
        self.visible_rows = visible_rows
        
    @abstractmethod
    def render(self, state: ScreenState):
        """Render the current screen state to the output device."""
        pass
        
    @abstractmethod
    def clear(self):
        """Clear the output device."""
        pass
