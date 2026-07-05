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
        elif state.screen_type == ScreenType.PSBT_OVERVIEW:
            lines = self._render_psbt_overview(state)
        elif state.screen_type == ScreenType.PSBT_ADDRESS_DETAILS:
            lines = self._render_psbt_address_details(state)
        elif state.screen_type == ScreenType.PSBT_CHANGE_DETAILS:
            lines = self._render_psbt_change_details(state)
        elif state.screen_type == ScreenType.PSBT_MATH:
            lines = self._render_psbt_math(state)
        elif state.screen_type == ScreenType.LOCALE_PICKER:
            lines = self._render_locale_picker(state)
        elif state.screen_type == ScreenType.SEED_FINALIZE:
            lines = self._render_seed_finalize(state)
        elif state.screen_type == ScreenType.LOADING:
            lines = self._render_loading(state)
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

    def _do_sliding_window(self, state: ScreenState, title_line: str, all_content: List[str], num_text_lines: int) -> List[str]:
        lines = [title_line]
        if not all_content:
            return self._pad_rows(lines)

        selected_idx = num_text_lines + state.selected_index
        current_scroll = getattr(state, "_unified_scroll_offset", 0)

        if selected_idx < current_scroll:
            current_scroll = selected_idx
        elif selected_idx >= current_scroll + self.item_rows:
            current_scroll = selected_idx - self.item_rows + 1

        max_scroll = max(0, len(all_content) - self.item_rows)
        current_scroll = min(current_scroll, max_scroll)
        setattr(state, "_unified_scroll_offset", current_scroll)

        end = min(len(all_content), current_scroll + self.item_rows)
        lines.extend(all_content[current_scroll:end])

        return self._pad_rows(lines)

    def _render_sliding_window(self, state: ScreenState, title_line: str) -> List[str]:
        """Sliding window that scrolls both wrapped text and items together."""
        text = state.context.get("text", "")
        all_content = []
        if text:
            for line in text.split('\n'):
                all_content.extend(self._word_wrap(line))

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
            elif self.tier == 2:
                # No trailing alphabet on Tier 2 as suggestions show below
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

        custom_icon = state.context.get("icon", "")
        ascii_art = []
        if status_type == "custom":
            icon = ""
            if self.tier >= 3:
                if custom_icon == "\ue91f": #  microSD
                    ascii_art = [
                        " .-------. ",
                        " |SD   _ | ",
                        " |    (_)| ",
                        " '-------' "
                    ]
                elif custom_icon == "\ue921": #  Pen
                    ascii_art = [
                        "    //     ",
                        "   //      ",
                        "  //       ",
                        " //_       ",
                        " `-'       "
                    ]
        
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
        
        if ascii_art:
            for art_line in ascii_art:
                content_lines.append(self._center(art_line))
            content_lines.append(self._center(""))

        import textwrap

        headline = state.context.get("status_headline", "")
        if headline:
            if icon.strip() and self.tier >= 2:
                icon_line = f"---{icon}---"
                if warning_edges:
                    content_lines.append(f"{edge_char}{icon_line.center(wrap_cols)}{edge_char}")
                else:
                    content_lines.append(self._center(icon_line))
                headline_text = headline
            else:
                headline_text = f"{icon} {headline}" if icon.strip() else headline
                
            wrapped = textwrap.wrap(headline_text, width=wrap_cols)
            for line in wrapped:
                if warning_edges:
                    content_lines.append(f"{edge_char}{line.center(wrap_cols)}{edge_char}")
                else:
                    content_lines.append(self._center(line))
                    
            # For Tier 0 (2 rows), if there's a headline, it's better to drop the generic "Status" title
            # so the headline is visible without scrolling.
            if self.tier == 0 and len(content_lines) > 1 and title_line in content_lines:
                content_lines.remove(title_line)

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
        
        # Vertically center if it fits perfectly
        if len(content_lines) < window_height:
            padding_top = (window_height - len(content_lines)) // 2
            empty_line = f"{edge_char}{' '*wrap_cols}{edge_char}" if warning_edges else " " * self.cols
            content_lines = [content_lines[0]] + [empty_line] * padding_top + content_lines[1:]
            
        # Tell state how far it can scroll without shrinking previous renderer constraints
        new_max = max(0, len(content_lines) - window_height)
        state.max_scroll_offset = max(getattr(state, 'max_scroll_offset', 0), new_max)
        
        # Auto-scroll if it's a long message and no manual scrolling has occurred
        start = min(state.scroll_offset, new_max)
        if new_max > 0 and state.scroll_offset == 0:
            # Increase scroll speed to 1 line every 4 ticks
            auto_scroll = (state.marquee_tick // 4) % (new_max + 4)
            start = min(auto_scroll, new_max)
            
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

    # ── seed_finalize_screen ────────────────────────────────────────

    def _render_seed_finalize(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Finalize Seed")
        title_line = self._title_row(title, "", state)
        
        fingerprint = state.context.get("fingerprint", "")
        fingerprint_label = state.context.get("fingerprint_label", "")
        
        all_content = []
        if fingerprint:
            all_content.append(self._center(fingerprint_label))
            # Optional: formatting it like [ 8c65eb9f ] or similar if we want to mimic a border
            all_content.append(self._center(fingerprint))
            all_content.append(self._center(""))
            
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, 0)

    # ── loading_screen ──────────────────────────────────────────────

    def _render_loading(self, state: ScreenState) -> List[str]:
        text = state.context.get("text", "")
        
        # Simulate a spinner using the marquee tick
        spinner = ["|", "/", "-", "\\"]
        spin_char = spinner[(state.marquee_tick // 2) % len(spinner)]
        
        lines = []
        # Centering vertically based on whether there is text
        total_content = 2 if text else 1
        padding_top = max(0, (self.rows - total_content) // 2)
        
        for _ in range(padding_top):
            lines.append(self._center(""))
            
        if text:
            lines.append(self._center(text))
        lines.append(self._center(spin_char))
        
        return self._pad_rows(lines)

    # ── helpers ─────────────────────────────────────────────────────

    def _render_locale_picker(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Language")
        title_line = self._title_row(title, "", state)
        
        rows = state.context.get("rows", [])
        active = state.context.get("active_locale", "")
        
        all_content = []
        for i, row in enumerate(rows):
            english = row.get("english", "")
            native = row.get("native", "")
            locale = row.get("locale", "")
            
            if self.tier >= 2:
                display = f"{native} ({english})" if native != english else native
            else:
                display = native
            
            selected = (i == state.selected_index)
            if locale == active:
                display = f"✓ {display}"
            else:
                display = f"  {display}"
                
            all_content.append(self._item_row(display, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, num_text_lines=0)

    def _render_psbt_overview(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Transaction")
        title_line = self._title_row(title, "", state)
        
        amount = state.context.get("btc_amount", {})
        primary = amount.get("primary", "")
        unit = amount.get("unit", "")
        
        content = []
        if primary and unit:
            content.append(f"Spend: {primary} {unit}")
            
        num_inputs = state.context.get("num_inputs", 0)
        content.append(f"Inputs: {num_inputs}")
        
        dest_addrs = state.context.get("destination_addresses", [])
        if dest_addrs:
            content.append(f"Destinations: {len(dest_addrs)}")
            
        num_self = state.context.get("num_self_transfer_outputs", 0)
        if num_self > 0:
            content.append(f"Self-transfers: {num_self}")
            
        if state.context.get("has_op_return"):
            content.append("OP_RETURN: 1")
            
        num_change = state.context.get("num_change_outputs", 0)
        if num_change > 0:
            content.append(f"Change outputs: {num_change}")
            
        all_content = []
        for line in content:
            all_content.append(self._center(line))
            
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, num_text_lines=len(content))

    def _render_psbt_address_details(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Verify Send Address")
        title_line = self._title_row(title, "", state)
        
        amount = state.context.get("btc_amount", {})
        primary = amount.get("primary", "")
        unit = amount.get("unit", "")
        
        all_content = []
        if primary and unit:
            all_content.append(self._center(f"Amount: {primary} {unit}"))
            all_content.append(self._center(""))
            
        address = state.context.get("address", "")
        if address:
            for line in self._word_wrap(address):
                all_content.append(self._center(line))
            all_content.append(self._center(""))
                
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, num_text)

    def _render_psbt_change_details(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Your Change")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        addr_type = state.context.get("address_type_label", "")
        if addr_type:
            all_content.append(self._center(f"[{addr_type}]"))
            
        amount = state.context.get("btc_amount", {})
        primary = amount.get("primary", "")
        unit = amount.get("unit", "")
        if primary and unit:
            all_content.append(self._center(f"{primary} {unit}"))
            all_content.append(self._center(""))
            
        address = state.context.get("address", "")
        if address:
            for line in self._word_wrap(address):
                all_content.append(self._center(line))
            all_content.append(self._center(""))
            
        is_verified = state.context.get("is_verified", False)
        if is_verified:
            verified_text = state.context.get("verified_text", "Address verified!")
            all_content.append(self._center(f"✓ {verified_text}"))
            all_content.append(self._center(""))
            
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, num_text)

    def _render_psbt_math(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Transaction Math")
        title_line = self._title_row(title, "", state)
        
        amounts = state.context.get("amounts", {})
        labels = state.context.get("labels", {})
        
        all_content = []
        def add_row(key: str, prefix: str = ""):
            if key in amounts and key in labels:
                val = amounts[key]
                lbl = labels[key]
                # left align label, right align amount
                avail = self.cols - len(lbl) - len(prefix) - len(val) - 1
                if avail < 1:
                    avail = 1
                row = f"{lbl}{' ' * avail}{prefix}{val}"
                all_content.append(self._fixed(row[:self.cols]))
                
        add_row("input")
        add_row("spend", "-")
        add_row("change", "-")
        add_row("fee", "=")
        
        num_text = len(all_content)
        if num_text > 0:
            all_content.append(self._center(""))
            num_text += 1
            
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, num_text)

    def _title_row(self, title: str, suffix: str, state: ScreenState = None) -> str:
        """Build a title row: title left-aligned, suffix right-aligned. Marquee if too long."""
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

    def _render_splash(self, state: ScreenState) -> List[str]:
        """Render the Splash Screen with versions and partners."""
        version = state.context.get("version", "")
        show_partners = state.context.get("show_partner_logos", False)
        sponsor_text = state.context.get("sponsor_text", "")
        boot_logo_only = state.context.get("boot_logo_only", False)
        
        def _anim_center(text: str) -> str:
            if len(text) <= self.cols:
                return text.center(self.cols)
            diff = len(text) - self.cols
            total_frames = diff + 10
            frame = state.marquee_tick % total_frames
            if frame < 5: offset = 0
            elif frame >= 5 + diff: offset = diff
            else: offset = frame - 5
            visible = text[offset : offset + self.cols]
            return visible.center(self.cols)
        
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
                lines.append(_anim_center(sponsor_text))
                lines.append(_anim_center("Human Rights Foundation"))
                
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
                
            lines.append(_anim_center(bottom_text))
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
