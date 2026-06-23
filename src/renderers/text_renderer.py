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
            lines = self._pad_rows([
                self._center(""),
                self._center("SeedSigner"),
            ][:self.rows])
        else:
            lines = self._pad_rows([self._center("Unsupported")])
            
        toast_msg = state.context.get("toast")
        if toast_msg:
            toast_text = f"[{toast_msg}]"
            if len(toast_text) > self.cols:
                toast_text = f"[{toast_msg[:self.cols-3]}..]"
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

        if self.item_rows == 1:
            # ── Block Pagination (16x2) ─────────────────────────────
            return self._render_block_pagination(state, title_line)
        else:
            # ── Sliding Window (20x4) ───────────────────────────────
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
        return [title_line, item_line]

    def _render_sliding_window(self, state: ScreenState, title_line: str) -> List[str]:
        """20x4 mode: rows 1..N form a sliding window over the item list."""
        lines = [title_line]

        if not state.items:
            return self._pad_rows(lines)

        start = state.scroll_offset
        end = min(len(state.items), start + self.item_rows)

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

        if self.item_rows == 1:
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
        
        if self.item_rows == 1:
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
                
        else:
            # 20x4 Display
            # Row 0: Title
            # Row 1: Keyboard (for[c]defghij)
            # Row 2-3: Suggestions
            lines = [title_line, kb_line]
            
            if not suggestions:
                lines.append(self._fixed("  (no match)"))
                return self._pad_rows(lines)
                
            start = state.scroll_offset
            # We have (self.rows - 2) lines left for suggestions
            avail_rows = self.rows - 2
            end = min(len(suggestions), start + avail_rows)
            
            for i in range(start, end):
                sugg = suggestions[i]
                prefix = "> " if i == state.selected_index else "  "
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
                # Toggle every 2 ticks (approx 600ms)
                edge_char = "!" if (state.marquee_tick // 2) % 2 == 0 else " "
            else:
                edge_char = "!"
        else:
            edge_char = " "

        content_lines = [title_line]

        headline = state.context.get("status_headline", "")
        if headline:
            headline_text = f"{icon} {headline}"
            wrap_cols = self.cols - 2 if warning_edges else self.cols
            words = headline_text.split()
            wrapped_headline = []
            current = ""
            for word in words:
                if current and len(current) + 1 + len(word) > wrap_cols:
                    wrapped_headline.append(current.center(wrap_cols))
                    current = word
                elif not current:
                    current = word
                else:
                    current += " " + word
            if current:
                wrapped_headline.append(current.center(wrap_cols))
                
            for line in wrapped_headline:
                if warning_edges:
                    content_lines.append(f"{edge_char}{line}{edge_char}")
                else:
                    content_lines.append(self._center(line))

        text = state.context.get("text", "")
        if text:
            # Word-wrap text into available rows
            # Reserve space for edge chars if warning_edges is True
            wrap_cols = self.cols - 2 if warning_edges else self.cols
            words = text.split()
            wrapped_lines = []
            current = ""
            for word in words:
                if current and len(current) + 1 + len(word) > wrap_cols:
                    wrapped_lines.append(current.center(wrap_cols))
                    current = word
                elif not current:
                    current = word
                else:
                    current += " " + word
            if current:
                wrapped_lines.append(current.center(wrap_cols))
            
            for line in wrapped_lines:
                if warning_edges:
                    content_lines.append(f"{edge_char}{line}{edge_char}")
                else:
                    content_lines.append(self._center(line))

        # Determine available lines for content
        # We always reserve 1 line for the button if state.items exists
        button_space = 1 if state.items else 0
        window_height = self.rows - button_space
        
        # Tell state how far it can scroll without shrinking previous renderer constraints
        new_max = max(0, len(content_lines) - window_height)
        state.max_scroll_offset = max(getattr(state, 'max_scroll_offset', 0), new_max)
        
        # Clamp the start index so we don't scroll past the end on larger displays
        start = min(state.scroll_offset, new_max)
        
        # Slice the content based on clamped scroll_offset
        lines = content_lines[start : start + window_height]

        if state.items:
            item = state.items[state.selected_index]
            label = item.get("label", "")
            button_line = self._center(f"[ {label} ]")
            
            # Pad content if it doesn't fill the window
            while len(lines) < window_height:
                lines.append(" " * self.cols)
                
            lines.append(button_line)

        return self._pad_rows(lines)

    # ── helpers ─────────────────────────────────────────────────────

    def _title_row(self, title: str, suffix: str, state: ScreenState = None) -> str:
        """Build a title row: title left-aligned, suffix right-aligned. Marquee if too long."""
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
        lines = []
        
        # Center "SEEDSIGNER" on the first available row
        if self.rows > 2:
            lines.append(self._center(""))
        lines.append(self._center("SEEDSIGNER"))
        
        version = state.context.get("version", "")
        show_partners = state.context.get("show_partner_logos", False)
        sponsor_text = state.context.get("sponsor_text", "")
        boot_logo_only = state.context.get("boot_logo_only", False)
        
        # Build the bottom line string
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
            
        # Marquee logic if bottom_text exceeds columns
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
            lines.append(self._fixed(visible))
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
