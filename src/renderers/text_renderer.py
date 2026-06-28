"""
TextRenderer: Core text layout engine for character LCD displays.

Produces a List[str] of fixed-width rows that can be sent to any
character display (16x2, 20x4) or printed in a terminal simulator.

Two rendering strategies:
  - Block Pagination (16x2): Row 0 = title + position, Row 1 = current item only.
  - Sliding Window (20x4):   Row 0 = title + position, Rows 1-N = visible window.
"""

from typing import List
from src.screen_state import ScreenState, ScreenType


class TextRenderer:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        # Number of rows available for items (row 0 is always the title)
        self.item_rows = rows - 1
        self.tier = self._determine_tier()

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

    def render(self, state: ScreenState) -> List[str]:
        """Return exactly `self.rows` strings, each exactly `self.cols` chars wide."""
        if state.screen_type == ScreenType.BUTTON_LIST:
            lines = self._render_button_list(state)
        elif state.screen_type == ScreenType.MAIN_MENU:
            lines = self._render_main_menu(state)
        elif state.screen_type == ScreenType.LARGE_ICON_STATUS:
            lines = self._render_status(state)
        elif state.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
            lines = self._render_seed_mnemonic_entry(state)
        elif state.screen_type.is_keyboard():
            lines = self._render_keyboard(state)
        elif state.screen_type == ScreenType.SPLASH:
            lines = self._render_splash(state)
        elif state.screen_type == ScreenType.SCREENSAVER:
            lines = []
            padding_top = max(0, (self.rows - 1) // 2)
            for _ in range(padding_top):
                lines.append(self._center(""))
            lines.append(self._center("SeedSigner"))
            lines = self._pad_rows(lines[:self.rows])
        else:
            lines = self._pad_rows([self._center("Unsupported")])
            
        toast_msg = state.context.get("toast")
        if toast_msg:
            toast_msg = toast_msg.replace("\n", " ").strip()
            toast_text = f"[{toast_msg}]"
            if len(toast_text) > self.cols:
                toast_text = f"[{toast_msg[:self.cols-5]}...]"
            lines[-1] = self._center(toast_text)
            
        return lines

    # ── button_list_screen ──────────────────────────────────────────

    def _render_button_list(self, state: ScreenState) -> List[str]:
        total = len(state.items)
        title = state.context.get("top_nav", {}).get("title", "Menu")

        # Position indicator  e.g. " 2/10"
        if total > 0:
            pos = f" {state.selected_index + 1}/{total}"
        else:
            pos = ""

        title_line = self._title_row(title, pos, state)

        if self.tier == 0:
            # ── Block Pagination (16x2) ─────────────────────────────
            return self._render_block_pagination(state, title_line)
        else:
            # ── Sliding Window (20x4 and up) ───────────────────────────────
            return self._render_sliding_window(state, title_line)

    def _render_block_pagination(self, state: ScreenState, title_line: str) -> List[str]:
        """16x2 mode: show only the currently selected item on row 1."""
        if not state.items:
            return self._pad_rows([title_line])

        item = state.items[state.selected_index]
        label = item.get("label", "")
        value = item.get("value", "")

        # Show value alongside label if it differs (for tuple-style items)
        if value and value != label:
            display = f"{label}: {value}"
        else:
            display = label

        item_line = self._item_row(display, selected=True, state=state)
        
        lines = [title_line]
        text = state.context.get("text", "")
        if text:
            # For 16x2 we can't really fit text and button, but let's try to show the first line of text
            # if we are focused on it, otherwise just show the button. Actually 16x2 is too small.
            # But let's just append it. If it gets padded, it will be cropped.
            # But we can alternate between text and button if we wanted.
            pass # 16x2 is too small for extra text
            
        lines.append(item_line)
        return lines

    def _render_sliding_window(self, state: ScreenState, title_line: str) -> List[str]:
        """20x4 mode: rows 1..N form a sliding window over the item list."""
        lines = [title_line]

        text = state.context.get("text", "")
        extra_lines = []
        if text:
            for line in text.split('\n'):
                extra_lines.append(self._center(line[:self.cols]))
        
        lines.extend(extra_lines)

        if not state.items:
            return self._pad_rows(lines)

        available_item_rows = max(1, self.item_rows - len(extra_lines))
        start = state.scroll_offset
        end = min(len(state.items), start + available_item_rows)

        for i in range(start, end):
            item = state.items[i]
            label = item.get("label", "")
            value = item.get("value", "")

            if value and value != label:
                display = f"{label}: {value}"
            else:
                display = label

            selected = (i == state.selected_index)
            lines.append(self._item_row(display, selected=selected, state=state))

        return self._pad_rows(lines)

    # ── main_menu_screen ────────────────────────────────────────────

    def _render_main_menu(self, state: ScreenState) -> List[str]:
        """Render the 4-icon main menu with text-based icons."""
        total = len(state.items)
        pos = f" {state.selected_index + 1}/{total}" if total > 0 else ""
        title_line = self._title_row("SeedSigner", pos, state)

        icon_map = {
            "Scan": "▦",
            "Seeds": "⚿",
            "Tools": "⚒",
            "Settings": "⚙"
        }

        if self.tier == 0:
            # Block pagination — show only the selected item
            if not state.items:
                return self._pad_rows([title_line])
            item = state.items[state.selected_index]
            label = item.get("label", "")
            icon = icon_map.get(label, "[-]")
            entry = f"> {icon} {label}"
            return [title_line, self._fixed(entry)]
        else:
            # Sliding window
            lines = [title_line]
            start = state.scroll_offset
            end = min(total, start + self.item_rows)
            for i in range(start, end):
                item = state.items[i]
                label = item.get("label", "")
                prefix = ">" if i == state.selected_index else " "
                icon = icon_map.get(label, "[-]")
                entry = f"{prefix}{icon} {label}"
                lines.append(self._fixed(entry))
            return self._pad_rows(lines)

    # ── seed_mnemonic_entry_screen ──────────────────────────────────
    
    def _render_seed_mnemonic_entry(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Enter Word")
        entered = state.context.get("entered_text", "")
        suggestions = state.context.get("suggestions", [])
        total = len(suggestions)
        
        # Position indicator for the top right (e.g. " 1/12")
        pos = f" {state.selected_index + 1}/{total}" if total > 0 else ""
        
        # Row 0 MUST be the standard title row
        title_line = self._title_row(title, pos, state)
        
        # Build the keyboard string (e.g. "for[c]defgh...")
        alphabet = getattr(state, "alphabet", [])
        char_index = getattr(state, "char_index", 0)
        
        kb_str = entered
        if alphabet:
            avail = self.cols - len(entered)
            char = alphabet[char_index]
            focus = getattr(state, "focus", "keyboard")
            
            if self.tier >= 3:
                # Full grid, no need for sliding preview in input line
                kb_str = entered
            else:
                cursor_str = f"[{char}]" if focus == "keyboard" else f" {char} "
                if len(cursor_str) < avail:
                    trailing = ""
                    for i in range(1, avail - len(cursor_str) + 1):
                        idx = (char_index + i) % len(alphabet)
                        trailing += alphabet[idx]
                    cursor_str += trailing
                cursor_str = cursor_str[:avail]
                kb_str = f"{entered}{cursor_str}"
        else:
            kb_str = f"{entered}_"
            
        kb_line = self._fixed(kb_str)
        
        if self.tier == 0:
            # 16x2 Display
            # With only 1 content row, if we have suggestions we should show the active suggestion.
            # But the user still needs to see what they are typing. 
            # We will show the active suggestion, but prepend the entered text!
            if not suggestions:
                return [title_line, kb_line]
            else:
                sugg = suggestions[state.selected_index] if state.selected_index < total else ""
                focus = getattr(state, "focus", "keyboard")
                
                if focus == "keyboard":
                    combined = f"{entered}[{alphabet[char_index]}] {sugg}"
                else:
                    combined = f"{entered} {alphabet[char_index]}  >{sugg}"
                    
                if len(combined) > self.cols:
                    combined = combined[:self.cols]
                return [title_line, self._fixed(combined)]
                
        elif self.tier >= 3:
            lines = [title_line, kb_line]
            grid_lines = []
            current_line_items = []
            current_len = 0
            focus = getattr(state, "focus", "keyboard")
            
            for i, c in enumerate(alphabet):
                is_selected = (i == char_index and focus == "keyboard")
                if c.startswith("[") and c.endswith("]"):
                    display = c.replace("[", "<").replace("]", ">") if is_selected else c
                else:
                    display = f"[{c}]" if is_selected else f" {c} "
                    
                item_len = len(display)
                space_needed = item_len if current_len == 0 else item_len + 1
                
                if current_len + space_needed > self.cols:
                    line_str = " ".join(current_line_items)
                    grid_lines.append(self._center(line_str))
                    current_line_items = [display]
                    current_len = item_len
                else:
                    current_line_items.append(display)
                    current_len += space_needed
                    
            if current_line_items:
                line_str = " ".join(current_line_items)
                grid_lines.append(self._center(line_str))
                
            lines.extend(grid_lines)
            
            if not suggestions:
                lines.append(self._fixed("  (no match)"))
            else:
                avail_rows = self.rows - len(lines)
                start = state.scroll_offset
                end = min(len(suggestions), start + avail_rows)
                
                for i in range(start, end):
                    sugg = suggestions[i]
                    prefix = "> " if (i == state.selected_index and focus == "suggestions") else "  "
                    lines.append(self._fixed(f"{prefix}{sugg}"))
                    
            return self._pad_rows(lines)

        else:
            # 20x4 Display and 16x8 Display
            lines = [title_line, kb_line]
            
            if not suggestions:
                lines.append(self._fixed("  (no match)"))
                return self._pad_rows(lines)
                
            start = state.scroll_offset
            avail_rows = self.rows - 2
            end = min(len(suggestions), start + avail_rows)
            
            for i in range(start, end):
                sugg = suggestions[i]
                focus = getattr(state, "focus", "keyboard")
                prefix = "> " if (i == state.selected_index and focus == "suggestions") else "  "
                lines.append(self._fixed(f"{prefix}{sugg}"))
                
            return self._pad_rows(lines)

    # ── keyboard_screen ─────────────────────────────────────────────

    def _render_keyboard(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Input")
        
        # Append length counter if target is specified
        target = state.context.get("entropy_target")
        if target:
            title = f"{title} {len(state.entered_text)}/{target}"
            
        title_line = self._title_row(title, "", state)
        
        mode_name, chars = state.keyboard_modes[state.active_mode_index]
        char = chars[state.char_index]
        
        mask_input = state.context.get("mask_input", False)
        entered = state.entered_text
        if mask_input:
            entered = "*" * len(entered)
            
        cursor_str = f"[{char}]"
        input_str = f"{entered}{cursor_str}"
        
        if len(mode_name) > 0 and self.cols == 20:
            mode_indicator = f" ({mode_name})"
            available = self.cols - len(mode_indicator)
            if len(input_str) > available:
                input_str = ".." + input_str[-(available - 2):]
            input_line = input_str.ljust(available) + mode_indicator
        else:
            if len(input_str) > self.cols:
                input_str = ".." + input_str[-(self.cols - 2):]
            input_line = self._fixed(input_str)
            
        lines = [title_line, input_line]
        
        if self.tier >= 2:
            grid_lines = []
            current_line_items = []
            current_len = 0
            
            for i, c in enumerate(chars):
                is_selected = (i == state.char_index)
                
                if c.startswith("[") and c.endswith("]"):
                    display = c.replace("[", "<").replace("]", ">") if is_selected else c
                else:
                    display = f"[{c}]" if is_selected else f" {c} "
                    
                item_len = len(display)
                space_needed = item_len if current_len == 0 else item_len + 1
                
                if current_len + space_needed > self.cols:
                    line_str = " ".join(current_line_items)
                    grid_lines.append(self._center(line_str))
                    current_line_items = [display]
                    current_len = item_len
                else:
                    current_line_items.append(display)
                    current_len += space_needed
                    
            if current_line_items:
                line_str = " ".join(current_line_items)
                grid_lines.append(self._center(line_str))
                
            used_rows = 2 + len(grid_lines)
            padding = max(0, self.rows - used_rows)
            top_pad = padding // 2
            
            for _ in range(top_pad):
                lines.append(self._center(""))
                
            lines.extend(grid_lines)
            return self._pad_rows(lines)
            
        else:
            return self._pad_rows(lines)

    # ── large_icon_status_screen ────────────────────────────────────

    def _render_status(self, state: ScreenState) -> List[str]:
        """Render success / warning / error status screens."""
        status_type = state.context.get("status_type", "success")
        icon_map = {
            "success": "✓",
            "warning": "⚠",
            "dire_warning": "‼",
            "error": "✕"
        }
        icon = icon_map.get(status_type, " ")
        
        title = state.context.get("top_nav", {}).get("title", "Status")
        title_line = self._title_row(title, "", state)
        
        warning_edges = state.context.get("warning_edges", False)
        animated = state.context.get("animated", False)
        
        if warning_edges:
            if animated:
                edge_char = "!" if (state.marquee_tick // 2) % 2 == 0 else " "
            else:
                edge_char = "!"
        else:
            edge_char = " "

        content_lines = [title_line]
        wrap_cols = self.cols - 2 if warning_edges else self.cols
        import textwrap

        headline = state.context.get("status_headline", "")
        if headline:
            headline_text = f"{icon} {headline}"
            wrapped = textwrap.wrap(headline_text, width=wrap_cols)
            for line in wrapped:
                if warning_edges:
                    content_lines.append(f"{edge_char}{line.center(wrap_cols)}{edge_char}")
                else:
                    content_lines.append(self._center(line))

        text = state.context.get("text", "")
        if text:
            if headline and self.tier >= 2:
                # Add spacing between headline and text on larger screens
                if warning_edges:
                    content_lines.append(f"{edge_char}{' '*wrap_cols}{edge_char}")
                else:
                    content_lines.append(self._center(""))
                    
            wrapped = textwrap.wrap(text, width=wrap_cols)
            for line in wrapped:
                if warning_edges:
                    content_lines.append(f"{edge_char}{line.center(wrap_cols)}{edge_char}")
                else:
                    content_lines.append(self._center(line))

        # Determine available lines for content
        button_space = 1 if state.items else 0
        window_height = self.rows - button_space
        
        # Tell state how far it can scroll without shrinking previous renderer constraints
        new_max = max(0, len(content_lines) - window_height)
        state.max_scroll_offset = max(getattr(state, 'max_scroll_offset', 0), new_max)
        
        start = min(state.scroll_offset, new_max)
        lines = content_lines[start : start + window_height]

        if state.items:
            item = state.items[state.selected_index]
            label = item.get("label", "")
            button_line = self._center(f"[ {label} ]")
            
            while len(lines) < window_height:
                if warning_edges:
                    lines.append(f"{edge_char}{' '*wrap_cols}{edge_char}")
                else:
                    lines.append(" " * self.cols)
                
            lines.append(button_line)

        return self._pad_rows(lines)

    # ── helpers ─────────────────────────────────────────────────────

    def _title_row(self, title: str, suffix: str, state: ScreenState = None) -> str:
        """Build a title row: title left-aligned, suffix right-aligned. Marquee if too long."""
        if self.tier >= 2 and state and state.context.get("top_nav", {}).get("show_back_button", False):
            title = f"[<] {title}"
            
        avail = self.cols - len(suffix)
        if len(title) > avail:
            if state is not None:
                diff = len(title) - avail
                total_frames = diff + 10
                frame = state.marquee_tick % total_frames
                
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

    def _item_row(self, label: str, selected: bool, state: ScreenState = None) -> str:
        """Build an item row with a `> ` or `  ` prefix, sliding horizontally if selected and too long."""
        prefix = "> " if selected else "  "
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

    def _render_splash(self, state: ScreenState) -> List[str]:
        """Render the Splash Screen with versions and partners."""
        version = state.context.get("version", "")
        show_partners = state.context.get("show_partner_logos", False)
        sponsor_text = state.context.get("sponsor_text", "")
        boot_logo_only = state.context.get("boot_logo_only", False)
        
        if self.tier >= 2:
            lines = []
            total_content_rows = 2 if not version else 3
            if not boot_logo_only and show_partners and sponsor_text:
                total_content_rows += 4
                
            padding_top = max(0, (self.rows - total_content_rows) // 2)
            for _ in range(padding_top):
                lines.append(self._center(""))
                
            lines.append(self._center("SEEDSIGNER"))
            if version:
                lines.append(self._center(version))
                
            if not boot_logo_only and show_partners and sponsor_text:
                lines.append(self._center(""))
                lines.append(self._center(sponsor_text))
                lines.append(self._center("Human Rights Foundation"))
                
            return self._pad_rows(lines)
            
        else:
            lines = []
            if self.rows > 2:
                lines.append(self._center(""))
            lines.append(self._center("SEEDSIGNER"))
            
            bottom_text = ""
            if not boot_logo_only:
                if version:
                    bottom_text += version
                    
                if show_partners and sponsor_text:
                    if bottom_text:
                        bottom_text += " | "
                    bottom_text += f"{sponsor_text} Human Rights Foundation"
                
            if not bottom_text:
                return self._pad_rows(lines)
                
            if len(bottom_text) > self.cols:
                diff = len(bottom_text) - self.cols
                total_frames = diff + 10
                frame = state.marquee_tick % total_frames
                
                if frame < 5:
                    offset = 0
                elif frame >= 5 + diff:
                    offset = diff
                else:
                    offset = frame - 5
                    
                visible = bottom_text[offset : offset + self.cols]
                lines.append(self._center(visible))
            else:
                lines.append(self._center(bottom_text))
                
            return self._pad_rows(lines)

    def _center(self, text: str) -> str:
        if len(text) > self.cols:
            text = text[: self.cols - 2] + ".."
        return text.center(self.cols)

    def _fixed(self, text: str) -> str:
        """Pad or truncate `text` to exactly `self.cols` characters."""
        if len(text) > self.cols:
            return text[: self.cols]
        return f"{text:<{self.cols}}"

    def _pad_rows(self, lines: List[str]) -> List[str]:
        """Ensure we return exactly `self.rows` lines, each `self.cols` wide."""
        while len(lines) < self.rows:
            lines.append(" " * self.cols)
        return lines[: self.rows]

    def _word_wrap(self, text: str) -> List[str]:
        """Simple greedy word-wrap into rows of `self.cols` width."""
        words = text.split()
        lines: List[str] = []
        current = ""
        for word in words:
            if current and len(current) + 1 + len(word) > self.cols:
                lines.append(self._fixed(current))
                current = word
            elif not current:
                current = word
            else:
                current += " " + word
        if current:
            lines.append(self._fixed(current))
        return lines
