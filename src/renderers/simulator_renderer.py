from src.renderers.base_renderer import BaseRenderer
from src.screen_state import ScreenState, ScreenType

class SimulatorRenderer(BaseRenderer):
    def __init__(self, visible_rows: int = 5, cols: int = 20):
        super().__init__(visible_rows)
        self.cols = cols
        
    def render(self, state: ScreenState):
        self.clear()
        
        # Simple ASCII box
        print(f"┌{'─' * self.cols}┐")
        
        if state.screen_type == ScreenType.BUTTON_LIST:
            self._render_button_list(state)
        elif state.screen_type == ScreenType.MAIN_MENU:
            self._render_main_menu(state)
        elif state.screen_type == ScreenType.LARGE_ICON_STATUS:
            self._render_status(state)
        else:
            print(f"│{'Unsupported Screen'.center(self.cols)}│")
            
        print(f"└{'─' * self.cols}┘")
        
    def _render_button_list(self, state: ScreenState):
        # Render title
        title = state.context.get("top_nav", {}).get("title", "Menu")
        
        # Position indicator e.g. [2/10]
        total = len(state.items)
        pos_str = f" [{state.selected_index + 1}/{total}]" if total > 0 else ""
        
        avail_title_len = self.cols - len(pos_str)
        if len(title) > avail_title_len:
            title = title[:avail_title_len - 2] + ".."
            
        title_line = f"{title:<{avail_title_len}}{pos_str}"
        print(f"│{title_line:<{self.cols}}│")
        print(f"├{'─' * self.cols}┤")
        
        # Render items
        start_idx = state.scroll_offset
        end_idx = min(len(state.items), start_idx + self.visible_rows)
        
        for i in range(start_idx, end_idx):
            item = state.items[i]
            label = item.get("label", "")
            
            prefix = "> " if i == state.selected_index else "  "
            
            # Truncate label if necessary
            if len(label) > self.cols - 2:
                label = label[:self.cols - 4] + ".."
                
            line = f"{prefix}{label}"
            print(f"│{line:<{self.cols}}│")
            
        # Pad remaining rows
        drawn_rows = end_idx - start_idx
        for _ in range(drawn_rows, self.visible_rows):
            print(f"│{' ' * self.cols}│")

    def _render_main_menu(self, state: ScreenState):
        # Simple 2x2 grid representation
        items = state.items
        for i in range(0, min(len(items), 4), 2):
            left = items[i].get("label", "")
            right = items[i+1].get("label", "") if i+1 < len(items) else ""
            
            left_prefix = ">" if i == state.selected_index else " "
            right_prefix = ">" if i+1 == state.selected_index else " "
            
            # Rough formatting for 20 cols
            line = f"{left_prefix}{left[:8]:8} {right_prefix}{right[:8]:8}"
            print(f"│{line:<{self.cols}}│")
            print(f"│{' ' * self.cols}│")
            
        # pad remaining
        print(f"│{' ' * self.cols}│")

    def _render_status(self, state: ScreenState):
        title = state.context.get("title", "")
        print(f"│{title.center(self.cols)}│")
        print(f"├{'─' * self.cols}┤")
        
        headline = state.context.get("status_headline", "")
        if headline:
            print(f"│{headline.center(self.cols)}│")
            
        print(f"│{' ' * self.cols}│")
        print(f"│{'[ OK ]'.center(self.cols)}│")
        print(f"│{' ' * self.cols}│")
        
    def clear(self):
        # Clear terminal screen (cross-platform)
        print("\033[H\033[J", end="")
