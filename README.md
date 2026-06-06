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
