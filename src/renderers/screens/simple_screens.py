from typing import List
from src.screen_state import ScreenState

class SimpleScreensMixin:
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

