# SeedSigner Constrained UI Runner

This repository contains the standalone Python runner for constrained hardware interfaces (character LCDs, small OLEDs, and audio buzzers) using the same JSON semantic contract developed for SeedSigner's LVGL architecture.

## Overview

Instead of directly drawing pixels to a 240x240 screen, this engine consumes JSON payloads that describe the *intent* of a screen (e.g., a list of buttons, a warning, or a QR code) and renders them optimally for the connected hardware.

As of Week 8, this runner supports **29 unique text-renderable screen types**, covering the entire signing flow (including PSBT details, multisig descriptors, message signing, and complex keyboard entry). 6 screens remain strictly visual-only (QR code display and Camera overlays).

Supported outputs (Categorized by Tier):
* **Tier 0**: 16x2 Character LCD (I2C) - *Tested on generic HD44780 + I2C backpack*
* **Tier 1**: 20x4 Character LCD (I2C) - *Tested on generic HD44780 + I2C backpack*
* **Graphical Pixel Displays**: 128x32 / 128x64 OLED (SSD1306) and 200x200 E-Paper (Waveshare 1.54") — *Dimensions dynamically mapped to text grid via `src/utils/graphics.py`*
* **Audio**: Navigation cues (PWM Buzzer) - *Tested on standard 5V active buzzer*

## Multi-Platform Support (CPython & MicroPython)

The core text rendering engine is **100% pure Python** with zero standard library dependencies (`os.path`, `threading`, `uuid` have been bypassed or polyfilled). 

This allows the UI to run on two vastly different architectures:
1. **Raspberry Pi Zero (CPython)**: Using `smbus2` for I2C and `Pillow`/`luma.oled` for graphical drawing.
2. **ESP32-S3 (MicroPython 1.27)**: Using our native `machine.I2C` LCD driver and the lightweight `framebuf_mpy.py` renderer for OLEDs and E-Paper. No Pillow required.

## Setup

```bash
pip install -r requirements.txt
```

## Terminal Simulators

These simulate the exact character output that would appear on a physical LCD directly in your laptop's terminal without any hardware connected. Use the **Up/Down arrow keys** to navigate, **Enter** to select, and **q** to quit.

**Tier 0: 16x2 LCD (Block Pagination)** — shows one item at a time:
```bash
python3 -m src.main --display lcd_16x2_sim --scenario button_list_screen
```

**Tier 1: 20x4 LCD (Sliding Window)** — shows a 3-item scrollable window:
```bash
python3 -m src.main --display lcd_20x4_sim --scenario button_list_screen --variation scroll_many
```

**Graphical OLED (Dynamic Grid)** — rows and columns computed from pixel dimensions:
```bash
python3 -m src.main --display lcd_16x8_sim --scenario button_list_screen --variation scroll_many
```

**Testing Status Screens (Simulators):**
```bash
python3 -m src.main --display lcd_20x4_sim --scenario large_icon_status_screen --variation warning
```

## Running on Physical Hardware

To run the runner directly on physical I2C LCD displays connected to the Raspberry Pi:

**16x2 Physical LCD:**
```bash
python3 -m src.main --display lcd_16x2 --scenario button_list_screen
```

**20x4 Physical LCD:**
```bash
python3 -m src.main --display lcd_20x4 --scenario large_icon_status_screen --variation dire_warning
```

**Testing Audio (Buzzer):**
```bash
python3 -m src.main --display lcd_16x2 --audio --scenario button_list_screen
```

## Interactive Dual Runner (Developer Tool)

For rapid design validation, you can run the side-by-side interactive Tkinter application. This loads the generated LVGL screenshots from the upstream repository alongside the live `16x2`, `20x4`, `16x8`, and `25x16` text simulators.

```bash
python3 tools/dual_runner.py
```
*Note: You can pass `--lvgl-dir` to point to custom screenshot directories.*

* Keyboard controls: `W`, `A`, `S`, `D` to navigate, `Space` to select. 
* **Side-by-Side vs Isolated Mode**: By default, the Dual Runner renders all display tiers simultaneously. Because it shares a single virtual controller, it prioritizes the scrolling limits of the smallest display (Tier 0). You can use the dropdown menu to isolate a specific tier (e.g., "Tier 3: E-Paper"), which will immediately un-link the shared scroll constraints and allow you to interact with that tier's 1-to-1 native scrolling behavior.

## Interactive Hardware Tester

For testing the full UI experience on physical hardware connected to a Raspberry Pi (e.g., over SSH), use the interactive hardware tester. It supports all display types and dynamically computes the text grid from the hardware's physical dimensions.

```bash
# Test on 128x32 OLED (SSD1306)
./tools/interactive_hardware_test.py --display oled

# Test on 16x2 Character LCD
./tools/interactive_hardware_test.py --display lcd16x2

# Test on 20x4 Character LCD
./tools/interactive_hardware_test.py --display lcd20x4

# Test on Waveshare 1.54" E-Paper
./tools/interactive_hardware_test.py --display epaper
```

* Keyboard controls: `W`/`S` or Arrow keys to scroll, `N`/`Enter` for next screen, `Q` to quit.
* The tool mirrors the current screen to your SSH terminal so you can see what the hardware is rendering.
* Marquee animations run in real-time (non-blocking 300ms tick loop), matching `dual_runner.py`.

## Documentation

* **[Text UI Design Guide](docs/text_ui_design_guide.md)**: Rules for architectural tiers (Tier 0-3), block pagination, sliding windows, and 2D spatial layouts.

## Running Tests

To run the standard unit tests:
```bash
python3 -m pytest tests/test_screen_state.py tests/test_text_renderer.py tests/test_json_parser.py -v
```

To run the automated Golden UI tests (verifies text snapshots across all hardware tiers against `scenarios.json`):
```bash
python3 -m pytest tests/test_all_screens_golden.py
```
*(Append `--update-golden` to overwrite baselines if you make intentional design changes)*

## Hardware Screen Walkthrough (Passive)

To passively walk through all 130+ screen variations on auto-detected hardware (no interactive scrolling):

```bash
./tools/test_all_screens.py
```
*(Press Enter to manually advance through the screens)*

## Architecture: Shared Graphics Utility & Dynamic CGRAM

All graphical display drivers (OLED, E-Paper) delegate text rendering to a shared utility at `src/utils/graphics.py`. This module:

1. **Dynamically measures** the loaded PIL font's ascent and average character width — no hardcoded pixel constants.
2. **Computes the text grid** (`cols`, `rows`, `line_height`) from any pixel resolution via `compute_text_grid(width, height, font)`.
3. **Bundles a Monospace Font**: The repository ships with `DejaVuSansMono.ttf` to guarantee that text alignment, bounded wrapping, and ASCII art render flawlessly on any host OS, bypassing unpredictable system-default fonts.
4. **Renders proportional text** with automatic right-alignment of pagination indicators (e.g., `3/4`) and custom icon bitmap substitution via a single `draw_text_line()` function. It natively draws 8x8 pixel-art versions of all SeedSigner icons (Warning, Dire Warning, Checkmark, etc.) regardless of the host font's capabilities.

For character LCDs (Tier 0 & 1), the engine uses a **Dynamic CGRAM Allocator**:
1. The HD44780 controller only has 8 custom character slots.
2. The `TextRenderer` parses each frame and identifies all unique custom icons requested.
3. The allocator assigns the available 8 slots on-the-fly to the highest-priority icons.
4. Any icons that exceed the 8-slot limit are safely degraded to ASCII equivalents, completely eliminating the hardware bottleneck while preserving the UX.
