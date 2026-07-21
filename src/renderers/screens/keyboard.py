from typing import List
from src.screen_state import ScreenState

class KeyboardMixin:
    def _render_keyboard(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Input")
        
        # Append length counter if target is specified
        target = state.context.get("entropy_target")
        if target:
            title = f"{title} {len(state.entered_text)}/{target}"
            
        title_line = self._title_row(title, "", state)
        
        mode_name, chars = state.keyboard_modes[state.active_mode_index]
        chars = list(chars) # copy
        
        # Add mode toggles to the end of the chars for all tiers
        toggles = []
        for i, (m_name, _) in enumerate(state.keyboard_modes):
            if i != state.active_mode_index and m_name:
                toggles.append(f"[{m_name}]")
                
        # Insert toggles before [DEL] and [OK] if they exist
        insert_idx = len(chars)
        for i, c in enumerate(chars):
            if c == "[DEL]" or c == "[OK]" or c == "[ ]":
                insert_idx = i
                break
                
        chars = chars[:insert_idx] + toggles + chars[insert_idx:]
        state.keyboard_chars = chars
        
        explicit_cols = state.context.get("cols")
        if explicit_cols:
            state.keyboard_cols = explicit_cols
        elif self.tier >= 2:
            state.keyboard_cols = 4 if self.cols <= 16 else 6
        else:
            state.keyboard_cols = 0
            
        # Ensure char_index is within bounds (in case we switched tiers)
        state.char_index = state.char_index % len(chars)
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
        
        # Add ASCII art for dice/coin if we have enough vertical space
        if self.rows >= 14:
            last_char = state.entered_text[-1] if state.entered_text else ""
            art = []
            if "Dice Roll" in title:
                art = self._get_dice_ascii(last_char)
            elif "Coin Flip" in title:
                art = self._get_coin_ascii(last_char)
                
            if art:
                # Add a blank line for padding
                lines.append(" " * self.cols)
                for line in art:
                    lines.append(self._center(line))
        
        if self.tier >= 2:
            grid_lines = []
            grid_layout = []
            current_line_items = []
            current_line_indices = []
            current_len = 0
            
            for i, c in enumerate(chars):
                is_selected = (i == state.char_index)
                
                if c.startswith("[") and c.endswith("]"):
                    display = c.replace("[", "<").replace("]", ">") if is_selected else c
                else:
                    display = f"[{c}]" if is_selected else f" {c} "
                    
                item_len = len(display)
                space_needed = item_len if current_len == 0 else item_len + 1
                
                if current_len + space_needed > self.cols or len(current_line_items) >= state.keyboard_cols:
                    line_str = " ".join(current_line_items)
                    grid_lines.append(self._center(line_str))
                    grid_layout.append(current_line_indices)
                    current_line_items = [display]
                    current_line_indices = [i]
                    current_len = item_len
                else:
                    current_line_items.append(display)
                    current_line_indices.append(i)
                    current_len += space_needed
                    
            if current_line_items:
                line_str = " ".join(current_line_items)
                grid_lines.append(self._center(line_str))
                grid_layout.append(current_line_indices)
                
            if not hasattr(state, "keyboard_grid_layouts"):
                state.keyboard_grid_layouts = {}
            state.keyboard_grid_layouts[self.tier] = grid_layout
                
            # Vertical sliding window for grid
            available_rows = self.rows - 2 # Title + Input
            
            if not hasattr(self, "_keyboard_window_start"):
                self._keyboard_window_start = 0
                
            # Keep selected row in view
            selected_row_idx = 0
            for r_idx, r_indices in enumerate(grid_layout):
                if state.char_index in r_indices:
                    selected_row_idx = r_idx
                    break
                    
            if selected_row_idx < self._keyboard_window_start:
                self._keyboard_window_start = selected_row_idx
            elif selected_row_idx >= self._keyboard_window_start + available_rows:
                self._keyboard_window_start = selected_row_idx - available_rows + 1
                
            visible_grid = grid_lines[self._keyboard_window_start:self._keyboard_window_start + available_rows]
            
            used_rows = 2 + len(visible_grid)
            padding = max(0, self.rows - used_rows)
            top_pad = padding // 2
            
            for _ in range(top_pad):
                lines.append(self._center(""))
                
            lines.extend(visible_grid)
            return self._pad_rows(lines)
            
        else:
            return self._pad_rows(lines)

    def _get_dice_ascii(self, roll: str) -> list[str]:
        if roll == "1":
            return [" .-------. ", " |       | ", " |   *   | ", " |       | ", " '-------' "]
        elif roll == "2":
            return [" .-------. ", " | *     | ", " |       | ", " |     * | ", " '-------' "]
        elif roll == "3":
            return [" .-------. ", " | *     | ", " |   *   | ", " |     * | ", " '-------' "]
        elif roll == "4":
            return [" .-------. ", " | *   * | ", " |       | ", " | *   * | ", " '-------' "]
        elif roll == "5":
            return [" .-------. ", " | *   * | ", " |   *   | ", " | *   * | ", " '-------' "]
        elif roll == "6":
            return [" .-------. ", " | *   * | ", " | *   * | ", " | *   * | ", " '-------' "]
        else:
            return [" .-------. ", " |       | ", " |   ?   | ", " |       | ", " '-------' "]

    def _get_coin_ascii(self, flip: str) -> list[str]:
        if flip == "0":
            return ["   .---.   ", "  /     \\  ", " | TAILS | ", "  \\     /  ", "   '---'   "]
        elif flip == "1":
            return ["   .---.   ", "  /     \\  ", " | HEADS | ", "  \\     /  ", "   '---'   "]
        else:
            return ["   .---.   ", "  /     \\  ", " |   ?   | ", "  \\     /  ", "   '---'   "]


    # ── large_icon_status_screen ────────────────────────────────────

