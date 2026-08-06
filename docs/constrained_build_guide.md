# Constrained UI Build & Deployment Guide

This guide covers how to deploy the constrained UI text engine to physical hardware. Our architecture supports two distinct platforms: the **Raspberry Pi Zero** (running Linux/CPython) and the **ESP32-S3** (running MicroPython 1.27).

---

## 1. Raspberry Pi Zero (CPython)

The Pi Zero is the standard SeedSigner target. We run the text UI engine directly in CPython using standard Linux I2C/SPI interfaces.

### 1.1 Requirements
- Raspberry Pi Zero (v1.3 or W)
- MicroSD Card with Bookworm Lite or Pi OS
- SSH Access enabled
- Connected Display (16x2 LCD, SSD1306 OLED, or Waveshare E-Paper)
- Passive Buzzer (optional, for audio feedback)

### 1.2 Software Setup
1. Clone this repository onto your Pi.
2. Create a virtual environment and install requirements:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Enable I2C and SPI via `sudo raspi-config` (Interfacing Options).

### 1.3 Hardware Testing
You can interact with the engine immediately using the hardware tester tool. This script dynamically pulls the exact dimensions of your display (e.g., 20x4 or 128x32) and starts a navigable UI session.

```bash
# Test on 128x32 OLED (SSD1306)
./tools/interactive_hardware_test.py --display oled

# Test on 16x2 Character LCD
./tools/interactive_hardware_test.py --display lcd16x2
```

---

## 2. ESP32-S3 (MicroPython)

Because our rendering engine separates state logic from hardware I/O, the entire text algorithm runs perfectly on MicroPython 1.27.

### 2.1 Requirements
- ESP32-S3 Development Board
- Display (I2C LCD or I2C OLED)
- 5x Tactile Push Buttons (for directional navigation)
- `esptool` and `mpremote` installed on your host machine.

### 2.2 Flashing MicroPython
Download the latest MicroPython 1.27 firmware for your ESP32-S3 board.

1. Erase the flash:
   ```bash
   esptool.py --chip esp32s3 --port /dev/ttyUSB0 erase_flash
   ```
2. Write the firmware:
   ```bash
   esptool.py --chip esp32s3 --port /dev/ttyUSB0 write_flash -z 0 microPython-1.27-esp32s3.bin
   ```

### 2.3 Uploading the Codebase
We use `mpremote` to copy our pure-Python logic and MicroPython-specific hardware drivers to the ESP32.

```bash
# Copy the source code and scenario JSON
mpremote fs cp -r src/ :
mpremote fs cp -r scenarios/ :

# Copy the MicroPython entrypoint to the root so it runs on boot
mpremote fs cp mpy_main.py :main.py
```

### 2.4 Wiring & Pinout
By default, `mpy_main.py` expects the following wiring. (You can change these in the script).

**I2C Display (OLED or LCD):**
- **VCC:** 3.3V or 5V (Check your display specs)
- **GND:** GND
- **SDA:** GPIO 8
- **SCL:** GPIO 9

**Navigation Buttons (Wired to GND):**
- **UP:** GPIO 4
- **DOWN:** GPIO 5
- **LEFT:** GPIO 6
- **RIGHT:** GPIO 7
- **ENTER:** GPIO 15

### 2.5 MicroPython Native Drivers
To avoid CPython dependencies like `Pillow` or `smbus2`, we use custom native drivers on the ESP32:
- `src/drivers/lcd_i2c_mpy.py` uses `machine.I2C` for character LCDs.
- `src/drivers/framebuf_mpy.py` uses the built-in `framebuf.FrameBuffer` for pixel displays like the SSD1306 OLED, converting complex Unicode icons to ASCII fallbacks automatically.
