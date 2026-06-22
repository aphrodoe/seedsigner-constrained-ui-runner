import pytest
from src.renderers.text_renderer import TextRenderer
from src.screen_state import ScreenState


# ── helpers ─────────────────────────────────────────────────────────

def _make_state(items, title="Settings", visible_rows=1, screen="button_list_screen"):
    """Build a ScreenState with pre-normalized button_list items."""
    context = {
        "top_nav": {"title": title},
        "button_list": [{"label": i, "value": i} for i in items],
    }
    return ScreenState(screen, context, visible_rows=visible_rows)


# ═══════════════════════════════════════════════════════════════════
#  16 x 2  BLOCK PAGINATION
# ═══════════════════════════════════════════════════════════════════

class TestBlockPagination16x2:
    """Row 0 = title + position, Row 1 = currently selected item."""

    def setup_method(self):
        self.renderer = TextRenderer(rows=2, cols=16)

    def test_basic_render(self):
        state = _make_state(["Language", "Network"], visible_rows=1)
        lines = self.renderer.render(state)

        assert len(lines) == 2
        assert all(len(l) == 16 for l in lines)
        assert "Settings" in lines[0]
        assert "1/2" in lines[0]
        assert "> Language" in lines[1]

    def test_navigate_down(self):
        state = _make_state(["Language", "Network"], visible_rows=1)
        state.move_down()
        lines = self.renderer.render(state)

        assert "2/2" in lines[0]
        assert "> Network" in lines[1]

    def test_long_title_truncation(self):
        state = _make_state(["A"], title="Persistent Settings Screen", visible_rows=1)
        lines = self.renderer.render(state)

        assert len(lines[0]) == 16
        # Title should be truncated, position indicator must be visible
        assert "1/1" in lines[0]

    def test_long_label_marquee(self):
        # We test a selected item to verify marquee slicing
        state = _make_state(["Persistent Settings Override"], visible_rows=1)
        lines = self.renderer.render(state)

        assert len(lines[1]) == 16
        assert lines[1].startswith("> ")
        assert ".." not in lines[1]
        assert "Persistent Set" in lines[1]

    def test_single_item(self):
        state = _make_state(["Only"], visible_rows=1)
        lines = self.renderer.render(state)

        assert "1/1" in lines[0]
        assert "> Only" in lines[1]

    def test_empty_list(self):
        state = _make_state([], visible_rows=1)
        lines = self.renderer.render(state)

        assert len(lines) == 2
        # No position indicator for empty list
        assert "/" not in lines[0]

    def test_tuple_items(self):
        """Items with differing label/value should show 'label: value'."""
        context = {
            "top_nav": {"title": "Menu"},
            "button_list": [{"label": "Dog", "value": "dog_val"}],
        }
        state = ScreenState("button_list_screen", context, visible_rows=1)
        lines = self.renderer.render(state)

        assert "> Dog: dog_val" in lines[1]


# ═══════════════════════════════════════════════════════════════════
#  20 x 4  SLIDING WINDOW
# ═══════════════════════════════════════════════════════════════════

class TestSlidingWindow20x4:
    """Row 0 = title, Rows 1-3 = visible window with '>' cursor."""

    def setup_method(self):
        self.renderer = TextRenderer(rows=4, cols=20)

    def test_basic_render(self):
        state = _make_state(
            ["Language", "Network", "Camera", "Display"],
            visible_rows=3,
        )
        lines = self.renderer.render(state)

        assert len(lines) == 4
        assert all(len(l) == 20 for l in lines)
        assert "Settings" in lines[0]
        assert "> Language" in lines[1]
        assert "  Network" in lines[2]
        assert "  Camera" in lines[3]

    def test_scroll_down(self):
        items = ["Language", "Network", "Camera", "Display", "Security"]
        state = _make_state(items, visible_rows=3)

        # Move to index 3 → window should scroll
        state.move_down()  # 1
        state.move_down()  # 2
        state.move_down()  # 3
        lines = self.renderer.render(state)

        assert "4/5" in lines[0]
        assert "  Network" in lines[1]
        assert "  Camera" in lines[2]
        assert "> Display" in lines[3]

    def test_scroll_back_up(self):
        items = ["Language", "Network", "Camera", "Display", "Security"]
        state = _make_state(items, visible_rows=3)

        # Scroll all the way down, then back up to 0
        for _ in range(4):
            state.move_down()
        for _ in range(4):
            state.move_up()
        lines = self.renderer.render(state)

        assert "1/5" in lines[0]
        assert "> Language" in lines[1]

    def test_fewer_items_than_rows(self):
        """When items < visible rows, remaining rows should be blank."""
        state = _make_state(["A", "B"], visible_rows=3)
        lines = self.renderer.render(state)

        assert len(lines) == 4
        assert "> A" in lines[1]
        assert "  B" in lines[2]
        assert lines[3].strip() == ""

    def test_exact_fit(self):
        """When items == visible rows, no scrolling needed."""
        state = _make_state(["A", "B", "C"], visible_rows=3)
        lines = self.renderer.render(state)

        assert "> A" in lines[1]
        assert "  B" in lines[2]
        assert "  C" in lines[3]

    def test_unselected_long_label_truncation(self):
        """Unselected long items should truncate with .."""
        state = _make_state(["Selected", "Persistent Settings Override"], visible_rows=3)
        lines = self.renderer.render(state)

        assert len(lines[2]) == 20
        assert lines[2].startswith("  ")
        assert ".." in lines[2]


# ═══════════════════════════════════════════════════════════════════
#  ROW WIDTH INVARIANTS
# ═══════════════════════════════════════════════════════════════════

class TestRowWidthInvariants:
    """Every row must be exactly `cols` characters wide, always."""

    @pytest.mark.parametrize("rows,cols", [(2, 16), (4, 20)])
    def test_all_rows_exact_width(self, rows, cols):
        renderer = TextRenderer(rows=rows, cols=cols)
        items = [f"Item {i}" for i in range(10)]
        state = _make_state(items, visible_rows=rows - 1)

        for _ in range(10):
            lines = renderer.render(state)
            assert len(lines) == rows
            for line in lines:
                assert len(line) == cols, f"Row '{line}' is {len(line)} chars, expected {cols}"
            state.move_down()

    @pytest.mark.parametrize("rows,cols", [(2, 16), (4, 20)])
    def test_empty_state_exact_width(self, rows, cols):
        renderer = TextRenderer(rows=rows, cols=cols)
        state = _make_state([], visible_rows=rows - 1)
        lines = renderer.render(state)

        assert len(lines) == rows
        for line in lines:
            assert len(line) == cols


# ═══════════════════════════════════════════════════════════════════
#  MAIN MENU + STATUS SCREENS
# ═══════════════════════════════════════════════════════════════════

class TestMainMenuRenderer:
    def _menu_context(self):
        return {
            "button_grid": [
                {"label": "Scan", "value": "Scan"},
                {"label": "Seeds", "value": "Seeds"},
                {"label": "Settings", "value": "Settings"},
                {"label": "Tools", "value": "Tools"},
            ]
        }

    def test_20x4_numbered_list(self):
        state = ScreenState("main_menu_screen", self._menu_context(), visible_rows=3)
        renderer = TextRenderer(rows=4, cols=20)
        lines = renderer.render(state)

        assert "SeedSigner" in lines[0]
        assert ">1.Scan" in lines[1]
        assert " 2.Seeds" in lines[2]

    def test_16x2_block_pagination(self):
        state = ScreenState("main_menu_screen", self._menu_context(), visible_rows=1)
        renderer = TextRenderer(rows=2, cols=16)
        lines = renderer.render(state)

        assert "SeedSigner" in lines[0]
        assert "1/4" in lines[0]
        assert "> 1.Scan" in lines[1]

    def test_16x2_scroll_down(self):
        state = ScreenState("main_menu_screen", self._menu_context(), visible_rows=1)
        renderer = TextRenderer(rows=2, cols=16)

        state.move_down()
        lines = renderer.render(state)

        assert "2/4" in lines[0]
        assert "> 2.Seeds" in lines[1]


class TestStatusRenderer:
    def test_success_screen(self):
        context = {
            "top_nav": {"title": "Backup Verified"},
            "status_type": "success",
            "status_headline": "Success!",
            "text": "Done.",
            "button_list": [{"label": "OK", "value": "OK"}]
        }
        state = ScreenState("large_icon_status_screen", context, visible_rows=1)
        renderer = TextRenderer(rows=4, cols=20)
        lines = renderer.render(state)
        
        assert "Backup Verified" in lines[0]
        assert "✓" in lines[1]
        assert "Success!" in lines[1]
        assert "[ OK ]" in lines[3]

    def test_warning_screen(self):
        context = {
            "top_nav": {"title": "Privacy Leak!"},
            "status_type": "warning",
            "status_headline": "Warning!",
            "text": "Data exposed.",
            "warning_edges": True
        }
        state = ScreenState("large_icon_status_screen", context, visible_rows=1)
        renderer = TextRenderer(rows=4, cols=20)
        lines = renderer.render(state)
        
        assert "Privacy Leak!" in lines[0]
        assert "⚠" in lines[1]
        assert "Warning!" in lines[1]
        assert lines[2].startswith("!") and lines[2].endswith("!")

    def test_dire_warning_screen(self):
        context = {
            "top_nav": {"title": "DANGER"},
            "status_type": "dire_warning",
            "status_headline": "Stop!",
            "text": "Funds will be lost.",
            "warning_edges": True
        }
        state = ScreenState("large_icon_status_screen", context, visible_rows=1)
        renderer = TextRenderer(rows=4, cols=20)
        lines = renderer.render(state)
        
        assert "DANGER" in lines[0]
        assert "‼" in lines[1]
        assert "Stop!" in lines[1]
        assert lines[2].startswith("!") and lines[2].endswith("!")

    def test_error_screen(self):
        context = {
            "top_nav": {"title": "Error"},
            "status_type": "error",
            "status_headline": "Failed to Sign",
            "text": "Invalid PSBT.",
            "warning_edges": False
        }
        state = ScreenState("large_icon_status_screen", context, visible_rows=1)
        renderer = TextRenderer(rows=4, cols=20)
        lines = renderer.render(state)
        
        assert "Error" in lines[0]
        assert "✕" in lines[1]
        assert "Failed to Sign" in lines[1]
        assert not lines[1].startswith("!")

# ═══════════════════════════════════════════════════════════════════
#  KEYBOARD SCREEN
# ═══════════════════════════════════════════════════════════════════

class TestKeyboardRenderer:
    def setup_method(self):
        self.renderer_16x2 = TextRenderer(rows=2, cols=16)
        self.renderer_20x4 = TextRenderer(rows=4, cols=20)

    def test_basic_keyboard_render(self):
        context = {
            "top_nav": {"title": "Dice Roll"},
            "charset_modes": {"dice": "123456"},
            "initial_mode": "dice",
            "initial_text": "123"
        }
        state = ScreenState("tools_dice_entropy_entry_screen", context, visible_rows=1)
        
        # 16x2
        lines = self.renderer_16x2.render(state)
        assert len(lines) == 2
        assert "Dice Roll" in lines[0]
        # Text "123" + cursor "[1]" -> "123[1]" padded to 16
        assert "123[1]          " == lines[1]
        
        # 20x4
        lines = self.renderer_20x4.render(state)
        assert len(lines) == 4
        assert "Dice Roll" in lines[0]
        # 20 cols minus " (dice)" (7 chars) = 13 chars for text
        assert "123[1]        (dice)" == lines[1]

    def test_keyboard_input_overflow(self):
        context = {
            "top_nav": {"title": "Derivation"},
            "charset_modes": {"path": "m/0123456789'"},
            "initial_mode": "path",
            "initial_text": "m/84'/0'/0'/0/"
        }
        state = ScreenState("seed_export_xpub_custom_derivation_screen", context, visible_rows=1)
        
        lines = self.renderer_16x2.render(state)
        # 16 cols. "m/84'/0'/0'/0/" + "[m]" = 17 chars.
        # It should truncate the left side: "..4'/0'/0'/0/[m]"
        assert ".." in lines[1]
        assert "[m]" in lines[1]
        assert len(lines[1]) == 16

    def test_coin_flip_render(self):
        context = {
            "top_nav": {"title": "Coin Flip"},
            "charset_modes": {"coin": "10"},
            "initial_mode": "coin",
            "initial_text": ""
        }
        state = ScreenState("tools_coin_flip_entry_screen", context, visible_rows=1)
        lines = self.renderer_16x2.render(state)
        assert len(lines) == 2
        assert "Coin Flip" in lines[0]
        assert "[1]             " == lines[1]

    def test_bip85_render(self):
        context = {
            "top_nav": {"title": "BIP85 Index"},
            "charset_modes": {"digits": "0123456789"},
            "initial_mode": "digits",
            "initial_text": "0"
        }
        state = ScreenState("seed_bip85_select_child_index_screen", context, visible_rows=1)
        lines = self.renderer_16x2.render(state)
        assert len(lines) == 2
        assert "BIP85 Index" in lines[0]
        assert "0[0]            " == lines[1]
