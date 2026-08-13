
try:
    typing = __import__('typing')
    Dict = typing.Dict
    Any = typing.Any
    List = typing.List
except ImportError:
    pass


class ScreenType:
    # ── Core screens (existing) ─────────────────────────────────────
    BUTTON_LIST = "button_list_screen"
    MAIN_MENU = "main_menu_screen"
    LARGE_ICON_STATUS = "large_icon_status_screen"
    SEED_ADD_PASSPHRASE = "seed_add_passphrase_screen"
    SPLASH = "opening_splash_screen"
    SCREENSAVER = "screensaver_screen"
    KEYBOARD = "keyboard_screen"
    SEED_MNEMONIC_ENTRY = "seed_mnemonic_entry_screen"
    SEED_FINALIZE = "seed_finalize_screen"
    LOADING = "loading_spinner_screen"
    LOCALE_PICKER = "settings_locale_picker_screen"
    PSBT_OVERVIEW = "psbt_overview_screen"
    PSBT_ADDRESS_DETAILS = "psbt_address_details_screen"
    PSBT_CHANGE_DETAILS = "psbt_change_details_screen"
    PSBT_MATH = "psbt_math_screen"

    # ── New text-renderable screens ─────────────────────────────────
    VERSION = "version_screen"
    TOAST_OVERLAY = "toast_overlay_screen"
    SEED_EXPORT_XPUB_DETAILS = "seed_export_xpub_details_screen"
    SEED_EXPORT_XPUB_CUSTOM_DERIVATION = "seed_export_xpub_custom_derivation_screen"
    SEED_REVIEW_PASSPHRASE = "seed_review_passphrase_screen"
    SEED_WORDS = "seed_words_screen"
    MULTISIG_WALLET_DESCRIPTOR = "multisig_wallet_descriptor_screen"
    SEED_SIGN_MESSAGE_CONFIRM_ADDRESS = "seed_sign_message_confirm_address_screen"
    SEED_SIGN_MESSAGE_CONFIRM_MESSAGE = "seed_sign_message_confirm_message_screen"
    SEED_ADDRESS_VERIFICATION = "seed_address_verification_screen"
    SEED_ADDRESS_VERIFICATION_SUCCESS = "seed_address_verification_success_screen"
    TOOLS_CALC_FINAL_WORD = "tools_calc_final_word_screen"
    TOOLS_CALC_FINAL_WORD_DONE = "tools_calc_final_word_done_screen"
    TOOLS_ADDRESS_EXPLORER_ADDRESS_LIST = "tools_address_explorer_address_list_screen"
    TOOLS_ADDRESS_EXPLORER_ADDRESS_TYPE = "tools_address_explorer_address_type_screen"
    POWER_OPTIONS = "power_options_screen"
    RESET = "reset_screen"
    POWER_OFF_NOT_REQUIRED = "power_off_not_required_screen"
    DONATE = "donate_screen"
    PSBT_OP_RETURN = "psbt_op_return_screen"

    # ── Visual-only screens (no text-UI equivalent) ─────────────────
    CAMERA_PREVIEW_PILLARBOXED = "camera_preview_pillarboxed_screen"
    CAMERA_PREVIEW_OVERLAY = "camera_preview_overlay_screen"
    CAMERA_ENTROPY_OVERLAY = "camera_entropy_overlay_screen"
    QR_DISPLAY = "qr_display_screen"
    SEED_TRANSCRIBE_ZOOMED_QR = "seed_transcribe_zoomed_qr_screen"
    SEED_TRANSCRIBE_WHOLE_QR = "seed_transcribe_whole_qr_screen"
    IO_TEST = "io_test_screen"

    # ── Screens with dedicated text renderers (not visual-only) ────
    SEED_TRANSCRIBE_SEEDQR_FORMAT = "seed_transcribe_seedqr_format_screen"
    SETTINGS_QR_CONFIRMATION = "settings_qr_confirmation_screen"

    @classmethod
    def is_keyboard(cls, val):
        return val in [
            cls.SEED_ADD_PASSPHRASE,
            cls.KEYBOARD,
            cls.SEED_MNEMONIC_ENTRY,
        ]

    @classmethod
    def is_visual_only(cls, val):
        return val in [
            cls.CAMERA_PREVIEW_PILLARBOXED,
            cls.CAMERA_PREVIEW_OVERLAY,
            cls.CAMERA_ENTROPY_OVERLAY,
            cls.QR_DISPLAY,
            cls.SEED_TRANSCRIBE_ZOOMED_QR,
            cls.SEED_TRANSCRIBE_WHOLE_QR,
            cls.IO_TEST,
        ]


class ScreenState:
    _bip39_wordlist = None

    def __init__(self, screen_type_str: str, context: dict, visible_rows: int = 1):
        self.screen_type = screen_type_str
        self.context = context
        self.state_id = str(id(self))
        self.visible_rows = visible_rows
        
        self.selected_index = 0
        self.scroll_offset = 0
        self.marquee_tick = 0
        
        self.selected_index = self.context.get("initial_selected_index", 0)
        self.checked_buttons = self.context.get("checked_buttons", [])
        
        self.entered_text = self.context.get("initial_text", "")
        self.keyboard_modes = []
        self.active_mode_index = 0
        self.char_index = 0
        self.keyboard_cols = 0
        
        if self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
            self._init_mnemonic_entry()
        elif ScreenType.is_keyboard(self.screen_type):
            self._init_keyboard()
        
        self.items = self._extract_items()
        
        if self.selected_index > 0:
            self._adjust_scroll()

    @property
    def max_scroll_offset(self) -> int:
        tier_scrolls = getattr(self, "tier_max_scroll", {})
        if not tier_scrolls:
            return 0
            
        active_tier = getattr(self, "active_tier_mode", -1)
        if active_tier != -1 and active_tier in tier_scrolls:
            return tier_scrolls[active_tier]
            
        return max(tier_scrolls.values())
        
    def _init_keyboard(self):
        if self.screen_type == ScreenType.KEYBOARD:
            keys = list(self.context.get("keys", []))
            
            # Map PUA FontAwesome icons to text for constrained UI
            pua_map = {
                "\uf525": "1", # Dice 1
                "\uf528": "2", # Dice 2
                "\uf527": "3", # Dice 3
                "\uf524": "4", # Dice 4
                "\uf526": "5", # Dice 5
                "\uf523": "6"  # Dice 6
            }
            keys = [pua_map.get(k, k) for k in keys]
            
            if self.context.get("show_save_button", False):
                keys.extend(["[DEL]", "[OK]"])
            else:
                keys.append("[DEL]")
            
            self.keyboard_modes = [("default", keys)]
            self.active_mode_index = 0
            self.entered_text = self.context.get("initial_value", "")
        else:
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

    def _init_mnemonic_entry(self):
        if ScreenState._bip39_wordlist is None:
            import os
            wordlist_path = __file__.rsplit("/", 1)[0] + "/data/bip39_english.txt"
            wordlist_exists = False
            try:
                os.stat(wordlist_path)
                wordlist_exists = True
            except OSError:
                pass
            if wordlist_exists:
                with open(wordlist_path, "r") as f:
                    ScreenState._bip39_wordlist = [line.strip() for line in f if line.strip() and not line.startswith("Source:") and not line.startswith("---")]
            else:
                ScreenState._bip39_wordlist = []
                
        initial = self.context.get("initial_letters", self.context.get("entered_text", ""))
        if isinstance(initial, list):
            self.entered_text = "".join(initial)
        else:
            self.entered_text = str(initial)
            
        self.context["entered_text"] = self.entered_text
        self.alphabet = list("abcdefghijklmnopqrstuvwxyz") + ["[DEL]", "[OK]"]
        self.char_index = 0
        self._update_mnemonic_suggestions()
        
        initial_selected = self.context.get("initial_selected_word")
        if initial_selected and initial_selected in self.context.get("suggestions", []):
            self.selected_index = self.context["suggestions"].index(initial_selected)

    def _update_mnemonic_suggestions(self):
        wordlist = self.context.get("wordlist", ScreenState._bip39_wordlist)
        if not self.entered_text:
            self.context["suggestions"] = []
            self.valid_next_chars = set("abcdefghijklmnopqrstuvwxyz")
        else:
            self.context["suggestions"] = [w for w in wordlist if w.startswith(self.entered_text)]
            self.valid_next_chars = set()
            for w in self.context["suggestions"]:
                if len(w) > len(self.entered_text):
                    self.valid_next_chars.add(w[len(self.entered_text)])
        self.selected_index = 0
        
    def is_key_enabled(self, key: str) -> bool:
        if self.screen_type != ScreenType.SEED_MNEMONIC_ENTRY:
            return True
        if getattr(self, "valid_next_chars", None) is None:
            return True
        if key in ["[DEL]", "[OK]"]:
            return True
        return key in self.valid_next_chars
        
    def _normalize_items(self, items: List[Any]) -> List[Any]:
        """Normalize item list: plain strings become {label: str, value: str}."""
        normalized = []
        for item in items:
            if isinstance(item, str):
                normalized.append({"label": item, "value": item})
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                normalized.append({"label": str(item[0]), "value": item[1]})
            elif isinstance(item, dict):
                if "label" not in item:
                    item["label"] = item.get("text", "")
                if "value" not in item:
                    item["value"] = item["label"]
                normalized.append(item)
            else:
                normalized.append({"label": str(item), "value": str(item)})
        return normalized

    def _extract_items(self) -> List[Any]:
        if "items" in self.context:
            return self._normalize_items(self.context["items"])
        if "button_list" in self.context:
            return self._normalize_items(self.context["button_list"])
        if "button_grid" in self.context:
            return self._normalize_items(self.context["button_grid"])
        if "button_data" in self.context:
            return self._normalize_items(self.context["button_data"])
        if "rows" in self.context:
            return self._normalize_items(self.context["rows"])
        if "button" in self.context:
            return [{"label": self.context["button"]}]
        if "background" in self.context and isinstance(self.context["background"], dict):
            bg = self.context["background"]
            if "button_list" in bg:
                return self._normalize_items(bg["button_list"])
        if "addresses" in self.context:
            items = []
            start_idx = self.context.get("start_index", 0)
            for i, addr in enumerate(self.context["addresses"]):
                items.append({"label": f"{start_idx + i}:{addr}", "value": addr})
            if "next_label" in self.context:
                items.append({"label": self.context["next_label"], "value": "next"})
            return items
        return []
        
    def tick(self) -> bool:
        """Increment marquee tick. Returns True to indicate screen needs render."""
        self.marquee_tick += 1
        return True
        
    def move_up(self) -> bool:
        """Move cursor up. Returns True if selection changed or scrolled."""
        if self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
            self.focus = getattr(self, "focus", "keyboard")
            if self.focus == "keyboard":
                self.focus = "suggestions"
                return True
                
            suggestions = self.context.get("suggestions", [])
            if suggestions and self.selected_index > 0:
                self.selected_index -= 1
                self._adjust_scroll()
                return True
            elif self.scroll_offset > 0:
                self.scroll_offset -= 1
                return True
            else:
                self.focus = "keyboard"
                return True
                
        if ScreenType.is_keyboard(self.screen_type):
            if self.visible_rows < 7:
                return False
                
            grids = getattr(self, "keyboard_grid_layouts", {})
            active_tier = 3 if self.visible_rows > 7 else 2
            grid = grids.get(active_tier, grids.get(3, grids.get(2)))
            
            if grid:
                curr_r, curr_c = 0, 0
                for r, row in enumerate(grid):
                    if self.char_index in row:
                        curr_r, curr_c = r, row.index(self.char_index)
                        break
                new_r = max(0, curr_r - 1)
                new_c = min(curr_c, len(grid[new_r]) - 1)
                self.char_index = grid[new_r][new_c]
                return True
            elif len(self.keyboard_modes) > 1:
                self.active_mode_index = (self.active_mode_index - 1) % len(self.keyboard_modes)
                self.char_index = 0
                return True
            return False

        self._user_has_moved = True
        changed = False
        if self.items and self.selected_index > 0:
            self.selected_index -= 1
            self.marquee_tick = 0
            self._adjust_scroll()
            changed = True
        elif getattr(self, "items", None) is not None and self.selected_index == 0:
            # Only allow scrolling up if at least one tier is not at the top
            active_tier = getattr(self, "active_tier_mode", -1)
            can_scroll = False
            for tier, at_top in getattr(self, "tier_at_top", {}).items():
                if active_tier != -1 and tier != active_tier:
                    continue
                if not at_top:
                    can_scroll = True
            
            if can_scroll or not hasattr(self, "tier_at_top"):
                if hasattr(self, "tier_text_intent"):
                    for tier in self.tier_text_intent:
                        if active_tier != -1 and tier != active_tier:
                            continue
                        self.tier_text_intent[tier] -= 1
                changed = True
        elif not self.items and self.scroll_offset > 0:
            self.scroll_offset -= 1
            changed = True
        return changed
        
    def move_down(self) -> bool:
        """Move cursor down. Returns True if UI needs re-render."""
        if self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
            self.focus = getattr(self, "focus", "keyboard")
            if self.focus == "keyboard":
                self.focus = "suggestions"
                return True
                
            suggestions = self.context.get("suggestions", [])
            if suggestions and self.selected_index < len(suggestions) - 1:
                self.selected_index += 1
                self._adjust_scroll()
                return True
            elif self.scroll_offset < self.max_scroll_offset:
                self.scroll_offset += 1
                return True
            return False
            
        if ScreenType.is_keyboard(self.screen_type):
            if self.visible_rows < 7:
                return False
                
            grids = getattr(self, "keyboard_grid_layouts", {})
            active_tier = 3 if self.visible_rows > 7 else 2
            grid = grids.get(active_tier, grids.get(3, grids.get(2)))
            
            if grid:
                curr_r, curr_c = 0, 0
                for r, row in enumerate(grid):
                    if self.char_index in row:
                        curr_r, curr_c = r, row.index(self.char_index)
                        break
                new_r = min(len(grid) - 1, curr_r + 1)
                new_c = min(curr_c, len(grid[new_r]) - 1)
                self.char_index = grid[new_r][new_c]
                return True
            elif len(self.keyboard_modes) > 1:
                self.active_mode_index = (self.active_mode_index + 1) % len(self.keyboard_modes)
                self.char_index = 0
                return True
            return False

        self._user_has_moved = True
        changed = False
        
        if hasattr(self, "tier_text_intent"):
            active_tier = getattr(self, "active_tier_mode", -1)
            can_scroll_down = False
            for tier, intent in self.tier_text_intent.items():
                if active_tier != -1 and tier != active_tier:
                    continue
                if intent < 0:
                    self.tier_text_intent[tier] += 1
                    can_scroll_down = True
            if can_scroll_down:
                return True
                
        if self.items and self.selected_index < len(self.items) - 1:
            self.selected_index += 1
            self.marquee_tick = 0
            self._adjust_scroll()
            changed = True
        elif not self.items and self.scroll_offset < getattr(self, "max_scroll_offset", 0):
            self.scroll_offset += 1
            changed = True
                
        return changed

    def move_left(self) -> bool:
        """Move cursor left. For keyboard, cycles chars left. For lists, pages up."""
        if ScreenType.is_keyboard(self.screen_type) or self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
            if getattr(self, "focus", "keyboard") == "keyboard":
                chars = getattr(self, "keyboard_chars", None)
                if not chars:
                    if self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
                        chars = self.alphabet
                    else:
                        _, chars = self.keyboard_modes[self.active_mode_index]
                for _ in range(len(chars)):
                    self.char_index = (self.char_index - 1) % len(chars)
                    if self.is_key_enabled(chars[self.char_index]):
                        break
                return True
            else:
                self.focus = "keyboard"
                return True
        return self.page_up()

    def move_right(self) -> bool:
        """Move cursor right. For keyboard, cycles chars right. For lists, pages down."""
        if ScreenType.is_keyboard(self.screen_type) or self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
            if getattr(self, "focus", "keyboard") == "keyboard":
                chars = getattr(self, "keyboard_chars", None)
                if not chars:
                    if self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
                        chars = self.alphabet
                    else:
                        _, chars = self.keyboard_modes[self.active_mode_index]
                for _ in range(len(chars)):
                    self.char_index = (self.char_index + 1) % len(chars)
                    if self.is_key_enabled(chars[self.char_index]):
                        break
                return True
            else:
                self.focus = "keyboard"
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
            
        prioritize_scroll = getattr(self, "prioritize_scroll", False)
        if prioritize_scroll:
            if hasattr(self, "max_scroll_offset"):
                self.scroll_offset = min(self.scroll_offset, self.max_scroll_offset)
            return
            
        if self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
            items = self.context.get("suggestions", [])
            # Mnemonic entry uses an extra row for the keyboard input line
            effective_visible_rows = max(1, self.visible_rows - 1)
        else:
            items = getattr(self, "items", None)
            effective_visible_rows = self.visible_rows
            
        if not items:
            return

        if self.selected_index < self.scroll_offset:
            # Scroll up to reveal the item
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + effective_visible_rows:
            # Scroll down to reveal the item
            self.scroll_offset = self.selected_index - effective_visible_rows + 1

    def _update_dynamic_title(self):
        """Dynamically update titles like 'Dice Roll 1/50' based on entered_text length."""
        top_nav = self.context.get("top_nav")
        if not top_nav: return
        title = top_nav.get("title", "")
        
        import re
        if "/" in title and re.search(r'\d+/\d+', title):
            new_count = len(self.entered_text) + 1
            new_title = re.sub(r'\d+(/\d+)', rf'{new_count}\1', title)
            top_nav["title"] = new_title

    def on_enter(self) -> str:
        """Handle ENTER key. Returns 'SUBMIT' if finished, 'UPDATE' if text changed, or 'SELECT'."""
        focus = getattr(self, "focus", "keyboard")
        
        # 1. Handle List / Suggestions Selection
        if focus == "list" or focus == "suggestions":
            if self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
                suggestions = self.context.get("suggestions", [])
                if suggestions and self.selected_index < len(suggestions):
                    self.entered_text = suggestions[self.selected_index]
                    self.context["entered_text"] = self.entered_text
                return "SUBMIT"
            else:
                return "SELECT"
                
        # 2. Handle Keyboard Selection
        if ScreenType.is_keyboard(self.screen_type):
            chars = getattr(self, "keyboard_chars", None)
            if not chars:
                if self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
                    chars = self.alphabet
                else:
                    _, chars = self.keyboard_modes[self.active_mode_index]
            
            char = chars[self.char_index]
            if char == "[DEL]":
                self.entered_text = self.entered_text[:-1]
                self._update_dynamic_title()
                if self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
                    self._update_mnemonic_suggestions()
                    self.context["entered_text"] = self.entered_text
                return "UPDATE"
            elif char == "[OK]":
                return "SUBMIT"
            elif char.startswith("[") and char.endswith("]") and char != "[ ]":
                # Mode toggle!
                for i, (name, _) in enumerate(self.keyboard_modes):
                    if f"[{name}]" == char:
                        self.active_mode_index = i
                        self.char_index = 0
                        return "UPDATE"
                self.active_mode_index = (self.active_mode_index + 1) % len(self.keyboard_modes)
                self.char_index = 0
                return "UPDATE"
            else:
                if char == "[ ]":
                    char = " "
                self.entered_text += char
                self._update_dynamic_title()
                if self.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
                    self._update_mnemonic_suggestions()
                    self.context["entered_text"] = self.entered_text
                
                # Auto-submit if we hit the requested character limit (e.g. for Dice Rolls)
                limit = self.context.get("return_after_n_chars")
                if limit and len(self.entered_text) >= limit:
                    return "SUBMIT"
                    
                return "UPDATE"
                
        return "SELECT"
