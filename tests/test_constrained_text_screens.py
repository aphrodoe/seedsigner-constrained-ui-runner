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


class FakeLineDriver:
    """A bare line driver, like MicroPython's framebuf driver: write_lines() only."""

    rows, cols = 8, 16

    def __init__(self):
        self.frames = []

    def write_lines(self, lines):
        self.frames.append(list(lines))


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


@pytest.mark.parametrize("label", ["Backup seed", "Back to Main Menu", "Cancel"])
def test_buttons_named_like_back_are_still_buttons(bridge, label):
    # Real upstream labels. The View acts on the index it gets back: "Back to Main
    # Menu" routes to the main menu, which RET_CODE__BACK_BUTTON would not do.
    bridge.button_list_screen({"button_list": ["Export Xpub", label]})
    assert press(bridge, "DOWN", "ENTER") == ("button_selected", 1, label)


def test_back_key_rides_the_index_slot(bridge):
    bridge.button_list_screen({"top_nav": {"show_back_button": True}, "button_list": ["A"]})
    assert press(bridge, "KEY1") == ("button_selected", RET_CODE__BACK_BUTTON, "topnav_back")


def test_back_key_is_ignored_on_the_main_menu(bridge):
    bridge.main_menu_screen({"button_list": ["Scan", "Seeds"]})
    assert press(bridge, "KEY1") is None


def test_back_key_is_ignored_when_the_view_hides_back(bridge):
    # The runner nests show_back_button inside top_nav (seedsigner.gui.lvgl_config.top_nav).
    bridge.button_list_screen({"top_nav": {"show_back_button": False}, "button_list": ["OK"]})
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


# --- display backends --------------------------------------------------------

def test_a_bare_line_driver_gets_full_frames(bridge, monkeypatch):
    # MicroPython's framebuf driver has write_lines() and a rows x cols grid, no render().
    driver = FakeLineDriver()
    monkeypatch.setattr(bridge, "_renderer", driver)
    bridge.button_list_screen({"top_nav": {"title": "Seeds"}, "button_list": ["A", "B"]})
    press(bridge, "DOWN")
    assert len(driver.frames) == 2  # once when built, again on navigation
    for frame in driver.frames:
        assert len(frame) == driver.rows
        assert all(len(line) == driver.cols for line in frame)


# --- MicroSD interceptors: the runner's camera scan and QR display, rerouted to the card ---

import base64
import sys
import types

from src.hardware.microsd import MicroSDManager


class Recorded:
    def __init__(self, *args):
        self.args = args


class FakeDecoder:
    def __init__(self):
        self.data = []

    def add_data(self, text):
        self.data.append(text)


@pytest.fixture
def sd_bridge(bridge, monkeypatch):
    """The bridge, with the card and seedsigner's ScanResult/build_xpub_data faked."""
    card = {"files": [], "contents": {}, "reads": [], "writes": []}
    monkeypatch.setattr(MicroSDManager, "list_files", classmethod(lambda cls: list(card["files"])))
    monkeypatch.setattr(MicroSDManager, "read_file",
                        classmethod(lambda cls, name: card["reads"].append(name) or card["contents"][name]))
    monkeypatch.setattr(MicroSDManager, "write_file",
                        classmethod(lambda cls, name, data, binary=True: card["writes"].append((name, data))))
    for name, attrs in {
        "seedsigner": {}, "seedsigner.hardware": {}, "seedsigner.models": {},
        "seedsigner.hardware.scan_consumer": {"ScanResult": Recorded},
        "seedsigner.models.encode_qr": {
            "build_xpub_data": lambda seed, derivation, network, sig_type:
                types.SimpleNamespace(xpubstring=f"xpub/{derivation}/{network}")},
    }.items():
        monkeypatch.setitem(sys.modules, name, types.SimpleNamespace(**attrs))
    events = []
    monkeypatch.setattr(bridge, "poll_for_result", lambda: events.pop(0) if events else ("button_selected", 0, "OK"))
    bridge._sd, bridge._events = card, events
    return bridge


def test_scan_with_no_files_shows_error_and_cancels(sd_bridge):
    result = sd_bridge._intercept_run_camera_scan(FakeDecoder())
    assert sd_bridge._renderer.drawn == [ScreenType.LARGE_ICON_STATUS]
    assert result.args[1:4] == (False, True, "cancelled")


def test_scan_lists_card_and_feeds_chosen_text_file(sd_bridge):
    sd_bridge._sd["files"] = ["a.psbt", "b.txt"]
    sd_bridge._sd["contents"]["b.txt"] = b"  cHNidP8B...\n"
    sd_bridge._events.append(("button_selected", 1, "b.txt"))
    decoder = FakeDecoder()
    result = sd_bridge._intercept_run_camera_scan(decoder)
    assert sd_bridge._current_state.screen_type == ScreenType.BUTTON_LIST
    assert sd_bridge._sd["reads"] == ["b.txt"]
    assert decoder.data == ["cHNidP8B..."]
    assert result.args[1:4] == (True, False, "complete")


def test_scan_base64s_a_binary_psbt(sd_bridge):
    raw = b"psbt\xff" + bytes(range(64))
    sd_bridge._sd["files"] = ["tx.psbt"]
    sd_bridge._sd["contents"]["tx.psbt"] = raw
    decoder = FakeDecoder()
    sd_bridge._intercept_run_camera_scan(decoder)
    assert decoder.data == [base64.b64encode(raw).decode()]


def test_scan_back_cancels_without_reading(sd_bridge):
    sd_bridge._sd["files"] = ["tx.psbt"]
    sd_bridge._events.append(("button_selected", RET_CODE__BACK_BUTTON, "back"))
    result = sd_bridge._intercept_run_camera_scan(FakeDecoder())
    assert sd_bridge._sd["reads"] == []
    assert result.args[1:4] == (False, True, "cancelled")


def test_display_writes_signed_psbt(sd_bridge):
    encoder = types.SimpleNamespace(psbt=types.SimpleNamespace(serialize=lambda: b"signed"))
    sd_bridge._intercept_run_qr_display_screen(encoder)
    assert sd_bridge._sd["writes"] == [("signed_tx.psbt", b"signed")]
    assert sd_bridge._current_state.screen_type == ScreenType.LARGE_ICON_STATUS


def test_display_writes_xpub(sd_bridge):
    encoder = types.SimpleNamespace(derivation="m/84h/0h/0h", network="main", sig_type="ss")
    sd_bridge._intercept_run_qr_display_screen(encoder)
    assert sd_bridge._sd["writes"] == [("xpub.txt", b"xpub/m/84h/0h/0h/main")]


# --- MicroPython display selection: /config.json, same format as the Pi's ---

import json


class FakeI2C:
    def __init__(self, *args, **kwargs):
        self.writes = []

    def writeto(self, addr, data):
        self.writes.append(addr)


class FakeSSD1306:
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width, self.height, self.addr = width, height, addr

    def fill(self, c): pass
    def text(self, s, x, y, c): pass
    def show(self): pass


@pytest.fixture
def mpy(monkeypatch, tmp_path):
    machine = types.SimpleNamespace(I2C=FakeI2C, Pin=lambda n, *a, **k: n)
    monkeypatch.setitem(sys.modules, "machine", machine)
    monkeypatch.setitem(sys.modules, "ssd1306", types.SimpleNamespace(SSD1306_I2C=FakeSSD1306))
    monkeypatch.setattr(cts, "machine", machine, raising=False)
    monkeypatch.chdir(tmp_path)

    def with_config(display):
        (tmp_path / "config.json").write_text(json.dumps({"display": display}))
        return cts._mpy_display()
    return with_config


def test_mpy_defaults_to_the_20x4_lcd_without_a_config(mpy, tmp_path):
    display = cts._mpy_display()
    assert (display.rows, display.cols, display.i2c_addr) == (4, 20, 0x27)


@pytest.mark.parametrize("kind, rows, cols", [("lcd_20x4", 4, 20), ("lcd_16x2", 2, 16)])
def test_mpy_lcd_from_config(mpy, kind, rows, cols):
    display = mpy({"type": kind, "i2c_address": "0x3F"})
    assert (display.rows, display.cols, display.i2c_addr) == (rows, cols, 0x3F)


def test_mpy_oled_128x64(mpy):
    display = mpy({"type": "oled_128x64"})
    assert (display.rows, display.cols, display.display.addr) == (8, 16, 0x3C)


def test_mpy_oled_128x32_keeps_three_rows_like_the_pi(mpy):
    """The bezel on generic 128x32 modules hides the 4th text row; display_manager
    limits it to 3 on the Pi, and the device must lay out the same screens."""
    display = mpy({"type": "oled_128x32", "i2c_address": "0x3C"})
    assert (display.rows, display.cols, display.display.height) == (3, 16, 32)


def test_mpy_unknown_display_type_fails_loudly(mpy):
    with pytest.raises(ValueError):
        mpy({"type": "epaper_200x200"})


def test_mpy_selected_display_draws_through_the_bridge(mpy, bridge):
    bridge._renderer = mpy({"type": "lcd_20x4"})
    bridge.main_menu_screen({"top_nav": {"title": "Home"}, "button_list": ["Scan", "Seeds", "Tools", "Settings"]})
    assert bridge._renderer.i2c.writes  # the frame went out over I2C
