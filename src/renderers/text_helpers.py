from typing import List
from src.screen_state import ScreenState, ScreenType

class TextHelpersMixin:
    def _determine_tier(self) -> int:
        if self.rows <= 2:
            return 0  # Minimal: 16x2
        elif self.rows <= 4:
            return 1  # Compact: 20x4, 16x4
        elif self.rows <= 8:
            return 2  # Comfortable: 128x64 OLED
        else:
            return 3  # Spacious: E-Paper, Nokia 5110

    # ── public API ──────────────────────────────────────────────────

    def _center(self, text: str) -> str:
        if len(text) > self.cols:
            text = text[: self.cols - 2] + ".."
        return text.center(self.cols)

    def _fixed(self, text: str) -> str:
        """Pad or truncate `text` to exactly `self.cols` characters."""
        if len(text) > self.cols:
            return text[: self.cols]
        return f"{text:<{self.cols}}"

    def _highlight_address(self, address: str) -> str:
        """Generic address formatter."""
        if not address:
            return ""
        if len(address) > 16:
            return " ".join([address[i:i+4] for i in range(0, len(address), 4)])
        return address

    def _highlight_address_verify(self, address: str) -> str:
        """Truncate the middle of the address to match LVGL Verify Address layout."""
        if not address:
            return ""
        if address.startswith("bc1") or address.startswith("tb1") or address.startswith("bcrt1"):
            sep = address.rfind("1") + 2
            prefix = address[:sep]
            rest = address[sep:]
            if len(rest) > 14:
                middle = rest[7:-7]
                if len(middle) > 13:
                    middle = middle[:13] + "..."
                return f"{prefix} [{rest[:7]}] {middle} [{rest[-7:]}]"
        else:
            if len(address) > 15:
                middle = address[8:-7]
                if len(middle) > 13:
                    middle = middle[:13] + "..."
                return f"[{address[:8]}] {middle} [{address[-7:]}]"
        return address

    def _highlight_address_success(self, address: str) -> str:
        """Heavily truncate the address to match LVGL Success Screen layout."""
        if not address:
            return ""
        if address.startswith("bc1") or address.startswith("tb1") or address.startswith("bcrt1"):
            sep = address.rfind("1") + 2
            prefix = address[:sep]
            rest = address[sep:]
            if len(rest) > 10:
                return f"{prefix} [{rest[:7]}]...[{rest[-3:]}]"
        else:
            if len(address) > 11:
                return f"[{address[:8]}]...[{address[-3:]}]"
        return address

    def _pad_rows(self, lines: List[str]) -> List[str]:
        """Ensure we return exactly `self.rows` lines, each `self.cols` wide."""
        while len(lines) < self.rows:
            lines.append(" " * self.cols)
        return lines[: self.rows]

    def _word_wrap(self, text: str) -> List[str]:
        """Simple greedy word-wrap into rows of `self.cols` width, breaking long words if needed."""
        words = text.split()
        lines: List[str] = []
        current = ""
        for word in words:
            if not current:
                if len(word) > self.cols:
                    # Break long word
                    while len(word) > self.cols:
                        lines.append(word[:self.cols])
                        word = word[self.cols:]
                    current = word
                else:
                    current = word
            elif len(current) + 1 + len(word) > self.cols:
                lines.append(current)
                if len(word) > self.cols:
                    # Break long word
                    while len(word) > self.cols:
                        lines.append(word[:self.cols])
                        word = word[self.cols:]
                    current = word
                else:
                    current = word
            else:
                current += " " + word
        if current:
            lines.append(current)
        return lines
    def _pad_text_above_buttons(self, text_lines: List[str], num_buttons: int) -> List[str]:
        """Pads text lines vertically so they are centered in the space above buttons."""
        total_lines = len(text_lines) + num_buttons
        if total_lines < self.rows - 1:
            space_above = self.rows - 1 - num_buttons
            padding_top = (space_above - len(text_lines)) // 2
            padding_bottom = space_above - len(text_lines) - padding_top
            
            return [self._center("")] * padding_top + text_lines + [self._center("")] * padding_bottom
        return text_lines

    # ── seed_finalize_screen ────────────────────────────────────────

    def _title_row(self, title: str, suffix: str, state: ScreenState = None) -> str:
        """Build a title row: title left-aligned, suffix right-aligned. Marquee if too long."""
        import re
        if self.tier >= 2 and re.match(r'^\s*\d+/\d+$', suffix):
            suffix = ""

        if state:
            top_nav = state.context.get("top_nav", {})
            icon = top_nav.get("icon")
            if icon:
                icon_map = {
                    "\uf030": "O ",     # CAMERA
                    "\uf522": ":: ",    # DICE
                    "\ue91a": "@ ",     # FINGERPRINT
                    "\uf11c": "⌨ ",     # KEYBOARD
                    "\ue90f": "+ ",     # PLUS
                    "\ue920": "▦ ",     # QRCODE
                    "\ue90a": " >",     # CHEVRON_RIGHT
                    "": "✓ ",      # APPROVE / CHECK
                    "": "✗ ",      # CANCEL / CROSS
                }
                if icon in icon_map:
                    title = f"{icon_map[icon]}{title}"
            
            if self.tier >= 2 and top_nav.get("show_back_button", False):
                title = f"[<] {title}"
            
            
        avail = self.cols - len(suffix)
        if len(title) > avail:
            if state is not None:
                diff = len(title) - avail
                total_frames = diff + 10
                # Move 1 character every 3 ticks
                frame = (state.marquee_tick // 3) % total_frames
                
                if frame < 5:
                    offset = 0
                elif frame >= 5 + diff:
                    offset = diff
                else:
                    offset = frame - 5
                    
                title_visible = title[offset : offset + avail]
                return self._fixed(f"{title_visible}{suffix}")
            else:
                title = title[: avail - 2] + ".."
        return self._fixed(f"{title:<{avail}}{suffix}")

    def _item_row(self, label: str, selected: bool, state: ScreenState = None, index: int = -1) -> str:
        """Build an item row with a `> ` or `  ` prefix, sliding horizontally if selected and too long."""
        if state and 0 <= index < len(state.items):
            item = state.items[index]
            if isinstance(item, dict):
                icon_map = {
                    "\uf030": "O ",     # CAMERA
                    "\uf522": ":: ",    # DICE
                    "\ue91a": "@ ",     # FINGERPRINT
                    "\uf11c": "⌨ ",     # KEYBOARD
                    "\ue90f": "+ ",     # PLUS
                    "\ue920": "▦ ",     # QRCODE
                    "\ue90a": " >",     # CHEVRON_RIGHT
                    "": "✓ ",      # APPROVE / CHECK
                    "": "✗ ",      # CANCEL / CROSS
                    "": "[+] ",    # SCAN
                    "": "▦ ",      # XPUB/GRID
                    "": "✎ ",      # SIGN/PEN
                }
                icon = item.get("icon")
                right_icon = item.get("right_icon")
                if icon in icon_map:
                    label = f"{icon_map[icon]}{label}"
                if right_icon in icon_map:
                    label = f"{label}{icon_map[right_icon]}"

        button_style = state.context.get("button_style", "default") if state else "default"
        is_centered = state.context.get("is_button_text_centered", True) if state else True
        
        if self.tier == 3 and button_style == "default":
            if selected:
                max_label = self.cols - 4
                if len(label) > max_label:
                    diff = len(label) - max_label
                    total_frames = diff + 10
                    frame = (state.marquee_tick if state else 0) % total_frames
                    if frame < 5: offset = 0
                    elif frame >= 5 + diff: offset = diff
                    else: offset = frame - 5
                    visible = label[offset : offset + max_label]
                    btn_text = f"[ {visible} ]"
                else:
                    btn_text = f"[ {label} ]"
                    
                if is_centered:
                    return self._center(btn_text)
                else:
                    return self._fixed(btn_text)
            else:
                if is_centered:
                    if len(label) > self.cols:
                        label = label[:self.cols-2] + ".."
                    return self._center(label)
                else:
                    max_label = self.cols - 2
                    if len(label) > max_label:
                        label = label[:max_label-2] + ".."
                    return self._fixed(f"  {label}")
                
        prefix = "> " if selected else "  "
        
        if state is not None:
            is_checked = index in state.checked_buttons
            if button_style == "checkbox":
                check_str = "[x]" if is_checked else "[ ]"
                prefix = f"{prefix}{check_str} "
            elif button_style == "checked_selection":
                check_str = "(●)" if is_checked else "( )"
                prefix = f"{prefix}{check_str} "
                
        max_label = self.cols - len(prefix)
        
        if len(label) > max_label:
            if selected and state is not None:
                # Marquee logic
                diff = len(label) - max_label
                # 5 ticks pause at start, diff ticks scrolling, 5 ticks pause at end
                total_frames = diff + 10
                frame = state.marquee_tick % total_frames
                
                if frame < 5:
                    offset = 0
                elif frame >= 5 + diff:
                    offset = diff
                else:
                    offset = frame - 5
                    
                visible = label[offset : offset + max_label]
                return f"{prefix}{visible}"
            else:
                label = label[: max_label - 2] + ".."
                
        return self._fixed(f"{prefix}{label}")

    def _do_sliding_window(self, state: ScreenState, title_line: str, all_content: List[str], num_text_lines: int) -> List[str]:
        lines = [title_line]
        if not all_content:
            return self._pad_rows(lines)

        max_scroll = max(0, len(all_content) - self.item_rows)
        
        if not hasattr(state, "tier_max_scroll"):
            state.tier_max_scroll = {}
        state.tier_max_scroll[self.tier] = max_scroll

        selected_idx = num_text_lines + state.selected_index
        
        if not hasattr(state, "tier_unified_scroll"):
            state.tier_unified_scroll = {}
            
        current_scroll = state.tier_unified_scroll.get(self.tier, 0)
        
        if not hasattr(state, f"_opened_{self.tier}"):
            setattr(state, f"_opened_{self.tier}", True)
            state.tier_unified_scroll[self.tier] = 0
            
        current_scroll = state.tier_unified_scroll.get(self.tier, 0)
        
        # Base sliding window calculation
        if selected_idx < current_scroll:
            current_scroll = selected_idx
        elif selected_idx >= current_scroll + self.item_rows:
            current_scroll = selected_idx - self.item_rows + 1

        # Calculate natural min scroll needed to keep selected item visible
        natural_min_scroll = selected_idx - self.item_rows + 1 if selected_idx >= self.item_rows else 0
        
        if not hasattr(state, "tier_text_intent"):
            state.tier_text_intent = {}

        # If the user hasn't moved yet, we want to stay at 0 to show the text!
        if not getattr(state, "_user_has_moved", False):
            if state.selected_index == 0 and natural_min_scroll > 0:
                # Initialize intent so the first 'down' scrolls sequentially
                state.tier_text_intent[self.tier] = -natural_min_scroll
                
                if state.screen_type == ScreenType.SEED_SIGN_MESSAGE_CONFIRM_MESSAGE:
                    # Auto-scroll vertically if the content doesn't fit on screen
                    # 6 ticks per frame (0.6s per line). Pause at top/bottom for 6 frames (3.6s)
                    total_frames = natural_min_scroll * 2 + 12
                    frame = (state.marquee_tick // 6) % total_frames
                    if frame < 6:
                        current_scroll = 0
                    elif frame < 6 + natural_min_scroll:
                        current_scroll = frame - 6
                    elif frame < 12 + natural_min_scroll:
                        current_scroll = natural_min_scroll
                    else:
                        current_scroll = natural_min_scroll - (frame - (12 + natural_min_scroll))
                else:
                    current_scroll = 0
            else:
                current_scroll = 0
        else:
            if self.tier not in state.tier_text_intent:
                state.tier_text_intent[self.tier] = 0
            
        # Apply manual text scroll intent if the user is scrolling text at the top button
        if state.selected_index == 0 and getattr(state, "_user_has_moved", False):
            intent = state.tier_text_intent.get(self.tier, 0)
            current_scroll += intent
            
            # Clamp locally, DO NOT mutate the global intent
            if current_scroll < 0:
                current_scroll = 0
            elif current_scroll > natural_min_scroll:
                current_scroll = natural_min_scroll

        # Track if this tier has hit the top for ScreenState to prevent runaway intent
        if not hasattr(state, "tier_at_top"):
            state.tier_at_top = {}
        state.tier_at_top[self.tier] = (current_scroll <= 0)

        current_scroll = min(current_scroll, max_scroll)
        state.tier_unified_scroll[self.tier] = current_scroll

        end = min(len(all_content), current_scroll + self.item_rows)
        lines.extend(all_content[current_scroll:end])

        return self._pad_rows(lines)

