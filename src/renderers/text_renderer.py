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

        item_line = self._item_row(display, selected=True)
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
            lines.append(self._item_row(display, selected=selected))

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

    # ── large_icon_status_screen ────────────────────────────────────

    def _render_status(self, state: ScreenState) -> List[str]:
        """Render success / warning / error status screens."""
        icon_map = {"success": "\x00", "warning": "!", "error": "X"}  # \x00 = custom char on real LCD
        icon = icon_map.get(state.context.get("status_icon", ""), " ")
        title = state.context.get("title", "")

        lines = [self._center(f"{icon} {title}")]

        headline = state.context.get("status_headline", "")
        if headline:
            lines.append(self._center(headline))

        text = state.context.get("text", "")
        if text:
            # Word-wrap text into available rows
            wrapped = self._word_wrap(text)
            lines.extend(wrapped)

        return self._pad_rows(lines)

    # ── helpers ─────────────────────────────────────────────────────

    def _title_row(self, title: str, suffix: str) -> str:
        """Build a title row: title left-aligned, suffix right-aligned."""
        avail = self.cols - len(suffix)
        if len(title) > avail:
            title = title[: avail - 2] + ".."
        return self._fixed(f"{title:<{avail}}{suffix}")

    def _item_row(self, label: str, selected: bool) -> str:
        """Build an item row with a `> ` or `  ` prefix."""
        prefix = "> " if selected else "  "
        max_label = self.cols - len(prefix)
        if len(label) > max_label:
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
