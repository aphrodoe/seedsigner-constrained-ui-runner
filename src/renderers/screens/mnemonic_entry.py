from typing import List
from src.screen_state import ScreenState

class MnemonicEntryMixin:
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
            elif self.tier >= 1:
                # No trailing alphabet on Tier 1 and 2 as suggestions show below
                cursor_str = f"[{char}]" if focus == "keyboard" else f" {char} "
                kb_str = f"{entered}{cursor_str}"
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
                is_enabled = state.is_key_enabled(c)
                
                if c.startswith("[") and c.endswith("]"):
                    display = c.replace("[", "<").replace("]", ">") if is_selected else c
                else:
                    if is_enabled:
                        display = f"[{c}]" if is_selected else f" {c} "
                    else:
                        display = f"[{c}]" if is_selected else f" . "
                    
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
                if entered:
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
                if entered:
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

