# SeedSigner Constrained UI Runner

This repository contains the standalone Python runner for constrained hardware interfaces (character LCDs, small OLEDs, and audio buzzers) using the same JSON semantic contract developed for SeedSigner's LVGL architecture.

## Overview

Instead of directly drawing pixels to a 240x240 screen, this engine consumes JSON payloads that describe the *intent* of a screen (e.g., a list of buttons, a warning, or a QR code) and renders them optimally for the connected hardware.

Supported outputs:
* Desktop Terminal (Simulator)
* 16x2 Character LCD (I2C)
* 20x4 Character LCD (I2C)
* 128x32 OLED (I2C)
* Audio Navigation cues (PWM Buzzer)

## Setup

```bash
pip install -r requirements.txt
```

## Running the Simulator

You can test the UI on your laptop without any hardware connected using the built-in terminal simulator. Use the **Up/Down arrow keys** to navigate, **Enter** to select, and **q** to quit.

**Test 1: A simple short menu**
```bash
python3 -m src.main --display simulator --scenario button_list_screen
```

**Test 2: A long menu with scrolling**
```bash
python3 -m src.main --display simulator --scenario button_list_screen --variation scroll_many
```

**Test 3: The Main Menu Grid**
```bash
python3 -m src.main --display simulator --scenario main_menu_screen
```

## LCD Simulators

These simulate the exact character output that would appear on a physical LCD:

**16x2 LCD (Block Pagination)** — shows one item at a time:
```bash
python3 -m src.main --display lcd_16x2_sim --scenario button_list_screen
```

**20x4 LCD (Sliding Window)** — shows a 3-item scrollable window:
```bash
python3 -m src.main --display lcd_20x4_sim --scenario button_list_screen --variation scroll_many
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

For rapid design validation, you can run the side-by-side interactive Tkinter application. This loads the generated LVGL screenshots from the upstream repository alongside the live `16x2` and `20x4` simulators.

```bash
python3 tools/dual_runner.py
```
*Note: You can pass `--lvgl-dir` to point to custom screenshot directories.*

* Keyboard controls: `W`, `A`, `S`, `D` to navigate, `Space` to select. 

## Documentation

* **[Text UI Design Guide](docs/text_ui_design_guide.md)**: Rules for block pagination, sliding windows, truncations, and icon mapping.

## Running Tests

```bash
python3 -m pytest tests/ -v
```
