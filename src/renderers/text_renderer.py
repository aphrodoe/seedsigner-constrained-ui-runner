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
        # Visual-only screens (camera, QR, I/O test) — not applicable to text UI
        if state.screen_type.is_visual_only():
            title = state.context.get("top_nav", {}).get("title", "Visual Only")
            lines = [self._title_row(title, "", state)]
            lines.append(self._center("[Visual Only]"))
            lines.append(self._center("No text-UI"))
            return self._pad_rows(lines)

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
        # ── New screen renderers ────────────────────────────────────
        elif state.screen_type == ScreenType.TOAST_OVERLAY:
            lines = self._render_toast_overlay(state)
        elif state.screen_type == ScreenType.SEED_EXPORT_XPUB_DETAILS:
            lines = self._render_seed_export_xpub_details(state)
        elif state.screen_type == ScreenType.SEED_REVIEW_PASSPHRASE:
            lines = self._render_seed_review_passphrase(state)
        elif state.screen_type == ScreenType.SEED_WORDS:
            lines = self._render_seed_words(state)
        elif state.screen_type == ScreenType.MULTISIG_WALLET_DESCRIPTOR:
            lines = self._render_multisig_wallet_descriptor(state)
        elif state.screen_type == ScreenType.SEED_TRANSCRIBE_SEEDQR_FORMAT:
            lines = self._render_seed_transcribe_seedqr_format(state)
        elif state.screen_type == ScreenType.SEED_SIGN_MESSAGE_CONFIRM_ADDRESS:
            lines = self._render_seed_sign_message_confirm_address(state)
        elif state.screen_type == ScreenType.SEED_SIGN_MESSAGE_CONFIRM_MESSAGE:
            lines = self._render_seed_sign_message_confirm_message(state)
        elif state.screen_type == ScreenType.SEED_ADDRESS_VERIFICATION:
            lines = self._render_seed_address_verification(state)
        elif state.screen_type == ScreenType.SEED_ADDRESS_VERIFICATION_SUCCESS:
            lines = self._render_seed_address_verification_success(state)
        elif state.screen_type == ScreenType.TOOLS_CALC_FINAL_WORD:
            lines = self._render_tools_calc_final_word(state)
        elif state.screen_type == ScreenType.TOOLS_CALC_FINAL_WORD_DONE:
            lines = self._render_tools_calc_final_word_done(state)
        elif state.screen_type == ScreenType.TOOLS_ADDRESS_EXPLORER_ADDRESS_LIST:
            lines = self._render_tools_address_explorer_list(state)
        elif state.screen_type == ScreenType.TOOLS_ADDRESS_EXPLORER_ADDRESS_TYPE:
            lines = self._render_tools_address_explorer_type(state)
        elif state.screen_type == ScreenType.SETTINGS_QR_CONFIRMATION:
            lines = self._render_settings_qr_confirmation(state)
        elif state.screen_type in (ScreenType.DONATE, ScreenType.RESET,
                                    ScreenType.POWER_OFF_NOT_REQUIRED):
            lines = self._render_text_only(state)
        # ── Button-list fallback screens ────────────────────────────
        elif state.screen_type == ScreenType.POWER_OPTIONS:
            lines = self._render_button_list(state)
        elif state.screen_type == ScreenType.PSBT_OP_RETURN:
            lines = self._render_psbt_op_return(state)
        else:
            lines = self._pad_rows([self._center("Unsupported")])
            
        toast_msg = state.context.get("toast")
        if toast_msg:
            toast_msg = toast_msg.replace("\n", " ").strip()
            max_label = self.cols - 4
            if len(toast_msg) > max_label:
                diff = len(toast_msg) - max_label
                total_frames = diff + 10
                frame = state.marquee_tick % total_frames
                if frame < 5: offset = 0
                elif frame >= 5 + diff: offset = diff
                else: offset = frame - 5
                visible = toast_msg[offset : offset + max_label]
                toast_text = f"[ {visible} ]"
            else:
                toast_text = f"[ {toast_msg} ]"
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

        max_scroll = max(0, len(all_content) - self.item_rows)
        
        if not hasattr(state, "tier_max_scroll"):
            state.tier_max_scroll = {}
        state.tier_max_scroll[self.tier] = max_scroll

        selected_idx = num_text_lines + state.selected_index
        
        if not hasattr(state, "tier_unified_scroll"):
            state.tier_unified_scroll = {}
            
        current_scroll = state.tier_unified_scroll.get(self.tier, 0)
        
        if not hasattr(state, f"_opened_{self.tier}"):
            setattr(state, f"_opened_{self.tier}", True)
            state.tier_unified_scroll[self.tier] = 0
            
        current_scroll = state.tier_unified_scroll.get(self.tier, 0)
        
        # Base sliding window calculation
        if selected_idx < current_scroll:
            current_scroll = selected_idx
        elif selected_idx >= current_scroll + self.item_rows:
            current_scroll = selected_idx - self.item_rows + 1

        # Calculate natural min scroll needed to keep selected item visible
        natural_min_scroll = selected_idx - self.item_rows + 1 if selected_idx >= self.item_rows else 0
        
        if not hasattr(state, "tier_text_intent"):
            state.tier_text_intent = {}

        # If the user hasn't moved yet, we want to stay at 0 to show the text!
        if not getattr(state, "_user_has_moved", False):
            if state.selected_index == 0 and natural_min_scroll > 0:
                # Initialize intent so the first 'down' scrolls sequentially
                state.tier_text_intent[self.tier] = -natural_min_scroll
                
                if state.screen_type == ScreenType.SEED_SIGN_MESSAGE_CONFIRM_MESSAGE:
                    # Auto-scroll vertically if the content doesn't fit on screen
                    # 6 ticks per frame (0.6s per line). Pause at top/bottom for 6 frames (3.6s)
                    total_frames = natural_min_scroll * 2 + 12
                    frame = (state.marquee_tick // 6) % total_frames
                    if frame < 6:
                        current_scroll = 0
                    elif frame < 6 + natural_min_scroll:
                        current_scroll = frame - 6
                    elif frame < 12 + natural_min_scroll:
                        current_scroll = natural_min_scroll
                    else:
                        current_scroll = natural_min_scroll - (frame - (12 + natural_min_scroll))
                else:
                    current_scroll = 0
            else:
                current_scroll = 0
        else:
            if self.tier not in state.tier_text_intent:
                state.tier_text_intent[self.tier] = 0
            
        # Apply manual text scroll intent if the user is scrolling text at the top button
        if state.selected_index == 0 and getattr(state, "_user_has_moved", False):
            intent = state.tier_text_intent.get(self.tier, 0)
            current_scroll += intent
            
            # Clamp locally, DO NOT mutate the global intent
            if current_scroll < 0:
                current_scroll = 0
            elif current_scroll > natural_min_scroll:
                current_scroll = natural_min_scroll

        # Track if this tier has hit the top for ScreenState to prevent runaway intent
        if not hasattr(state, "tier_at_top"):
            state.tier_at_top = {}
        state.tier_at_top[self.tier] = (current_scroll <= 0)

        current_scroll = min(current_scroll, max_scroll)
        state.tier_unified_scroll[self.tier] = current_scroll

        end = min(len(all_content), current_scroll + self.item_rows)
        lines.extend(all_content[current_scroll:end])

        return self._pad_rows(lines)

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
            if custom_icon == "\ue91f": #  microSD
                if self.tier >= 3:
                    ascii_art = [
                        " .-------. ",
                        " |SD   _ | ",
                        " |    (_)| ",
                        " '-------' "
                    ]
                else:
                    icon = "[SD]"
            elif custom_icon == "\ue921": #  Pen
                if self.tier >= 3:
                    ascii_art = [
                        "    //     ",
                        "   //      ",
                        "  //       ",
                        " //_       ",
                        " `-'       "
                    ]
                else:
                    icon = "[PEN]"
        
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
                if warning_edges:
                    content_lines.append(f"{edge_char}{art_line.center(wrap_cols)}{edge_char}")
                else:
                    content_lines.append(self._center(art_line))
            
            if warning_edges:
                content_lines.append(f"{edge_char}{' '*wrap_cols}{edge_char}")
            else:
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
        
        if not hasattr(state, "tier_max_scroll"):
            state.tier_max_scroll = {}
        state.tier_max_scroll[self.tier] = new_max
        
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
            # Ensure it renders with marquee by leveraging the standard item row logic
            state.context["is_button_text_centered"] = True
            button_line = self._item_row(label, selected=True, state=state, index=state.selected_index)
            
            while len(lines) < window_height:
                if warning_edges:
                    lines.append(f"{edge_char}{' '*wrap_cols}{edge_char}")
                else:
                    lines.append(" " * self.cols)
                
            lines.append(button_line)

        return self._pad_rows(lines)

    def _pad_text_above_buttons(self, text_lines: List[str], num_buttons: int) -> List[str]:
        """Pads text lines vertically so they are centered in the space above buttons."""
        total_lines = len(text_lines) + num_buttons
        if total_lines < self.rows - 1:
            space_above = self.rows - 1 - num_buttons
            padding_top = (space_above - len(text_lines)) // 2
            padding_bottom = space_above - len(text_lines) - padding_top
            
            return [self._center("")] * padding_top + text_lines + [self._center("")] * padding_bottom
        return text_lines

    # ── seed_finalize_screen ────────────────────────────────────────

    def _render_seed_finalize(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Finalize Seed")
        title_line = self._title_row(title, "", state)
        
        fingerprint = state.context.get("fingerprint", "")
        fingerprint_label = state.context.get("fingerprint_label", "")
        
        text_lines = []
        if fingerprint:
            for line in self._word_wrap(f"@ {fingerprint_label}"):
                text_lines.append(self._center(line))
            for line in self._word_wrap(fingerprint):
                text_lines.append(self._center(line))
            
        text_lines = self._pad_text_above_buttons(text_lines, len(state.items))
        all_content = text_lines
            
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, len(text_lines))

    # ── loading_screen ──────────────────────────────────────────────

    def _render_loading(self, state: ScreenState) -> List[str]:
        text = state.context.get("text", "")
        
        has_space = self.rows >= 4
        frame = (state.marquee_tick // 2) % 4
        
        if has_space:
            spinners = [
                [" | ", " | ", " | "],
                ["  /", " / ", "/  "],
                ["   ", "---", "   "],
                ["\\  ", " \\ ", "  \\"]
            ]
            spin_lines = spinners[frame]
        else:
            spinner = ["|", "/", "-", "\\"]
            spin_lines = [spinner[frame]]
        
        lines = []
        # Centering vertically based on whether there is text
        total_content = len(spin_lines) + (1 if text else 0)
        padding_top = max(0, (self.rows - total_content) // 2)
        
        for _ in range(padding_top):
            lines.append(self._center(""))
            
        if text:
            lines.append(self._center(text))
            
        for spin_line in spin_lines:
            lines.append(self._center(spin_line))
        
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
            
        if self.tier >= 3:
            # Huge screen: Render ASCII flowchart diagram
            all_content = []
            if primary and unit:
                all_content.append(self._center(f"{primary} {unit}"))
                all_content.append(self._center(""))
            
            flow_lines = self._get_psbt_ascii_flow(state)
            for line in flow_lines:
                all_content.append(self._center(line))
        else:
            all_content = []
            for line in content:
                for wrapped in self._word_wrap(line):
                    all_content.append(self._center(wrapped))
                
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
            
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, num_text_lines=num_text)

    def _get_psbt_ascii_flow(self, state: ScreenState) -> List[str]:
        num_inputs = state.context.get("num_inputs", 0)
        dest_addrs = state.context.get("destination_addresses", [])
        num_self = state.context.get("num_self_transfer_outputs", 0)
        has_op = state.context.get("has_op_return", False)
        num_change = state.context.get("num_change_outputs", 0)
        
        left = []
        if num_inputs == 1: left.append("1 input")
        elif num_inputs <= 4: left.extend([f"input {i}" for i in range(1, num_inputs + 1)])
        else: left.extend(["input 1", "input 2", " [...] ", f"input {num_inputs-1}", f"input {num_inputs}"])
        
        right = []
        if dest_addrs:
            if len(dest_addrs) == 1: right.append("recipient")
            elif len(dest_addrs) <= 2: right.extend([f"recipient {i}" for i in range(1, len(dest_addrs) + 1)])
            else: right.extend(["recip 1", " [...] ", f"recip {len(dest_addrs)}"])
        if num_self > 0: right.append("self-transfer")
        if has_op: right.append("OP_RETURN")
        if num_change > 0: right.append("change")
        right.append("fee")
        
        max_h = max(len(left), len(right))
        if max_h % 2 == 0: max_h += 1 # Force odd for a clear middle row
        
        while len(left) < max_h:
            if len(left) % 2 == 0: left.append("")
            else: left.insert(0, "")
        while len(right) < max_h:
            if len(right) % 2 == 0: right.append("")
            else: right.insert(0, "")
            
        left_w = max((len(s) for s in left if s), default=0)
        right_w = max((len(s) for s in right if s), default=0)
        
        available = self.cols - left_w - right_w
        if available < 3: available = 3
        
        use_conn = available >= 5
        if use_conn:
            mid_w = available - 4
        else:
            mid_w = available - 2
            
        lines = []
        anim_char = ["-", ">"][(state.marquee_tick // 2) % 2]
        
        mid_row = max_h // 2
        l_first = next((i for i, s in enumerate(left) if s), mid_row)
        l_last = max((i for i, s in enumerate(left) if s), default=mid_row)
        r_first = next((i for i, s in enumerate(right) if s), mid_row)
        r_last = max((i for i, s in enumerate(right) if s), default=mid_row)
        
        for i in range(max_h):
            l_str = left[i].rjust(left_w)
            r_str = right[i].ljust(right_w)
            
            # Left side tree
            if left[i]:
                if i == l_first and i == l_last: l_c = "-"
                elif i == mid_row: l_c = "+"
                elif i == l_first: l_c = "\\"
                elif i == l_last: l_c = "/"
                else: l_c = "|"
            else:
                if l_first <= i <= l_last:
                    if i == mid_row: l_c = "+"
                    else: l_c = "|"
                else:
                    l_c = " "
                    
            # Right side tree
            if right[i]:
                if i == r_first and i == r_last: r_c = "-"
                elif i == mid_row: r_c = "+"
                elif i == r_first: r_c = "/"
                elif i == r_last: r_c = "\\"
                else: r_c = "|"
            else:
                if r_first <= i <= r_last:
                    if i == mid_row: r_c = "+"
                    else: r_c = "|"
                else:
                    r_c = " "
                    
            if i == mid_row: mid_c = anim_char * mid_w
            else: mid_c = " " * mid_w
                
            if use_conn:
                l_conn = "-" if left[i] or (l_first<=i<=l_last and i==mid_row) else " "
                r_conn = "-" if right[i] or (r_first<=i<=r_last and i==mid_row) else " "
                lines.append(f"{l_str}{l_conn}{l_c}{mid_c}{r_c}{r_conn}{r_str}")
            else:
                lines.append(f"{l_str}{l_c}{mid_c}{r_c}{r_str}")
                
        return lines

    def _render_psbt_address_details(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Verify Send Address")
        title_line = self._title_row(title, "", state)
        
        amount = state.context.get("btc_amount", {})
        primary = amount.get("primary", "")
        unit = amount.get("unit", "")
        
        all_content = []
        if primary and unit:
            for line in self._word_wrap(f"Amount: {primary} {unit}"):
                all_content.append(self._center(line))
            
        address = self._highlight_address(state.context.get("address", ""))
        if address:
            for line in self._word_wrap(address):
                all_content.append(self._center(line))
                
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
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
            for line in self._word_wrap(f"{primary} {unit}"):
                all_content.append(self._center(line))
            
        address = self._highlight_address(state.context.get("address", ""))
        if address:
            for line in self._word_wrap(address):
                all_content.append(self._center(line))
            
        is_verified = state.context.get("is_verified", False)
        if is_verified:
            verified_text = state.context.get("verified_text", "Address verified!")
            all_content.append(self._center(f"✓ {verified_text}"))
            
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
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
        def add_row(amount_key: str, label_key: str, prefix: str = ""):
            if amount_key in amounts and label_key in labels:
                val = amounts[amount_key]
                if val == "0" and amount_key == "spend":
                    return # Omit 0 spend for self-transfers
                lbl = labels[label_key]
                
                amount_str = f"{prefix}{val}"
                if len(lbl) + 1 + len(amount_str) > self.cols:
                    # Too long to fit on one line, wrap amount to next line
                    all_content.append(self._fixed(lbl[:self.cols]))
                    # Right-align the amount on the new line
                    avail = self.cols - len(amount_str)
                    if avail < 0: avail = 0
                    all_content.append(self._fixed(" " * avail + amount_str[:self.cols]))
                else:
                    # Fits on one line
                    avail = self.cols - len(lbl) - len(amount_str)
                    row = f"{lbl}{' ' * avail}{amount_str}"
                    all_content.append(self._fixed(row))
                
        add_row("input", "inputs")
        add_row("spend", "recipients", "-")
        add_row("fee", "fee", "-")
        
        if self.tier > 0:
            all_content.append("-" * self.cols)
            
        add_row("change", "change")
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, num_text)

    def _title_row(self, title: str, suffix: str, state: ScreenState = None) -> str:
        """Build a title row: title left-aligned, suffix right-aligned. Marquee if too long."""
        import re
        if self.tier >= 2 and re.match(r'^\s*\d+/\d+$', suffix):
            suffix = ""

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

    # ── text_only (reset, power_off_not_required, donate) ───────────

    def _render_text_only(self, state: ScreenState) -> List[str]:
        """Render screens with title + body text + optional URL, no buttons."""
        title = state.context.get("top_nav", {}).get("title", "")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        text = state.context.get("text", "")
        if text:
            for paragraph in text.split('\n'):
                paragraph = paragraph.strip()
                if paragraph:
                    for line in self._word_wrap(paragraph):
                        all_content.append(self._center(line))
                else:
                    all_content.append(self._center(""))
        
        # donate_screen has a URL field
        url = state.context.get("url", "")
        if url:
            all_content.append(self._center(""))
            all_content.append(self._center(url))

        # Vertically center if the content fits on a single screen
        available_rows = self.rows - 1
        if len(all_content) < available_rows:
            pad_top = (available_rows - len(all_content)) // 2
            for _ in range(pad_top):
                all_content.insert(0, self._center(""))

        return self._do_sliding_window(state, title_line, all_content, len(all_content))

    # ── toast_overlay_screen ────────────────────────────────────────

    def _render_toast_overlay(self, state: ScreenState) -> List[str]:
        """Composite: render background screen, overlay toast banner on last row."""
        severity = state.context.get("severity", "default")
        label_text = state.context.get("label_text", "").replace("\n", " ").strip()
        
        icon_map = {
            "success": "✓",
            "warning": "⚠",
            "dire_warning": "‼",
            "error": "✕",
            "info": "ℹ",
            "default": "·",
        }
        icon = icon_map.get(severity, "·")
        
        # Try to render the background screen
        bg_ctx = state.context.get("background", {})
        bg_lines = None
        if bg_ctx:
            try:
                # Determine the background screen type from its structure
                if bg_ctx.get("top_nav", {}).get("title") == "Home":
                    bg_state = ScreenState("main_menu_screen", bg_ctx, visible_rows=state.visible_rows)
                elif "button_list" in bg_ctx:
                    bg_state = ScreenState("button_list_screen", bg_ctx, visible_rows=state.visible_rows)
                else:
                    bg_state = ScreenState("button_list_screen", bg_ctx, visible_rows=state.visible_rows)
                bg_lines = self.render(bg_state)
            except Exception:
                bg_lines = None
        
        if not bg_lines:
            bg_lines = self._pad_rows([self._center("---")])
        
        # Build toast banner with marquee if needed
        max_label = self.cols - 4
        full_text = f"{icon} {label_text}" if icon else label_text
        if len(full_text) > max_label:
            diff = len(full_text) - max_label
            total_frames = diff + 10
            frame = state.marquee_tick % total_frames
            if frame < 5: offset = 0
            elif frame >= 5 + diff: offset = diff
            else: offset = frame - 5
            visible = full_text[offset : offset + max_label]
            toast_text = f"[ {visible} ]"
        else:
            toast_text = f"[ {full_text} ]"
        
        # Overlay toast on last row (or last 2 rows with separator on larger tiers)
        if self.tier >= 1 and len(bg_lines) >= 2:
            bg_lines[-2] = self._fixed("-" * self.cols)
            bg_lines[-1] = self._center(toast_text)
        else:
            bg_lines[-1] = self._center(toast_text)
        
        return bg_lines

    # ── seed_export_xpub_details_screen ─────────────────────────────

    def _render_seed_export_xpub_details(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Xpub Details")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        warning_edges = state.context.get("warning_edges", False)
        usable_cols = self.cols - 2 if warning_edges else self.cols
        
        def _fmt(text: str) -> str:
            if len(text) > usable_cols:
                text = text[:usable_cols]
            return f"{text:<{usable_cols}}"
            
        fp_label = state.context.get("fingerprint_label", "Fingerprint")
        fp = state.context.get("fingerprint", "")
        if fp:
            all_content.append(_fmt(f"@ {fp_label}"))
            all_content.append(_fmt(f"  {fp}"))
        
        deriv_label = state.context.get("derivation_label", "Derivation")
        deriv = state.context.get("derivation_path", "")
        if deriv:
            all_content.append(_fmt(f"⎇ {deriv_label}"))
            all_content.append(_fmt(f"  {deriv}"))
        
        xpub_label = state.context.get("xpub_label", "Xpub")
        xpub = state.context.get("xpub", "")
        if xpub:
            all_content.append(_fmt(f"✕ {xpub_label}"))
            if len(xpub) > 15:
                xpub = xpub[:15] + ".."
            all_content.append(_fmt(f"  {xpub}"))
        
        # We need to temporarily override self.cols for button padding if warning_edges
        old_cols = self.cols
        self.cols = usable_cols
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        self.cols = old_cols
        
        lines = self._do_sliding_window(state, title_line, all_content, num_text)
        
        if warning_edges:
            animated = state.context.get("animated", False)
            if animated:
                edge_char = "!" if (state.marquee_tick // 2) % 2 == 0 else " "
            else:
                edge_char = "!"
                
            for i in range(1, len(lines)):
                # Take the first `usable_cols` characters to avoid erasing text
                content = lines[i][:usable_cols]
                lines[i] = f"{edge_char}{content}{edge_char}"
                
        return lines

    # ── seed_review_passphrase_screen ───────────────────────────────

    def _render_seed_review_passphrase(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Verify Passphrase")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        passphrase = state.context.get("passphrase", "")
        if passphrase:
            passphrase_display = passphrase.replace(" ", "·")
            for line in self._word_wrap(f'"{passphrase_display}"'):
                all_content.append(self._center(line))
        
        changes_label = state.context.get("changes_fingerprint_label", "changes fingerprint")
        fp_without = state.context.get("fingerprint_without", "")
        fp_with = state.context.get("fingerprint_with", "")
        if fp_without and fp_with:
            for line in self._word_wrap(f"@ {changes_label}"):
                all_content.append(self._center(line))
            for line in self._word_wrap(f"{fp_without} -> {fp_with}"):
                all_content.append(self._center(line))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── seed_words_screen ───────────────────────────────────────────

    def _render_seed_words(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Seed Words")
        title_line = self._title_row(title, "", state)
        
        words = state.context.get("words", [])
        start_num = state.context.get("start_number", 1)
        
        all_content = []
        for i, word in enumerate(words):
            num = start_num + i
            all_content.append(self._fixed(f" {num:>2}. {word}"))
        
        # We need to temporarily override self.cols for button padding if warning_edges
        warning_edges = state.context.get("warning_edges", False)
        usable_cols = self.cols - 2 if warning_edges else self.cols
        old_cols = self.cols
        self.cols = usable_cols
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        self.cols = old_cols
        
        lines = self._do_sliding_window(state, title_line, all_content, num_text)
        
        if warning_edges:
            animated = state.context.get("animated", False)
            if animated:
                edge_char = "!" if (state.marquee_tick // 2) % 2 == 0 else " "
            else:
                edge_char = "!"
                
            for i in range(1, len(lines)):
                content = lines[i][:usable_cols]
                lines[i] = f"{edge_char}{content}{edge_char}"
                
        return lines

    # ── seed_transcribe_seedqr_format_screen ────────────────────────────

    def _render_seed_transcribe_seedqr_format(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "SeedQR Format")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        
        # Standard Format details
        std_label = state.context.get("standard_label", "")
        std_text = state.context.get("standard_text", "")
        if std_label or std_text:
            if std_label:
                all_content.append(self._center(std_label))
            if std_text:
                for line in self._word_wrap(std_text):
                    all_content.append(self._center(line))
                    
        # Add spacing between the two formats
        all_content.append(self._center(""))
        
        # Compact Format details
        cmp_label = state.context.get("compact_label", "")
        cmp_text = state.context.get("compact_text", "")
        if cmp_label or cmp_text:
            if cmp_label:
                all_content.append(self._center(cmp_label))
            if cmp_text:
                for line in self._word_wrap(cmp_text):
                    all_content.append(self._center(line))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "")
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── psbt_op_return_screen ───────────────────────────────────────

    def _render_psbt_op_return(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "OP_RETURN")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        
        # Regular text variation
        text = state.context.get("text", "")
        if text:
            for line in self._word_wrap(text):
                all_content.append(self._center(line))
        
        # Raw hex variation
        hex_data = state.context.get("hex", "")
        if hex_data:
            hex_label = state.context.get("hex_label", "")
            if hex_label:
                all_content.append(self._center(hex_label))
            # Just chunk the hex string since it has no spaces
            for line in self._word_wrap(hex_data):
                all_content.append(self._center(line))
                
        # Optional spacing above buttons
        if all_content:
            all_content.append(self._center(""))
            
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "")
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
            
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── multisig_wallet_descriptor_screen ───────────────────────────

    def _render_multisig_wallet_descriptor(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Descriptor")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        policy_label = state.context.get("policy_label", "Policy")
        policy = state.context.get("policy", "")
        if policy:
            all_content.append(self._center(policy_label))
            all_content.append(self._center(policy))
        
        keys_label = state.context.get("signing_keys_label", "Signing Keys")
        fingerprints = state.context.get("fingerprints", [])
        if fingerprints:
            all_content.append(self._center(keys_label))
            fp_str = " ".join(fingerprints)
            for line in self._word_wrap(fp_str):
                all_content.append(self._center(line))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── seed_sign_message_confirm_address_screen ────────────────────

    def _render_seed_sign_message_confirm_address(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Confirm Address")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        deriv_label = state.context.get("derivation_path_label", "derivation path")
        deriv = state.context.get("derivation_path", "")
        if deriv:
            for line in self._word_wrap(f"⎇ {deriv_label}"):
                all_content.append(self._center(line))
            for line in self._word_wrap(deriv):
                all_content.append(self._center(line))
        
        address = self._highlight_address_verify(state.context.get("address", ""))
        if address:
            for line in self._word_wrap(address):
                all_content.append(self._center(line))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── seed_sign_message_confirm_message_screen ────────────────────

    def _render_seed_sign_message_confirm_message(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Review Message")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        message = state.context.get("message", "")
        if message:
            for p in message.split("\n"):
                if p.strip() == "":
                    all_content.append(self._fixed(""))
                else:
                    for line in self._word_wrap(p):
                        all_content.append(self._fixed(line))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── seed_address_verification_screen ────────────────────────────

    def _render_seed_address_verification(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Verify Address")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        address = self._highlight_address_verify(state.context.get("address", ""))
        if address:
            for line in self._word_wrap(address):
                all_content.append(self._center(line))
        
        type_network = state.context.get("type_network", "")
        network = state.context.get("network", "")
        if type_network:
            for line in self._word_wrap(type_network):
                all_content.append(self._center(line))
        if network and network != "mainnet":
            all_content.append(self._center(f"[{network}]"))
        
        progress = state.context.get("progress_text", "")
        if progress:
            for line in self._word_wrap(progress):
                all_content.append(self._center(line))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── seed_address_verification_success_screen ────────────────────

    def _render_seed_address_verification_success(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Success!")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        headline = state.context.get("status_headline", "")
        if headline:
            for line in self._word_wrap(f"✓ {headline}"):
                all_content.append(self._center(line))
        
        address = self._highlight_address_success(state.context.get("address", ""))
        if address:
            for line in self._word_wrap(address):
                all_content.append(self._center(line))
        
        addr_type = state.context.get("address_type_text", "")
        index_text = state.context.get("index_text", "")
        if addr_type:
            for line in self._word_wrap(addr_type):
                all_content.append(self._center(line))
        if index_text:
            for line in self._word_wrap(index_text):
                all_content.append(self._center(line))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── settings_qr_confirmation_screen ─────────────────────────────

    def _render_settings_qr_confirmation(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Settings QR")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        
        config_name = state.context.get("config_name", "")
        if config_name:
            for line in self._word_wrap(f'"{config_name}"'):
                all_content.append(self._center(line))
                
        status_msg = state.context.get("status_message", "")
        if status_msg:
            if config_name:
                all_content.append(self._center(""))  # Blank line separator
            for line in self._word_wrap(status_msg):
                all_content.append(self._center(line))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── tools_calc_final_word_screen ────────────────────────────────

    def _render_tools_calc_final_word(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Final Word Calc")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        your_input = state.context.get("your_input_text", "")
        if your_input:
            for line in self._word_wrap(your_input):
                all_content.append(self._center(line))
            
        selected_bits = state.context.get("selected_final_bits", "")
        if selected_bits:
            all_content.append(self._center(selected_bits.ljust(11, "-")))
            
        checksum_label = state.context.get("checksum_label", "Checksum")
        checksum_bits = state.context.get("checksum_bits", "")
        if checksum_bits:
            all_content.append(self._center(""))
            all_content.append(self._center(checksum_label))
            all_content.append(self._center(checksum_bits.rjust(11, "-")))
            
        final_word = state.context.get("final_word_text", "")
        if final_word:
            all_content.append(self._center(""))
            for line in self._word_wrap(final_word):
                all_content.append(self._center(line))
            if selected_bits and checksum_bits:
                prefix = selected_bits[:11 - len(checksum_bits)]
                all_content.append(self._center(prefix + checksum_bits))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── tools_calc_final_word_done_screen ───────────────────────────

    def _render_tools_calc_final_word_done(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Final Word")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        final_word = state.context.get("final_word", "")
        if final_word:
            for line in self._word_wrap(f'Word: "{final_word}"'):
                all_content.append(self._center(line))
        
        fp_label = state.context.get("fingerprint_label", "fingerprint")
        fp = state.context.get("fingerprint", "")
        if fp:
            all_content.append(self._center(f"@ {fp_label}"))
            all_content.append(self._center(fp))
        
        word_len = state.context.get("mnemonic_word_length", "")
        if word_len:
            all_content.append(self._center(f"{word_len}-word mnemonic"))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── tools_address_explorer_address_list_screen ──────────────────

    def _render_tools_address_explorer_list(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Addresses")
        title_line = self._title_row(title, "", state)
        
        addresses = state.context.get("addresses", [])
        start_idx = state.context.get("start_index", 0)
        next_label = state.context.get("next_label", "Next")
        
        all_content = []
        for i, addr in enumerate(addresses):
            num = start_idx + i
            label = f"{num}:{addr}"
            selected = (state.selected_index == i)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        # The next_label acts as a navigable item
        if next_label:
            selected = (state.selected_index == len(addresses))
            all_content.append(self._item_row(next_label, selected=selected, state=state, index=len(addresses)))
        
        return self._do_sliding_window(state, title_line, all_content, 0)

    # ── tools_address_explorer_address_type_screen ──────────────────

    def _render_tools_address_explorer_type(self, state: ScreenState) -> List[str]:
        title = state.context.get("top_nav", {}).get("title", "Address Explorer")
        title_line = self._title_row(title, "", state)
        
        all_content = []
        fp_label = state.context.get("fingerprint_label", "Fingerprint")
        fp = state.context.get("fingerprint", "")
        if fp:
            all_content.append(self._center(f"@ {fp_label}"))
            all_content.append(self._center(fp))
        
        deriv_label = state.context.get("derivation_label", "Derivation")
        deriv = state.context.get("derivation_text", "")
        if deriv:
            all_content.append(self._center(f"⎇ {deriv_label}"))
            for line in self._word_wrap(deriv):
                all_content.append(self._center(line))
                
        wallet_label = state.context.get("wallet_descriptor_label", "")
        wallet_text = state.context.get("wallet_descriptor_text", "")
        if wallet_text:
            if wallet_label:
                for line in self._word_wrap(wallet_label):
                    all_content.append(self._center(line))
            for line in self._word_wrap(wallet_text):
                all_content.append(self._center(line))
        
        all_content = self._pad_text_above_buttons(all_content, len(state.items))
        num_text = len(all_content)
        for i, item in enumerate(state.items):
            label = item.get("label", "") if isinstance(item, dict) else str(item)
            selected = (i == state.selected_index)
            all_content.append(self._item_row(label, selected=selected, state=state, index=i))
        
        return self._do_sliding_window(state, title_line, all_content, num_text)

    # ── Utility helpers ─────────────────────────────────────────────

    def _center(self, text: str) -> str:
        if len(text) > self.cols:
            text = text[: self.cols - 2] + ".."
        return text.center(self.cols)

    def _fixed(self, text: str) -> str:
        """Pad or truncate `text` to exactly `self.cols` characters."""
        if len(text) > self.cols:
            return text[: self.cols]
        return f"{text:<{self.cols}}"

    def _highlight_address(self, address: str) -> str:
        """Generic address formatter."""
        if not address:
            return ""
        if len(address) > 16:
            return " ".join([address[i:i+4] for i in range(0, len(address), 4)])
        return address

    def _highlight_address_verify(self, address: str) -> str:
        """Truncate the middle of the address to match LVGL Verify Address layout."""
        if not address:
            return ""
        if address.startswith("bc1") or address.startswith("tb1") or address.startswith("bcrt1"):
            sep = address.rfind("1") + 2
            prefix = address[:sep]
            rest = address[sep:]
            if len(rest) > 14:
                middle = rest[7:-7]
                if len(middle) > 13:
                    middle = middle[:13] + "..."
                return f"{prefix} [{rest[:7]}] {middle} [{rest[-7:]}]"
        else:
            if len(address) > 15:
                middle = address[8:-7]
                if len(middle) > 13:
                    middle = middle[:13] + "..."
                return f"[{address[:8]}] {middle} [{address[-7:]}]"
        return address

    def _highlight_address_success(self, address: str) -> str:
        """Heavily truncate the address to match LVGL Success Screen layout."""
        if not address:
            return ""
        if address.startswith("bc1") or address.startswith("tb1") or address.startswith("bcrt1"):
            sep = address.rfind("1") + 2
            prefix = address[:sep]
            rest = address[sep:]
            if len(rest) > 10:
                return f"{prefix} [{rest[:7]}]...[{rest[-3:]}]"
        else:
            if len(address) > 11:
                return f"[{address[:8]}]...[{address[-3:]}]"
        return address

    def _pad_rows(self, lines: List[str]) -> List[str]:
        """Ensure we return exactly `self.rows` lines, each `self.cols` wide."""
        while len(lines) < self.rows:
            lines.append(" " * self.cols)
        return lines[: self.rows]

    def _word_wrap(self, text: str) -> List[str]:
        """Simple greedy word-wrap into rows of `self.cols` width, breaking long words if needed."""
        words = text.split()
        lines: List[str] = []
        current = ""
        for word in words:
            if not current:
                if len(word) > self.cols:
                    # Break long word
                    while len(word) > self.cols:
                        lines.append(word[:self.cols])
                        word = word[self.cols:]
                    current = word
                else:
                    current = word
            elif len(current) + 1 + len(word) > self.cols:
                lines.append(current)
                if len(word) > self.cols:
                    # Break long word
                    while len(word) > self.cols:
                        lines.append(word[:self.cols])
                        word = word[self.cols:]
                    current = word
                else:
                    current = word
            else:
                current += " " + word
        if current:
            lines.append(current)
        return lines
