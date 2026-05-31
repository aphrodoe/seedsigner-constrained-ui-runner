from enum import Enum
from typing import Dict, Any, List

class ScreenType(Enum):
    BUTTON_LIST = "button_list_screen"
    MAIN_MENU = "main_menu_screen"
    LARGE_ICON_STATUS = "large_icon_status_screen"
    SCREENSAVER = "screensaver_screen"
    
    @classmethod
    def from_str(cls, value: str):
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown screen type: {value}")


class ScreenState:
    def __init__(self, screen_type_str: str, context: Dict[str, Any], visible_rows: int = 1):
        self.screen_type = ScreenType.from_str(screen_type_str)
        self.context = context
        self.visible_rows = visible_rows
        
        self.selected_index = 0
        self.scroll_offset = 0
        
        self.items = self._extract_items()
        
    def _extract_items(self) -> List[Any]:
        if "button_list" in self.context:
            return self.context["button_list"]
        if "button_grid" in self.context:
            return self.context["button_grid"]
        if "button_data" in self.context:
            return self.context["button_data"]
        return []
        
    def move_up(self) -> bool:
        """Move cursor up. Returns True if selection changed."""
        if not self.items or self.selected_index <= 0:
            # Allow wrapping to bottom? The original UI doesn't generally wrap, but let's implement strict boundaries.
            return False
        
        self.selected_index -= 1
        self._adjust_scroll()
        return True
        
    def move_down(self) -> bool:
        """Move cursor down. Returns True if selection changed."""
        if not self.items or self.selected_index >= len(self.items) - 1:
            return False
            
        self.selected_index += 1
        self._adjust_scroll()
        return True

    def page_up(self) -> bool:
        """Move cursor up by visible_rows. Used for LEFT/RIGHT keys acting as page up/down on char LCDs."""
        if not self.items or self.selected_index <= 0:
            return False
            
        self.selected_index = max(0, self.selected_index - self.visible_rows)
        self._adjust_scroll()
        return True
        
    def page_down(self) -> bool:
        """Move cursor down by visible_rows."""
        if not self.items or self.selected_index >= len(self.items) - 1:
            return False
            
        self.selected_index = min(len(self.items) - 1, self.selected_index + self.visible_rows)
        self._adjust_scroll()
        return True

    def _adjust_scroll(self):
        """Adjusts the scroll offset to keep the selected index visible within the visible window."""
        if self.visible_rows <= 0:
            return

        if self.selected_index < self.scroll_offset:
            # Scroll up to reveal the item
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.visible_rows:
            # Scroll down to reveal the item
            self.scroll_offset = self.selected_index - self.visible_rows + 1
