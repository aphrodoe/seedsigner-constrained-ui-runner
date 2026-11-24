# Carrier board BOM

The parts for the S2 Mini carrier (pins in [`pin_map.md`](pin_map.md)), with sources
in India and abroad. Prices were read from the shops' own pages on **2026-11-25** and
include 18% GST unless marked "ex GST". Dollar figures use ~₹93 per $. Reviews come
from TechEnclave (India's main hobbyist forum), Trustpilot, EEVblog/Arduino/SparkFun
forums, GitHub issues and manufacturer datasheets. Reddit blocks automated access, so
it isn't covered.

## Parts on the board

| Part | Qty | Pick (India) | Backup / international | Per board |
|---|---|---|---|---|
| Female header 2.54 mm, 2×8, for the S2 Mini | 2 | Cut from a 2×40 strip: Robocraze ₹16 | LCSC C30734, $0.16 each | ₹8 |
| Female header 2.54 mm, 1×4 (I2C display) + 1×8 (SPI display) | 1 + 1 | Cut from a 1×40 strip: Robocraze ₹12 | LCSC C2718488 + C27438 | ₹4 |
| 5-way navigation switch: **HRO K1-1506SN-01**, SMD 10×10, 6 pads | 1 | Robu ₹73 | LCSC C145910, $0.97. Through-hole twin K1-1506DN-01: LCSC C145911 $0.94 (Robu ₹123, out of stock) | ₹73 |
| Tactile 6×6 mm through-hole: **C&K PTS645** | 3 (8 without the 5-way) | Robu ₹6–11 | Omron B3F-1000, LCSC C93157 $0.18 | ₹18–33 (₹48–88) |
| MicroSD socket, push-push, **HRO TF-01A** footprint | 1 | Quartz "SMD Push Type (9 Pin)" ₹9; the TF-01A match isn't confirmed | Genuine TF-01A: LCSC C91145, $0.18 | ₹9 |
| 10 kΩ 0805 (SD line pull-ups) | 5 | Robu or Evelta (strip) | LCSC C17414 (basic part) | ~₹5 |
| 100 nF 0805 (SD decoupling) | 2 | Robu or Evelta | LCSC C49678 (basic part) | ~₹5 |
| 10 µF 0805 (SD decoupling) | 1 | Robu or Evelta | LCSC C15850 (basic part) | ~₹2 |
| 4.7 kΩ 0805 (I2C pull-ups, **not fitted** unless a display lacks its own) | 0 (2 pads) | — | LCSC C17673 | — |
| 10 kΩ + 1 µF 0805 (EN filter) | 1 + 1 | Robu or Evelta | LCSC C17414 + 1 µF 0805 | ~₹3 |
| Solder jumpers (VCC/GND order, 3.3/5 V, SDA/SCL bypass) | — | copper on the board, no parts | | — |
| **5 V LCD builds only:** BSS138 SOT-23 + 10 kΩ 0805 (level shifter) | 2 + 4 | to source (Robu or Evelta) | LCSC | ~₹20 |
| **Carrier parts** | | | **LCSC ≈ $2** | **≈ ₹125–140** |

### Why these parts

- **5-way switch.** The datasheet for the K1-1506SN-01 confirms the centre press
  (300 gf) and gives the pinout: A=1, B=2, C=3, COM=4, D=5, centre=6. The unbranded
  ₹39 10×10 switch has no datasheet, and no reviews either way. ALPS SKRHABE010 (the
  Waveshare HAT's switch, rated 200,000 presses) is the best-documented option, but
  it's import-only and has a finer, harder-to-solder footprint. The five through-hole
  tactile footprints wired in parallel stay as the no-SMD fallback.
- **Tactile switches.** PTS645 is rated for 100,000 presses with bounce ≤ 10 ms, from
  a known maker, and costs only a few rupees more than an unbranded switch. Keep the
  firmware debounce at 10 ms or more.
- **MicroSD.** All 3 failure reports found were push-push latch or spring breakage
  (SparkFun OpenLog, Artemis, Olimex). TF-01A is rated for 5,000 cycles, plenty for a
  card that's rarely swapped. A push-pull socket (Molex 104031-0811, LCSC $0.68) has
  no latch to break, but needs a different footprint.
- **Headers.** Use stamped square-hole sockets, treated as good for 50–100 insertions.
  **Not machined round-pin sockets:** they don't accept the S2 Mini's 0.64 mm square
  pins.
- **The ₹39 SD module** on an optional 1×6 header (GND VCC MISO MOSI SCK CS) stays as
  a fallback if the socket is hard to solder.

## The bare board

| Maker | 5 boards, delivered | Time | Paperwork | Evidence |
|---|---|---|---|---|
| **JLCPCB** (China) + UPS | $13.54 + ~31% duty + any courier fee ≈ **₹1,700** | 2-day build + 5–7 days | Courier KYC (PAN or Aadhaar) | Strongest. An independent long-term comparison (lcamtuf, Jan 2026) calls the quality excellent, with a thinner solder mask than OSH Park. Positive Indian forum reports. |
| **IndiPCB** (Odisha) | **₹1,272** including GST and shipping | 5 working days | None | Almost none. Small and new. The offer needs traces and gaps of at least 0.25 mm. |
| **LionCircuits** (Bengaluru) | ₹1,204 (₹1,421 if GST is extra); leaded HASL only | 5–6 working days | None | Thin: "work just fine" from one user; a 2022 article mentions delays. |
| PCBWay (China), post | $16.68 | 11–33 days, unreliable | Possibly duty-free (postal ₹1,000 exemption, read differently by different customs offices) | Good (Trustpilot 4.2) |

Ruled out:
- **PCB Power** (₹4,655, one recent 1★ review).
- **Robu and Zbotic PCB** (15–20 days; Robu's may be resold JLCPCB).
- **OSH Park** ($74 for 6).
- **NextPCB** ($47).
- **Elecrow** (delivery complaints).
- **AllPCB** (site suspended).

**Chosen: JLCPCB with UPS.** It has the strongest quality evidence for a first board,
and its turnaround still fits before the December break. Have PAN or Aadhaar ready for
the courier's KYC upload.

India import duty on a personal courier parcel is **30.98%** (10% basic duty + surcharge
+ 18% IGST, from the Bengaluru and Chennai customs FAQs). A parcel declared as a gift is
charged 43.96%, so pay with your own card.

## Supplied by the builder

### Microcontroller: LOLIN S2 Mini, but check for PSRAM

**LOLIN has dropped PSRAM from the S2 Mini.** Its docs commit `746363a`
(2026-11-07) changes the chip from ESP32-S2FN4R2 to **ESP32-S2FH4** and deletes
"2MB PSRAM". Clones were already sold both ways (two first-hand reports of FH4 boards
sold as "S2 Mini"). LCSC also lists the ESP32-S2-MINI-2-N4R2 module as discontinued.

On an FH4 board our firmware still runs, but in the no-PSRAM configuration: 8 KB
caches, **3 s to sign 10 inputs** instead of 0.8 s, and 28 KB of SRAM left at the
tightest point (`research/silicon/README.md`). So:
- **Buy listings that name the S2FN4R2 / 2 MB PSRAM**, and check each board on
  arrival. `esptool chip-id` (in download mode) reports "Embedded PSRAM 2MB", or read
  the marking on the chip.
- The firmware should report the missing PSRAM at boot rather than quietly run slow.

| Source | Price | Note |
|---|---|---|
| Amazon.in, OceanLabz (FN4R2 in the title) | ₹524, 3.9★ from 12 reviews | In stock |
| Amazon.in, xcluma | ₹701 | Our bench board came from here, and it has PSRAM |
| Robu | ₹299 | Out of stock |
| AliExpress | ₹177–335 | Some sellers list "S2" and "S2 With PSRAM" separately. AliExpress delivery to India is unreliable. |

Other known S2 Mini clone faults: about 4 sources report resets under load from noise
on EN (one blamed a capacitor not soldered to ground), and 4 report flaky USB
flashing. That's a reason to put a 10 kΩ pull-up and an RC filter on EN on the carrier.

Alternatives considered:
- **LOLIN S3 Mini** (same 34.3×25.4 mm size, 27 IO, 2 MB PSRAM; AliExpress ₹468,
  but won't ship to India).
- **Waveshare ESP32-P4-Pico** (no radio at all, 32 MB PSRAM, 27 GPIOs; Robu ₹1,509,
  in stock).
- **Waveshare ESP32-S3-Pico** (₹966).
- **RP2350 Pico 2** (no radio, ₹518–659; our crypto modules would need porting to it).
- Too few GPIOs: S3 SuperMini, S3-Zero, XIAO S3, QT Py S2, C3 SuperMini.

### Display: 0.96″ SSD1306 OLED, with care

| Source | Price |
|---|---|
| Quartz | ₹144 |
| Hubtronics | ₹155 |
| Robu | ₹169 |
| AliExpress | ~$1.44 |

- **Pin order varies.** Four first-hand reports of modules with VCC and GND swapped,
  including an Amazon.in review from 2026-08. Reversing them can destroy a module. The
  carrier's I2C header needs a way to select the order, not only a silkscreen label.
- **Wear.** 9 reports of dimming or burn-in, nearly all from screens left on 24/7.
  Ledger's Nano S/X use the same SSD1306. A signing device is on for minutes per
  session; the firmware should blank the screen after idle time.
- **1.3″ SH1106 upgrade** (₹263–406). It fits the same 4-pin socket, but it's a
  different controller, so the firmware has to detect which one is fitted.
- **No burn-in:**
  - **20×4 HD44780 LCD** (already supported). Three threads say 5 V panels show faint
    text at 3.3 V, so offer a 5 V option with the backpack pull-ups kept off 5 V.
  - **Sharp Memory LCD**: best on paper, not sold in India.
- **E-paper** keeps the seed words on screen after power-off, so it needs a forced
  wipe at shutdown.

## Where to buy

- **Robu**: buy from here first. It has the strongest record on the forums (about 20
  positive TechEnclave users) and stocks the branded parts above. Recent Trustpilot
  reviews are poor (2.8★, missing items), so record an unboxing video.
- **Quartz**: fine for cheap parts, weak on returns.
- **Evelta**: branded stock, few reviews.
- **Avoid ElectronicsComp**: Trustpilot 1.1★ from 442 reviews, 96% 1★ (orders not
  sent, partial shipments, no refunds), and forum users calling it "scammers".
- **LCSC**: worth it only for a combined order (genuine TF-01A, SKRHABE010, B3F). It
  ships without duty paid, so budget for courier KYC plus about 31% duty and fees.
- **DigiKey India**: free delivery from ₹7,000.
- **AliExpress**: its app has been banned in India since 2020, and delivery is
  unreliable.

## What a device costs

| | India |
|---|---|
| Carrier parts | ≈ ₹130 |
| Bare board (1 of 5, JLCPCB, with duty) | ≈ ₹340 |
| S2 Mini with PSRAM | ₹524 |
| 0.96″ OLED | ₹144 |
| **Total** | **≈ ₹1,140 (≈ $12)**, plus shop shipping |

A stock SeedSigner is about $50.

## Before ordering

- [ ] Check the K1-1506SN-01's pad drawing against the footprint.
- [ ] Check the Quartz MicroSD socket against the TF-01A drawing, or order genuine TF-01A.
- [x] Display header: VCC/GND order jumpers, a 3.3 V/5 V jumper, and a BSS138 level shifter for 5 V (decided 2026-11-25; see `pin_map.md`).
- [x] EN: 10 kΩ + 1 µF filter (decided 2026-11-25).
- [ ] Source the BSS138.
- [ ] Firmware: a PSRAM check at boot, and blanking the OLED after idle time.
- [ ] Record the real customs duty or the Indian maker's quality when the first boards arrive.
