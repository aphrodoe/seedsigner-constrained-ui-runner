#!/usr/bin/env python3
"""
Interactive Hardware Tester

A hardware-agnostic tool for testing the full SeedSigner constrained UI
on any supported physical display. Supports real-time scrolling, marquee
animations, and scenario navigation — a 1:1 match with dual_runner.py.

Usage:
    ./tools/interactive_hardware_test.py --display oled
    ./tools/interactive_hardware_test.py --display lcd16x2
    ./tools/interactive_hardware_test.py --display lcd20x4
    ./tools/interactive_hardware_test.py --display epaper
"""
import os
import sys
import tty
import termios
import select
import argparse
import traceback
import json

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.json_parser import JSONParser
from src.screen_state import ScreenState, ScreenType
from src.renderers.text_renderer import TextRenderer


def get_key_timeout(timeout=0.1):
    """Non-blocking key reader. Terminal must already be in cbreak mode."""
    r, w, e = select.select([sys.stdin], [], [], timeout)
    if r:
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch += sys.stdin.read(2)
        return ch
    return None


def init_display(display_type):
    """
    Instantiate the hardware display driver and derive text grid dimensions.

    For graphical displays (OLED, E-Paper), cols and rows are dynamically
    computed from pixel dimensions by the driver itself via compute_text_grid().

    For character LCDs, cols and rows are intrinsic hardware properties.

    Returns:
        (display, text_cols, text_rows)
    """
    if display_type == "oled":
        from src.drivers.oled_ssd1306 import OledSSD1306
        display = OledSSD1306(i2c_port=1, i2c_addr=0x3C, width=128, height=32)
        return display, display.cols, display.rows

    elif display_type == "lcd16x2":
        from src.drivers.lcd_i2c import LCDI2C
        try:
            display = LCDI2C(i2c_addr=0x27, bus_num=1, rows=2, cols=16)
        except OSError:
            display = LCDI2C(i2c_addr=0x3F, bus_num=1, rows=2, cols=16)
        return display, display.cols, display.rows

    elif display_type == "lcd20x4":
        from src.drivers.lcd_i2c import LCDI2C
        try:
            display = LCDI2C(i2c_addr=0x3F, bus_num=1, rows=4, cols=20)
        except OSError:
            display = LCDI2C(i2c_addr=0x27, bus_num=1, rows=4, cols=20)
        return display, display.cols, display.rows

    elif display_type == "epaper":
        from src.drivers.epaper_waveshare import EpaperWaveshare
        display = EpaperWaveshare()
        return display, display.cols, display.rows

    raise ValueError(f"Unknown display type: {display_type}")


def load_scenarios():
    """Load scenarios from the canonical path (matching dual_runner.py)."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # EXACT path used by dual_runner.py to ensure 1:1 similarity
    primary_scenarios = os.path.abspath(
        os.path.join(base_dir, '../seedsigner-c-modules/tools/scenarios/scenarios.json'))
    if os.path.exists(primary_scenarios):
        parser = JSONParser(primary_scenarios)
    else:
        parser = JSONParser(os.path.join(base_dir, 'scenarios/scenarios.json'))

    synth_path = os.path.abspath(
        os.path.join(base_dir, '../seedsigner-c-modules/tools/scenarios/synthetic_screens.json'))
    if not os.path.exists(synth_path):
        synth_path = os.path.join(base_dir, 'scenarios/synthetic_screens.json')

    if os.path.exists(synth_path):
        with open(synth_path, 'r') as f:
            parser.scenarios.update(json.load(f))

    return parser


def main():
    ap = argparse.ArgumentParser(description="Interactive Hardware Tester")
    ap.add_argument("--display",
                    choices=["oled", "lcd16x2", "lcd20x4", "epaper"],
                    default="oled",
                    help="Target hardware display")
    args = ap.parse_args()

    display_type = args.display
    print(f"Initializing {display_type.upper()}...")

    try:
        display, text_cols, text_rows = init_display(display_type)
    except Exception as e:
        print(f"Failed to init {display_type.upper()}: {e}")
        traceback.print_exc()
        return

    print(f"Display ready: {text_cols} cols × {text_rows} rows")
    print("=" * 40)
    print(f"Interactive Hardware Tester ({display_type.upper()})")
    print("Use W/S or UP/DOWN arrows to scroll.")
    print("Press N or ENTER for next screen.")
    print("Press Q to quit.")
    print("=" * 40)

    parser = load_scenarios()
    renderer = TextRenderer(rows=text_rows, cols=text_cols)

    # Pre-compute total screen count for progress tracking
    all_screens = []
    for s_name, s_def in parser.scenarios.items():
        variations = [None] + [v.get("name") for v in s_def.get("variations", [])]
        for v_name in variations:
            all_screens.append((s_name, v_name))
    total_screens = len(all_screens)

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setcbreak(sys.stdin.fileno())
        
        for screen_idx, (s_name, v_name) in enumerate(all_screens, 1):
            s_def = parser.scenarios[s_name]
            ctx = parser.get_scenario_context(s_name, v_name)
            state = ScreenState(s_name, ctx, visible_rows=text_rows - 1)

            # Build a human-readable label for the current variation
            variation_label = f" ({v_name})" if v_name else " (default)"
            progress = f"[{screen_idx}/{total_screens}]"

            quit_all = False
            force_render = True
            tick_count = 0
            while True:
                try:
                    # 1. Read input FIRST with a short timeout for maximum responsiveness
                    key = get_key_timeout(0.1)
                    if key:
                        if state.screen_type.name == "TOAST_OVERLAY":
                            bg_ctx = state.context.get("background", {})
                            state.context.update(bg_ctx)
                            if bg_ctx.get("top_nav", {}).get("title") == "Home":
                                state.screen_type = ScreenType.MAIN_MENU
                            else:
                                state.screen_type = ScreenType.BUTTON_LIST
                            force_render = True
                            continue  # Consume the keypress to dismiss the toast

                        if key in ['w', '\x1b[A']:  # UP
                            if state.move_up():
                                force_render = True
                        elif key in ['s', '\x1b[B']:  # DOWN
                            if state.move_down():
                                force_render = True
                        elif key in ['a', '\x1b[D']:  # LEFT
                            if state.move_left():
                                force_render = True
                        elif key in ['d', '\x1b[C']:  # RIGHT
                            if state.move_right():
                                force_render = True
                        elif key in ['\r', '\n', ' ']: # ENTER / SPACE (Interact)
                            action = state.on_enter()
                            if action == "UPDATE":
                                force_render = True
                            elif action == "SUBMIT":
                                break # Move to next scenario
                        elif key in ['n', 'N']:  # NEXT SCENARIO
                            break
                        elif key in ['q', 'Q']:  # QUIT
                            quit_all = True
                            break

                    # 2. Advance time tracker
                    tick_count += 1

                    # 3. Render only when needed:
                    #    - Immediately on user input (force_render)
                    #    - Every tick (~100ms) for smooth marquee animation
                    if force_render or tick_count >= 1:
                        if not force_render:
                            # Only advance the marquee state when we're actually going to render it
                            # This fixes jumpy animations that occur when ticks outpace renders
                            state.tick()

                        tick_count = 0
                        lines = renderer.render(state)
                        display.write_lines(lines)

                        # Mirror to SSH terminal
                        print("\r\033[H\033[J", end="")  # clear screen with carriage return
                        print(f"{progress} {s_name}{variation_label}\r")
                        print(f"--- {display_type.upper()} [{text_cols}x{text_rows}] ---\r")
                        for line in lines[:text_rows]:
                            print(f"│{line}│\r")
                        print("-" * (text_cols + 2) + "\r")
                        print("W/S/A/D/Arrows: Scroll/Type | SPACE/ENTER: Select | N: Next | Q: Quit\r")

                        force_render = False

                except Exception as e:
                    print(f"Render error: {e}")
                    traceback.print_exc()
                    break

            if quit_all:
                display.clear()
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    main()
