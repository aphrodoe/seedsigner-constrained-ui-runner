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

**Buttons, built either way.** The carrier has a footprint for a 5-way navigation
switch (UP/DOWN/LEFT/RIGHT/ENTER; HRO K1-1506SN-01, SMD 10×10 mm), like the joystick
on SeedSigner's LCD HAT. It also has five 6×6 mm through-hole tactile footprints wired in parallel to the same five nets, so a
builder fits whichever they have. KEY1–3 are always 6×6 tactiles. Each switch
connects its GPIO to GND, and the firmware turns on the pull-ups, so there are no
resistors.

Why these pins:
- **UP/DOWN/LEFT/RIGHT on 4–7, as on the S3 and C3**, so a breadboard wired for one
  chip works on the others.
- **I2C on 8/9**, as in all three firmware board files. LOLIN's own default (33/35)
  is overridden in `firmware/boards/SEEDSIGNER_S2_MINI/mpconfigboard.h`.
- **SPI on 34–37**, the S2's FSPI IO-MUX pins (CS0, D, CLK, Q). They run SPI at
  full speed without going through the GPIO matrix. If a pin there turns out not to
  be on the IO MUX, nothing breaks:
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

The pins of the S3 devkit wiring used during development, plus KEY1. GPIO 35–37 belong to the
octal PSRAM on the N16R8.

| UP | DOWN | LEFT | RIGHT | ENTER | KEY1 | SDA | SCL |
|---|---|---|---|---|---|---|---|
| 4 | 5 | 6 | 7 | 15 | 16 | 8 | 9 |

## Status

- **Buttons:** done in the bridge for all three chips. Checked on an S2 Mini
  (KEY1 and ENTER); not yet on the S3 or C3.
- **SPI display and MicroSD on the ESP32:** pins assigned, no code yet. On the ESP32
  the app asks the bridge (`sd_ensure`, `sd_live`, `sd_poll`) to mount the card, and
  the bridge doesn't provide those yet, so the app sees no card. On the S2 this will
  be `machine.SDCard(slot=2, sck=36, mosi=35, miso=37, cs=34)`. The S2 has no SDMMC
  host, so SPI mode is the only option.

## Carrier circuit

**I2C display header (1×4: P1 P2 SCL SDA).**
- **Pin order.** OLED modules ship as both GND-VCC and VCC-GND, and powering one
  backwards can destroy it. So P1 and P2 each go through a
  3-pad solder jumper that connects it to either GND or display power. The silkscreen
  shows both settings, and the default is P1 = GND, P2 = VCC.
- **Display power.** A third 3-pad jumper picks 3V3 or VBUS (5 V):
  - **3.3 V (default):** OLEDs, 3.3 V LCDs, and many 5 V 20×4 LCDs with the
    contrast turned well down.
  - **5 V:** HD44780 LCDs whose text is too faint at 3.3 V.
- **Level shifter for 5 V only.** At 5 V the backpack's PCF8574 needs at least 3.5 V
  to read a logic high, more than the S2 drives, and its pull-ups would put 5 V on
  GPIO 8/9. So the 5 V build fits a 2-channel BSS138 level shifter (2× BSS138 and
  4× 10 kΩ: 3.3 V pull-ups on the S2 side, display-power pull-ups on the display
  side). For 3.3 V it's left off, and two solder jumpers bridge SDA and SCL straight
  through.
- **4.7 kΩ I2C pull-ups to 3V3**, not fitted unless a display has none of its own.

**SPI display header (1×8)** in Waveshare's e-paper order: VCC GND DIN CLK CS DC RST
BUSY, at 3.3 V.

**MicroSD.**
- A TF-01A push-push socket on the shared SPI bus, at 3.3 V.
- 10 kΩ pull-ups on CS, MOSI, MISO and the unused DAT1/DAT2.
- 100 nF + 10 µF decoupling.
- An optional 1×6 header (GND VCC MISO MOSI SCK CS) for the plug-in SD module.

**EN (reset) filter.** A 10 kΩ pull-up to 3V3 and 1 µF to GND on the S2 Mini's EN
pin, against spurious resets reported on some S2 Mini clones. The S2 Mini's RST button
still works through it.

**Power.** The S2 Mini's 3V3 and VBUS pins feed the carrier, so the carrier has no
regulator.

## To check before layout

- The SPI IO-MUX pins (34–37) against the ESP32-S2 datasheet.
- The K1-1506SN-01 and TF-01A footprints against their manufacturer drawings.
