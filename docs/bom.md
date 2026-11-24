# Carrier board: bill of materials

Everything needed to build one S2 Mini carrier. The pin assignments and circuit are in
[`pin_map.md`](pin_map.md). Indian prices include 18% GST. All prices were checked in
November 2026 and will drift.

## Always fitted

| Part | Qty | India | International (LCSC) | ≈ ₹ / board |
|---|---|---|---|---|
| Female header, 2.54 mm, 2×8 (holds the S2 Mini) | 2 | Cut from a 2×40 female strip (Robocraze ₹16) | C30734 | 8 |
| Female header, 2.54 mm, 1×4 (I2C display) | 1 | Cut from a 1×40 female strip (Robocraze ₹12) | C2718488 | 2 |
| Female header, 2.54 mm, 1×8 (SPI display) | 1 | from the same strip | C27438 | 2 |
| 5-way navigation switch, HRO K1-1506SN-01 (SMD, 10×10 mm) | 1 | Robu ₹73 | C145910 | 73 |
| Tactile switch 6×6 mm through-hole, C&K PTS645 (KEY1–3) | 3 | Robu ₹6–11 | Omron B3F-1000, C93157 | 18–33 |
| MicroSD socket, push-push, HRO TF-01A | 1 | Generic 9-pin push type (Quartz ₹9); check it against the TF-01A drawing | C91145 | 9 |
| Resistor 10 kΩ 0805: MicroSD pull-ups (CS, MOSI, MISO, DAT1, DAT2), I2C pull-ups (SDA, SCL) and the EN pull-up | 8 | Robu or Evelta | C17414 | 8 |
| Capacitor 100 nF 0805 (MicroSD decoupling) | 2 | Robu or Evelta | C49678 | 4 |
| Capacitor 10 µF 0805 (MicroSD decoupling) | 1 | Robu or Evelta | C15850 | 2 |
| Capacitor 1 µF 0805 (EN filter) | 1 | Robu or Evelta | any 1 µF X7R/X5R 0805 | 1 |
| **Total** | | | **≈ $2** | **≈ ₹125–140** |

## Optional

| Part | Qty | When to fit it |
|---|---|---|
| Tactile switch 6×6 mm, PTS645 | 5 | Instead of the 5-way switch. The footprints are wired in parallel, so no SMD soldering is needed. |
| BSS138 MOSFET (SOT-23) + 10 kΩ 0805 | 2 + 2 | Level shifter, only when the display header is set to 5 V (see `pin_map.md`). At 3.3 V, bridge the bypass jumpers instead. |
| Female header 1×6 + a 6-pin SPI MicroSD module (Robu ₹39) | 1 | Instead of soldering the MicroSD socket. |

All the configuration jumpers (VCC/GND order, 3.3/5 V, level-shifter bypass) are solder
pads on the board, not parts.

## The board

2-layer FR-4, 1.6 mm, HASL. Gerbers to follow with the layout. Any PCB maker works.
For reference, in November 2026:

| Maker | 5 boards, delivered to India | Lead time |
|---|---|---|
| JLCPCB (UPS) | $13.54 + import duty | ~1 week |
| IndiPCB | ₹1,272 incl. GST | 5 working days |
| LionCircuits | ₹1,204 + GST | 5–6 working days |

Boards imported into India by courier pay about **31% duty and IGST** on the order value
including shipping. The courier asks for KYC (PAN or Aadhaar) before clearance.

## Modules you plug in

**Microcontroller: LOLIN S2 Mini or a clone with ESP32-S2FN4R2** (4 MB flash, 2 MB
PSRAM). India: Amazon.in ₹524–701. International: AliExpress, ~$2–4.

> **Check for PSRAM.** Since November 2026, LOLIN's own S2 Mini uses the ESP32-S2FH4,
> which has no PSRAM, and clones are sold both ways. Without PSRAM the firmware still
> runs, but signing slows from ~0.8 s to ~3 s for a 10-input transaction. Buy listings
> that name the S2FN4R2. On arrival, run `esptool chip-id` with the board in download
> mode (hold 0, tap RST) and look for "Embedded PSRAM 2MB".

**Display: 0.96″ SSD1306 128×64 I2C OLED, 4-pin.** India: ₹144–169 (Quartz,
Hubtronics, Robu). International: ~$1.50.

> **Check the pin order** printed on the module (GND-VCC or VCC-GND) and set the
> carrier's jumpers to match before powering on. Reversed power can destroy the module.

Also supported:
- 1.3″ SH1106 OLED (same socket).
- 20×4 or 16×2 HD44780 LCD with a PCF8574 I2C backpack. Use 5 V and the level shifter
  if the text is faint at 3.3 V.
- 1.54″ Waveshare e-paper on the SPI header.

**MicroSD card.** Any small card, FAT32.

## Where to buy

- **In India:** Robu stocks every always-fitted part. Quartz and Evelta are useful for
  the socket and passives.
- **International:** LCSC has every part above. Small LCSC orders into India pay the
  same courier duty as the boards, so it's only worth it combined with other parts.

## Cost of a device

| | ≈ ₹ |
|---|---|
| Carrier parts | 130 |
| Board (1 of 5, JLCPCB, with duty) | 340 |
| S2 Mini | 524 |
| 0.96″ OLED | 144 |
| **Total** | **≈ 1,140 (≈ $12)** |

For comparison, a standard SeedSigner (Pi Zero, camera, LCD HAT) costs about $50.
