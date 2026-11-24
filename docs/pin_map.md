# Pin map

Which GPIO does what on each ESP32 board. The S2 Mini map is the carrier board's:
the schematic is drawn from it. The button maps are in the bridge
(`_BUTTON_PINS` in `src/constrained_text_screens.py`), which picks one by the chip it
runs on. Buttons are active-low with internal pull-ups: one side to the GPIO, the
other to GND.

## ESP32-S2 Mini (the carrier)

The LOLIN S2 Mini breaks out 27 GPIOs: 1–18, 21 and 33–40. GPIO 15 also drives the
on-board LED, so it's left unused. GPIO 0 (BOOT button) and 19/20 (native USB) aren't
on the headers.

| Function | GPIO | | Function | GPIO |
|---|---|---|---|---|
| UP | 4 | | I2C SDA | 8 |
| DOWN | 5 | | I2C SCL | 9 |
| LEFT | 6 | | SPI SCK | 36 |
| RIGHT | 7 | | SPI MOSI | 35 |
| ENTER (joystick press) | 10 | | SPI MISO | 37 |
| KEY1 (back) | 1 | | MicroSD CS | 34 |
| KEY2 (back) | 2 | | Display CS | 38 |
| KEY3 (not used yet) | 3 | | Display DC | 39 |
| | | | Display RST | 40 |
| | | | Display BUSY (e-paper) | 33 |

Spare: 11, 12, 13, 14, 16, 17, 18, 21.

The same pins by header position, USB-C at the bottom, viewed from the top:

| Left outer | Left inner | | Right inner | Right outer |
|---|---|---|---|---|
| EN | 1 KEY1 | | 40 Disp RST | 39 Disp DC |
| 3 KEY3 | 2 KEY2 | | 38 Disp CS | 37 MISO |
| 5 DOWN | 4 UP | | 36 SCK | 35 MOSI |
| 7 RIGHT | 6 LEFT | | 34 SD CS | 33 Disp BUSY |
| 9 SCL | 8 SDA | | 21 | 18 |
| 11 | 10 ENTER | | 17 | 16 |
| 12 | 13 | | GND | GND |
| 3V3 | 14 | | 15 (LED) | VBUS (5 V) |

So the left header carries the buttons and I2C, and the right header carries the SPI
bus. Each group's traces leave the module on its own side.

Why these pins:
- **UP/DOWN/LEFT/RIGHT on 4–7, as on the S3 and C3**, so a breadboard wired for one
  chip works on the others.
- **I2C on 8/9**, as in all three firmware board files. LOLIN's own default (33/35)
  is overridden in `firmware/boards/SEEDSIGNER_S2_MINI/mpconfigboard.h`.
- **SPI on 34–37**, the S2's FSPI IO-MUX pins (CS0, D, CLK, Q). They run SPI at
  full speed without going through the GPIO matrix. Check this against the ESP32-S2
  datasheet's IO MUX table in the schematic review. If it's wrong, nothing breaks:
  any GPIO can carry SPI through the matrix at MicroSD speeds.
- **No strapping pins.** The S2's are 0, 45 and 46, and none are on the headers.
- **39 and 40 are JTAG pins** (MTCK, MTDO) until the firmware sets them as GPIO.
  Display DC and RST are outputs, so a glitch on them during boot is harmless.

## ESP32-C3 SuperMini

It breaks out 0–10, 20 and 21. GPIO 15 doesn't exist, so ENTER is on 10. GPIO 2, 8
and 9 are strapping pins. 8 and 9 still carry I2C, because the bus pull-ups hold them
high at boot. 2 is left unused, since a button held down at boot would stop the chip
from starting.

| UP | DOWN | LEFT | RIGHT | ENTER | KEY1 | SDA | SCL |
|---|---|---|---|---|---|---|---|
| 4 | 5 | 6 | 7 | 10 | 1 | 8 | 9 |

It has I2C only: there aren't enough pins left for the SPI display header.

## ESP32-S3 devkit

These are the pins the breadboard already uses, plus KEY1. GPIO 35–37 belong to the
octal PSRAM on the N16R8.

| UP | DOWN | LEFT | RIGHT | ENTER | KEY1 | SDA | SCL |
|---|---|---|---|---|---|---|---|
| 4 | 5 | 6 | 7 | 15 | 16 | 8 | 9 |

## Status

- **Buttons:** done in the bridge for all three chips. They haven't been run on real
  hardware with this change yet.
- **SPI display and MicroSD on the ESP32:** pins assigned, no code yet. On the ESP32
  the app asks the bridge (`sd_ensure`, `sd_live`, `sd_poll`) to mount the card, and
  our bridge doesn't provide those yet, so the app sees no card. On the S2 this will
  be `machine.SDCard(slot=2, sck=36, mosi=35, miso=37, cs=34)`. The S2 has no SDMMC
  host, so SPI mode is the only option.

## Open for the schematic review

- **Display header voltage: 3.3 V.** The bench 20×4 LCD and its backpack run at 3.3 V
  (contrast trimmer turned well down), and so do the OLEDs. Don't feed the header from
  VBUS: the backpack pulls SDA and SCL up to its own VCC, which would put 5 V on GPIO 8
  and 9, and they aren't 5 V tolerant.
- **I2C header pin order.** SSD1306 modules ship as both GND-VCC-SCL-SDA and
  VCC-GND-SCL-SDA. Plan: label both on the silkscreen (#10), with GND-VCC-SCL-SDA as
  the default.
- **SPI display header:** in Waveshare's e-paper order, VCC GND DIN CLK CS DC RST BUSY.
