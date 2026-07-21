from typing import List
from src.screen_state import ScreenState

class SeedScreensMixin:
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

