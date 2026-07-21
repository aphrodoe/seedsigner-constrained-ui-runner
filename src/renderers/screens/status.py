from typing import List
from src.screen_state import ScreenState

class StatusMixin:
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

