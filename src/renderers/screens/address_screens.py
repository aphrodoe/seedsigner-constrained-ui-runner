from typing import List
from src.screen_state import ScreenState

class AddressScreensMixin:
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

