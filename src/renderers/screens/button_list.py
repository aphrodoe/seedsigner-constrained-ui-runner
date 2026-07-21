from typing import List
from src.screen_state import ScreenState

class ButtonListMixin:
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

        item_line = self._item_row(display, selected=True, state=state, index=state.selected_index)
        
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
        """Sliding window that scrolls both wrapped text and items together."""
        text = state.context.get("text", "")
        all_content = []
        if text:
            for line in text.split('\n'):
                for wrapped in self._word_wrap(line):
                    all_content.append(self._center(wrapped))

        num_text_lines = len(all_content)

        for i in range(len(state.items)):
            item = state.items[i]
            label = item.get("label", "")
            value = item.get("value", "")
            if value and value != label:
                display = f"{label}: {value}"
            else:
                display = label

            selected = (i == state.selected_index)
            all_content.append(self._item_row(display, selected=selected, state=state, index=i))

        return self._do_sliding_window(state, title_line, all_content, num_text_lines)

    # ── main_menu_screen ────────────────────────────────────────────

