from enum import Enum
from typing import Dict, Any, List

class ScreenType(Enum):
    BUTTON_LIST = "button_list_screen"
    MAIN_MENU = "main_menu_screen"
    LARGE_ICON_STATUS = "large_icon_status_screen"
    SEED_ADD_PASSPHRASE = "seed_add_passphrase_screen"
    SPLASH = "splash_screen"
    SCREENSAVER = "screensaver_screen"
    TOOLS_DICE_ENTROPY_ENTRY = "tools_dice_entropy_entry_screen"
    TOOLS_COIN_FLIP_ENTRY = "tools_coin_flip_entry_screen"
    SEED_BIP85_SELECT_CHILD_INDEX = "seed_bip85_select_child_index_screen"
    SEED_EXPORT_XPUB_CUSTOM_DERIVATION = "seed_export_xpub_custom_derivation_screen"
    
    def is_keyboard(self):
        return self in [
            ScreenType.SEED_ADD_PASSPHRASE,
            ScreenType.TOOLS_DICE_ENTROPY_ENTRY,
            ScreenType.TOOLS_COIN_FLIP_ENTRY,
            ScreenType.SEED_BIP85_SELECT_CHILD_INDEX,
            ScreenType.SEED_EXPORT_XPUB_CUSTOM_DERIVATION
        ]
    
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
        self.max_scroll_offset = 0
        self.marquee_tick = 0
        
        self.entered_text = self.context.get("initial_text", "")
        self.keyboard_modes = []
        self.active_mode_index = 0
        self.char_index = 0
        
        if self.screen_type.is_keyboard():
            self._init_keyboard()
        
        self.items = self._extract_items()
        
    def _init_keyboard(self):
        # Default charsets if none provided (for seed_add_passphrase_screen)
        charsets = self.context.get("charset_modes", {
            "lower": "abcdefghijklmnopqrstuvwxyz ",
            "upper": "ABCDEFGHIJKLMNOPQRSTUVWXYZ ",
            "digits": "0123456789",
            "symbols": "!@#$%^&*()-_=+[]{}|;:,.<>/?"
        })
        self.keyboard_modes = list(charsets.items())
        
        initial_mode = self.context.get("initial_mode", "")
        for i, (name, _) in enumerate(self.keyboard_modes):
            if name == initial_mode:
                self.active_mode_index = i
                break
                
        # Append [DEL] and [OK] to every charset as selectable items
        for i, (name, charset) in enumerate(self.keyboard_modes):
            chars = list(charset)
            chars.extend(["[DEL]", "[OK]"])
            self.keyboard_modes[i] = (name, chars)
        
    def _extract_items(self) -> List[Any]:
        if "button_list" in self.context:
            return self.context["button_list"]
        if "button_grid" in self.context:
            return self.context["button_grid"]
        if "button_data" in self.context:
            return self.context["button_data"]
        return []
        
    def tick(self) -> bool:
        """Increment marquee tick. Returns True to indicate screen needs render."""
        self.marquee_tick += 1
        return True
        
    def move_up(self) -> bool:
        """Move cursor up. Returns True if selection changed or scrolled."""
        if self.screen_type.is_keyboard():
            if len(self.keyboard_modes) > 1:
                self.active_mode_index = (self.active_mode_index - 1) % len(self.keyboard_modes)
                self.char_index = 0
                return True
            return False

        changed = False
        if self.items and self.selected_index > 0:
            self.selected_index -= 1
            self.marquee_tick = 0
            self._adjust_scroll()
            changed = True
        elif self.scroll_offset > 0:
            self.scroll_offset -= 1
            changed = True
        return changed
        
    def move_down(self) -> bool:
        """Move cursor down. Returns True if selection changed or scrolled."""
        if self.screen_type.is_keyboard():
            if len(self.keyboard_modes) > 1:
                self.active_mode_index = (self.active_mode_index + 1) % len(self.keyboard_modes)
                self.char_index = 0
                return True
            return False

        changed = False
        if self.items and self.selected_index < len(self.items) - 1:
            self.selected_index += 1
            self.marquee_tick = 0
            self._adjust_scroll()
            changed = True
        elif self.scroll_offset < self.max_scroll_offset:
            self.scroll_offset += 1
            changed = True
        return changed

    def move_left(self) -> bool:
        """Move cursor left. For keyboard, cycles chars left. For lists, pages up."""
        if self.screen_type.is_keyboard():
            _, chars = self.keyboard_modes[self.active_mode_index]
            self.char_index = (self.char_index - 1) % len(chars)
            return True
        return self.page_up()

    def move_right(self) -> bool:
        """Move cursor right. For keyboard, cycles chars right. For lists, pages down."""
        if self.screen_type.is_keyboard():
            _, chars = self.keyboard_modes[self.active_mode_index]
            self.char_index = (self.char_index + 1) % len(chars)
            return True
        return self.page_down()

    def page_up(self) -> bool:
        """Move cursor up by visible_rows. Used for LEFT/RIGHT keys acting as page up/down on char LCDs."""
        if not self.items or self.selected_index <= 0:
            return False
            
        self.selected_index = max(0, self.selected_index - self.visible_rows)
        self.marquee_tick = 0
        self._adjust_scroll()
        return True
        
    def page_down(self) -> bool:
        """Move cursor down by visible_rows."""
        if not self.items or self.selected_index >= len(self.items) - 1:
            return False
            
        self.selected_index = min(len(self.items) - 1, self.selected_index + self.visible_rows)
        self.marquee_tick = 0
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

    def on_enter(self) -> str:
        """Handle ENTER key. Returns 'SUBMIT' if finished, 'UPDATE' if text changed, or 'SELECT'."""
        if self.screen_type.is_keyboard():
            _, chars = self.keyboard_modes[self.active_mode_index]
            char = chars[self.char_index]
            if char == "[DEL]":
                self.entered_text = self.entered_text[:-1]
                return "UPDATE"
            elif char == "[OK]":
                return "SUBMIT"
            else:
                self.entered_text += char
                return "UPDATE"
        return "SELECT"
