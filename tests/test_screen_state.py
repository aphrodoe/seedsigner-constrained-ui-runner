import pytest
from src.screen_state import ScreenState, ScreenType

def test_screen_type_parsing():
    assert ScreenType.from_str("button_list_screen") == ScreenType.BUTTON_LIST
    
    with pytest.raises(ValueError):
        ScreenType.from_str("unknown_screen")

def test_initial_state():
    context = {"button_list": [{"label": "A"}, {"label": "B"}]}
    state = ScreenState("button_list_screen", context, visible_rows=2)
    
    assert state.selected_index == 0
    assert state.scroll_offset == 0
    assert len(state.items) == 2

def test_move_down_and_up():
    context = {"button_list": [{"label": "A"}, {"label": "B"}, {"label": "C"}]}
    state = ScreenState("button_list_screen", context, visible_rows=2)
    
    assert state.move_down() is True
    assert state.selected_index == 1
    
    assert state.move_up() is True
    assert state.selected_index == 0

def test_boundaries():
    context = {"button_list": [{"label": "A"}, {"label": "B"}]}
    state = ScreenState("button_list_screen", context, visible_rows=2)
    
    # Cannot move up from 0
    assert state.move_up() is False
    assert state.selected_index == 0
    
    # Move to last
    assert state.move_down() is True
    assert state.selected_index == 1
    
    # Cannot move past last
    assert state.move_down() is False
    assert state.selected_index == 1

def test_scroll_offset_adjustment():
    # 5 items, window of 2
    context = {"button_list": [{"label": str(i)} for i in range(5)]}
    state = ScreenState("button_list_screen", context, visible_rows=2)
    
    assert state.scroll_offset == 0
    
    # Moving down to index 1 doesn't change offset (0, 1 are visible)
    state.move_down()
    assert state.scroll_offset == 0
    
    # Moving down to index 2 forces offset to 1 (1, 2 are visible)
    state.move_down()
    assert state.scroll_offset == 1
    
    # Move to bottom
    state.move_down()
    state.move_down()
    assert state.selected_index == 4
    assert state.scroll_offset == 3  # (3, 4 are visible)
    
    # Move back up to 2 forces offset to 2 (2, 3 are visible)
    state.move_up()
    state.move_up()
    assert state.selected_index == 2
    assert state.scroll_offset == 2

def test_page_up_down():
    # 10 items, window of 3
    context = {"button_list": [{"label": str(i)} for i in range(10)]}
    state = ScreenState("button_list_screen", context, visible_rows=3)
    
    state.page_down()
    assert state.selected_index == 3
    assert state.scroll_offset == 1  # 3 - 3 + 1
    
    state.page_down()
    assert state.selected_index == 6
    assert state.scroll_offset == 4
    
    state.page_up()
    assert state.selected_index == 3
    assert state.scroll_offset == 3  # Moved up to 3, offset becomes 3
