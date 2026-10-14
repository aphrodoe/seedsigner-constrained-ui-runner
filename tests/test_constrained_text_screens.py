"""Behavioural tests for the integration bridge, src/constrained_text_screens.py.

The bridge is what SeedSigner's View layer talks to: it is imported as
`seedsigner_lvgl_screens`, a builder is called per screen name with a cfg dict,
then the runner polls for result tuples. These tests pin that contract as Keith's
runner (gui/lvgl_screen_runner.py on integration/lvgl-mpy) actually consumes it:
`("button_selected", index, label)`, with back riding the index slot as 1000, and
`("text_entered", -1, text)`. That differs from the older table in
view-to-screen-json-contract.md, which still shows ("topnav_back", -1, ...).

No hardware: a fake renderer records draws, a scripted input yields presses.
"""
import time

import pytest

import src.constrained_text_screens as cts
from src.screen_state import ScreenType

RET_CODE__BACK_BUTTON = 1000  # seedsigner.views.view; the runner returns it unchanged


class FakeRenderer:
    """A full renderer, like every CPython DisplayManager renderer: has .render()."""

    rows, cols = 4, 20

    def __init__(self):
        self.drawn = []

    def render(self, state):
        self.drawn.append(state.screen_type)


class ScriptedInput:
    def __init__(self):
        self.pending = []

    def read(self):
        return self.pending.pop(0) if self.pending else None


class NoKeyboard:
    def read_event(self, timeout=None):
        return None


@pytest.fixture
def bridge(monkeypatch):
    monkeypatch.setattr(cts, "_renderer", FakeRenderer())
    monkeypatch.setattr(cts, "_hardware_input", ScriptedInput())
    monkeypatch.setattr(cts, "_current_state", None)
    monkeypatch.setattr(cts, "_result_queue", [])
    # On CPython, poll_for_result() falls back to a termios keyboard. Keep it inert.
    monkeypatch.setattr(cts.HardwareInput, "_keyboard_hook", NoKeyboard(), raising=False)
    monkeypatch.setattr(cts.time, "sleep", lambda s: None)
    return cts


def press(bridge, *keys):
    """Feed presses one per poll, as the runner's loop does; return the first result."""
    bridge._hardware_input.pending.extend(keys)
    for _ in keys:
        result = bridge.poll_for_result()
        if result is not None:
            return result
    return None


# --- builders ----------------------------------------------------------------

SCREEN_NAMES = sorted(
    v for k, v in vars(ScreenType).items() if not k.startswith("_") and isinstance(v, str)
)


@pytest.mark.parametrize("name", SCREEN_NAMES)
def test_every_screen_type_has_a_builder(bridge, name):
    assert callable(getattr(bridge, name))


def test_a_screen_added_upstream_later_still_resolves(bridge):
    assert callable(bridge.some_future_screen)


def test_non_screen_attributes_raise(bridge):
    with pytest.raises(AttributeError):
        bridge.not_a_screen_thing


def test_builder_returns_immediately_and_draws_once(bridge):
    cfg = {"top_nav": {"title": "Seeds"}, "button_list": ["A", "B"]}
    assert bridge.button_list_screen(cfg) is None
    assert bridge._current_state.screen_type == ScreenType.BUTTON_LIST
    assert bridge._current_state.context is cfg
    assert bridge._renderer.drawn == [ScreenType.BUTTON_LIST]


# --- polling -----------------------------------------------------------------

def test_poll_is_none_before_any_screen(bridge):
    assert bridge.poll_for_result() is None


def test_poll_is_none_while_the_user_has_not_acted(bridge):
    bridge.button_list_screen({"button_list": ["A"]})
    assert bridge.poll_for_result() is None


def test_queued_results_come_first_and_clear_drops_them(bridge):
    bridge._result_queue.extend([("button_selected", 0, "x"), ("button_selected", 1, "y")])
    assert bridge.poll_for_result() == ("button_selected", 0, "x")
    bridge.clear_result_queue()
    assert bridge.poll_for_result() is None


def test_navigation_redraws(bridge):
    bridge.button_list_screen({"button_list": ["A", "B"]})
    press(bridge, "DOWN")
    assert len(bridge._renderer.drawn) == 2


# --- result tuples -----------------------------------------------------------

def test_select_returns_index_and_label(bridge):
    bridge.button_list_screen({"button_list": ["Scan", "Seeds", "Tools"]})
    assert press(bridge, "DOWN", "DOWN", "ENTER") == ("button_selected", 2, "Tools")


def test_object_form_buttons_report_their_label(bridge):
    bridge.button_list_screen({"button_list": [{"label": "Mainnet", "icon": "x"}, "Testnet"]})
    assert press(bridge, "ENTER") == ("button_selected", 0, "Mainnet")


def test_back_key_rides_the_index_slot(bridge):
    bridge.button_list_screen({"top_nav": {"show_back_button": True}, "button_list": ["A"]})
    assert press(bridge, "KEY1") == ("button_selected", RET_CODE__BACK_BUTTON, "topnav_back")


def test_back_key_is_ignored_on_the_main_menu(bridge):
    bridge.main_menu_screen({"button_list": ["Scan", "Seeds"]})
    assert press(bridge, "KEY1") is None


def test_keyboard_submit_returns_the_entered_text(bridge):
    bridge.keyboard_screen({"keys": ["1", "2", "3"], "show_save_button": True})
    # Keys become 1 2 3 [DEL] [OK]: enter 1, step right, enter 2, step to [OK], submit.
    result = press(bridge, "ENTER", "RIGHT", "ENTER", "RIGHT", "RIGHT", "RIGHT", "ENTER")
    assert result == ("text_entered", -1, "12")


def test_any_key_acknowledges_a_screen_without_buttons(bridge):
    bridge.large_icon_status_screen({"status_headline": "Saved"})
    assert press(bridge, "ENTER") == ("button_selected", 0, "OK")


def test_splash_dismisses_itself(bridge):
    bridge.opening_splash_screen({"version": "0.8.7"})
    assert bridge.poll_for_result() is None
    bridge._current_state.start_time = time.time() - 3.0
    assert bridge.poll_for_result() == ("button_selected", 0, "OK")

