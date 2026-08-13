"""
Regression coverage for DisplayManager.create_renderer().

The golden/unit suites build TextRenderer directly and never touch the renderer
factory, so a constructor-signature mismatch between BaseRenderer and its
subclasses can ship unnoticed (it did, in 9f02258). These tests build every
headless-safe simulator renderer through the factory and assert the grid the
BaseRenderer contract promises.
"""
import pytest

from src.display_manager import DisplayManager

# display.type -> (rows, cols)
SIM_TYPES = {
    "lcd_16x2_sim": (2, 16),
    "lcd_20x4_sim": (4, 20),
    "lcd_16x8_sim": (8, 16),
    "lcd_25x16_sim": (16, 25),
}


def _manager_for(display_type):
    dm = DisplayManager("config.json")
    dm.config = {"display": {"type": display_type}}
    return dm


@pytest.mark.parametrize("display_type,expected", SIM_TYPES.items())
def test_create_simulator_renderer(display_type, expected):
    rows, cols = expected
    renderer = _manager_for(display_type).create_renderer()

    assert renderer.rows == rows
    assert renderer.cols == cols
    assert renderer.visible_rows == rows - 1  # row 0 is the title
    assert hasattr(renderer, "render")
    assert renderer.text_renderer.rows == rows
    assert renderer.text_renderer.cols == cols


def test_unknown_display_type_raises():
    with pytest.raises(ValueError):
        _manager_for("does_not_exist").create_renderer()
