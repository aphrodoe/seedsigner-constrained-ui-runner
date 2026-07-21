# SeedSigner Constrained UI Runner

This repository contains the standalone Python runner for constrained hardware interfaces (character LCDs, small OLEDs, and audio buzzers) using the same JSON semantic contract developed for SeedSigner's LVGL architecture.

## Overview

Instead of directly drawing pixels to a 240x240 screen, this engine consumes JSON payloads that describe the *intent* of a screen (e.g., a list of buttons, a warning, or a QR code) and renders them optimally for the connected hardware.

As of Week 8, this runner supports **29 unique text-renderable screen types**, covering the entire signing flow (including PSBT details, multisig descriptors, message signing, and complex keyboard entry). 6 screens remain strictly visual-only (QR code display and Camera overlays).

Supported outputs (Categorized by Tier):
* **Tier 0**: 16x2 Character LCD (I2C) - *Tested on generic HD44780 + I2C backpack*
* **Tier 1**: 20x4 Character LCD (I2C) - *Tested on generic HD44780 + I2C backpack*
* **Tier 2**: 128x64 OLED (via Pixel-to-Text adapter) - *Upcoming Week 9 (ACEBOTT kit)*
* **Tier 3**: 200x200 E-Paper (via Pixel-to-Text adapter) - *Upcoming Week 10 (Waveshare 1.54")*
* **Audio**: Navigation cues (PWM Buzzer) - *Tested on standard 5V active buzzer*

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

**Tier 2: 128x64 OLED (Expansive View)** — shows up to 7 items:
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

## Documentation

* **[Text UI Design Guide](docs/text_ui_design_guide.md)**: Rules for architectural tiers (Tier 0-3), block pagination, sliding windows, and 2D spatial layouts.

## Running Tests

```bash
python3 -m pytest tests/ -v
```
