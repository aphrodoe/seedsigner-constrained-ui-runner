from typing import List
from src.screen_state import ScreenState

class PSBTMixin:
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

