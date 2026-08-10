# SeedSigner Constrained UI Runner

This repository contains the standalone Python runner for constrained hardware interfaces (character LCDs, small OLEDs, and audio buzzers) using the same JSON semantic contract developed for SeedSigner's LVGL architecture.

## Overview

Instead of directly drawing pixels to a 240x240 screen, this engine consumes JSON payloads that describe the *intent* of a screen (e.g., a list of buttons, a warning, or a QR code) and renders them optimally for the connected hardware.

For a comprehensive overview of supported hardware tiers, Airgapped MicroSD workflows, and architectural guidelines, **please refer directly to the [docs/](docs/) folder.**

## Airgapped MicroSD Workflows

Because constrained hardware (like standard I2C LCDs on a Raspberry Pi Zero) typically lacks a camera module and a high-resolution graphical display, standard SeedSigner QR-code data ingestion is impossible. 

This runner solves this by securely routing all data ingress (reading PSBTs) and data egress (writing XPUBs and signed PSBTs) through an attached SPI MicroSD card module. The runner natively intercepts the SeedSigner OS camera/QR hardware calls and seamlessly maps them to file I/O operations, preserving the entire upstream Bitcoin signing logic without modification.

For detailed hardware setup instructions (including the 5MHz SPI overlay), required sudoers permissions, and an automated Python script for generating valid test PSBTs to verify the workflow end-to-end, please see the **[Airgapped MicroSD Workflow Guide](docs/microsd_workflow_guide.md)**.

## Multi-Platform Support (CPython & MicroPython)

The core text rendering engine is **100% pure Python** with zero standard library dependencies (`os.path`, `threading`, `uuid` have been bypassed or polyfilled). 

This allows the UI to run on two vastly different architectures:
1. **Raspberry Pi Zero (CPython)**: Using `smbus2` for I2C and `Pillow`/`luma.oled` for graphical drawing.
2. **ESP32-S3 (MicroPython 1.27)**: Using our native `machine.I2C` LCD driver and the lightweight `framebuf_mpy.py` renderer for OLEDs and E-Paper. No Pillow required.

## Setup

For complete, step-by-step installation instructions and hardware wiring diagrams, please see the **[Constrained UI Build Guide](docs/constrained_build_guide.md)**.

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

## Running Full SeedSigner OS

You can run the full upstream SeedSigner OS application logic using this constrained UI runner as the display driver. This replaces the standard LVGL graphical display with the constrained hardware outputs.

Instead of manually cloning the upstream repository, this runner uses a unified setup script to automatically pull the correct upstream LVGL branch as a git submodule and install all hardware dependencies.

1. Run the unified setup script:
```bash
./setup.sh
```

2. Activate the virtual environment and start the OS:
```bash
source venv/bin/activate
python3 run_seedsigner.py
```

*Note: Configure your `config.json` in the constrained UI runner directory to select your target display hardware (e.g. `oled_128x32`, `lcd_16x2`, etc) before running the OS.*

## Documentation

* **[Constrained UI Build Guide](docs/constrained_build_guide.md)**: The definitive, step-by-step setup guide including hardware configurations, software installation, and Fritzing wiring diagrams for all supported displays.
* **[Airgapped MicroSD Workflow Guide](docs/microsd_workflow_guide.md)**: Architectural rationale for the SPI-based hot-swappable MicroSD data ingress/egress pipeline.
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
