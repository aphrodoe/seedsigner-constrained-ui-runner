from typing import List
from src.screen_state import ScreenState

class MainMenuMixin:
    def _render_main_menu(self, state: ScreenState) -> List[str]:
        """Render the 4-icon main menu with text-based icons."""
        total = len(state.items)
        pos = f" {state.selected_index + 1}/{total}" if total > 0 else ""
        title = state.context.get("top_nav", {}).get("title", "SeedSigner")
        title_line = self._title_row(title, pos, state)

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
            all_content = []
            for i in range(total):
                item = state.items[i]
                label = item.get("label", "")
                prefix = ">" if i == state.selected_index else " "
                icon = icon_map.get(label, "[-]")
                entry = f"{prefix}{icon} {label}"
                all_content.append(self._fixed(entry))
                
            return self._do_sliding_window(state, title_line, all_content, 0)

    # ── seed_mnemonic_entry_screen ──────────────────────────────────
    
