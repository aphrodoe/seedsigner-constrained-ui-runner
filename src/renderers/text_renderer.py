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
            return self._render_button_list(state)
        elif state.screen_type == ScreenType.MAIN_MENU:
            return self._render_main_menu(state)
        elif state.screen_type == ScreenType.LARGE_ICON_STATUS:
            return self._render_status(state)
        elif state.screen_type.is_keyboard():
            return self._render_keyboard(state)
        elif state.screen_type == ScreenType.SPLASH:
            return self._pad_rows([
                self._center(""),
                self._center("SEEDSIGNER"),
            ][:self.rows])
        elif state.screen_type == ScreenType.SCREENSAVER:
            return self._pad_rows([
                self._center(""),
                self._center("..."),
            ][:self.rows])
        else:
            return self._pad_rows([self._center("Unsupported")])

    # ── button_list_screen ──────────────────────────────────────────

    def _render_button_list(self, state: ScreenState) -> List[str]:
        total = len(state.items)
        title = state.context.get("top_nav", {}).get("title", "Menu")

        # Position indicator  e.g. " 2/10"
        if total > 0:
            pos = f" {state.selected_index + 1}/{total}"
        else:
            pos = ""

        title_line = self._title_row(title, pos)

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
        """Render the 4-icon main menu as a numbered list, with pagination."""
        total = len(state.items)
        pos = f" {state.selected_index + 1}/{total}" if total > 0 else ""
        title_line = self._title_row("SeedSigner", pos)

        if self.item_rows == 1:
            # Block pagination — show only the selected item
            if not state.items:
                return self._pad_rows([title_line])
            item = state.items[state.selected_index]
            label = item.get("label", "")
            prefix = ">" if state.selected_index == state.selected_index else " "
            entry = f"> {state.selected_index + 1}.{label}"
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
                entry = f"{prefix}{i + 1}.{label}"
                lines.append(self._fixed(entry))
            return self._pad_rows(lines)

    # ── keyboard_screen ─────────────────────────────────────────────

    def _render_keyboard(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Input")
        title_line = self._title_row(title, "")
        
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
        title_line = self._title_row(title, "")
        
        warning_edges = state.context.get("warning_edges", False)
        edge_char = "!" if warning_edges else " "

        content_lines = [title_line]

        headline = state.context.get("status_headline", "")
        if headline:
            headline_text = f"{icon} {headline}"
            if len(headline_text) > self.cols:
                words = headline_text.split()
                wrapped_headline = []
                current = ""
                for word in words:
                    if current and len(current) + 1 + len(word) > self.cols:
                        wrapped_headline.append(self._center(current))
                        current = word
                    elif not current:
                        current = word
                    else:
                        current += " " + word
                if current:
                    wrapped_headline.append(self._center(current))
                content_lines.extend(wrapped_headline)
            else:
                content_lines.append(self._center(headline_text))

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
        
        # Tell state how far it can scroll
        state.max_scroll_offset = max(0, len(content_lines) - window_height)
        
        # Slice the content based on scroll_offset
        lines = content_lines[state.scroll_offset : state.scroll_offset + window_height]

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

    def _title_row(self, title: str, suffix: str) -> str:
        """Build a title row: title left-aligned, suffix right-aligned."""
        avail = self.cols - len(suffix)
        if len(title) > avail:
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
                    
                label = label[offset : offset + max_label]
            else:
                label = label[: max_label - 2] + ".."
                
        return self._fixed(f"{prefix}{label}")

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
