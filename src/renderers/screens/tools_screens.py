from typing import List
from src.screen_state import ScreenState

class ToolsScreensMixin:
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

