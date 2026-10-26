# Screen survey

A low-cost SeedSigner is only useful if people can build it from parts they can actually buy,
and keep using it for years. This survey compares the displays the text renderer supports, plus
the obvious alternatives at the same price, on four axes: **cost, longevity, availability and
reliability**. It informs two hardware designs:
- a generic carrier board that accepts several displays;
- an integrated board with one display soldered on.

Prices are public listings seen in October 2026, linked under Sources, and will drift. **[DS]**
marks a datasheet or manufacturer figure, **[S]** a seller listing.

## At a glance

Text grids for pixel displays assume MicroPython's built-in 8×8 font. A larger font gives
fewer cells.

| Display | Text grid | Bus | India | Global | Rated life | Supply | MicroPython driver |
|---|---|---|---|---|---|---|---|
| 16×2 char LCD + I2C backpack | 16×2 | I2C | ₹150 | — | backlight >50,000 h [S] | clones of a discontinued part, everywhere | community |
| 20×4 char LCD + I2C backpack | 20×4 | I2C | ₹275–550 | $9–13 | not published | as above | community |
| SSD1306 0.96" OLED 128×64 | 16×8 | I2C | ₹130 | €8 | ≥10,000 h to half brightness [DS] | everywhere | **official** |
| SSD1306 0.91" OLED 128×32 | 16×4 | I2C | ₹184 | $4 | ≥10,000 h [DS] | everywhere | **official** |
| SH1106 1.3" OLED 128×64 | 16×8 | I2C | ₹329 | $5 | not published | wide | community |
| ST7789 1.54" IPS TFT 240×240 | 30×30 | SPI | ₹199 | $4 bare | not published | wide | community C module |
| ST7735 1.8" TFT 128×160 | 16×20 | SPI | ₹429 | $20 | not published | wide | community |
| Nokia 5110 (PCD8544) 84×48 | 10×6 | SPI | ₹280–349 | €8 | not published | **salvage only** | community |
| 1.54" e-paper 200×200, black/white | 25×25 | SPI | not listed | $10 | 1,000,000 refreshes [DS] | wide | community |
| Sharp Memory LCD 1.3" 168×144 | 21×18 | SPI | not sold | $25 | not published | **single source** | community, unmaintained |

## By family

### Character LCDs (16×2, 20×4)

- **Cost.** About ₹150 for a 16×2 with an I2C backpack. A 20×4 is ₹275 with backpack from a
  wholesaler, or ₹499 bare plus ₹49 for a backpack at retail; $9–13 abroad.
- **Longevity.** The best of the set. Nothing burns in. Waveshare rates the 1602's LED
  backlight above 50,000 hours.
- **Availability.** Hitachi discontinued the HD44780 long ago, but compatible clones (ST7066U,
  KS0066, AIP31066) are in every hobby shop, and the I2C backpack is the PCF8574 everywhere.
  Many independent sources with the same interface: the most robust supply in this survey.
- **Reliability.**
  - These are 5 V modules. The backpack pulls SDA/SCL up to its own supply, so at 5 V it puts
    5 V on a 3.3 V microcontroller's pins. A level shifter, or running the whole module at
    3.3 V, is required, and at 3.3 V the glass's contrast range shrinks.
  - 0–50 °C typical.
  - Bulky and thick next to everything else.
- **Fit.** Only 8 custom characters (CGRAM) per frame for icons; the renderer already
  allocates within that. Text-first design is native here.

### Monochrome OLEDs (SSD1306 0.96" and 0.91", SH1106 1.3")

- **Cost.** The cheapest pixel displays: ₹130–330.
- **Longevity.** The weak axis in principle. Datasheets rate the panels at ≥10,000 hours to
  half brightness, and static content burns in (a top navigation bar is static). A signing
  device is on for minutes per transaction, so 10,000 hours is decades of use. Keeping it that
  way takes powering down between uses and the screensaver SeedSigner already has.
  In the field they still die: a Bitaxe retailer's troubleshooting guide treats a dead OLED as a
  routine fault, fixed by swapping in a ~$5 0.96" SSD1306 module.
- **Availability.** Sold everywhere, by many vendors.
- **Reliability.**
  - 3.3 V native, −30–70 °C.
  - The SSD1306 is the **only display here with an official micropython-lib driver**.
  - Two module quirks a builder can hit. Some modules swap the GND and VCC pins, so a carrier
    must label its header clearly. The SH1106 has 132 columns of RAM for 128 pixels, so its
    driver needs a column offset.
- **Fit.** 16×8 at the built-in font. On the 0.91", the bezel hides part of the 4th row, so the
  renderer uses 3.

### Colour TFTs (ST7789 240×240, ST7735 128×160)

- **Cost.** Bare modules are cheap: ₹199 for a 1.54" ST7789 (out of stock when checked). The
  1.3" 240×240 HAT the Raspberry Pi SeedSigner uses is ₹1,010.
- **Longevity.** Backlight life is unpublished; no burn-in.
- **Availability.** Wide.
- **Reliability.**
  - 3.3 V native.
  - Adafruit warns that the backlight can peel away from the glass without a cover holding it.
  - Drivers are community-only. The fast one (`st7789_mpy`) is a C module, so it needs a
    custom firmware build.
- **Fit.**
  - A large text grid and colour.
  - A full 240×240×16-bit frame is 115 KB, a large share of the ~400 KB of SRAM on a chip
    without PSRAM such as the ESP32-C3. Text can be drawn cell by cell without a framebuffer.
  - **This is the one family that pulls toward a graphics library.** It's the panel class
    SeedSigner's LVGL screens target, so choosing it points to an LVGL firmware rather than the
    text renderer.

### Nokia 5110 (PCD8544)

Retired by SparkFun, Core Electronics and Little Bird. Little Bird says the panels are recycled
from old phones: "there's no such thing as a 'new' Nokia 5110 display." **Out:** a build guide
can't depend on salvage.

### 1.54" e-paper (SSD1681)

- **Cost.** No black/white listing found in India; Hubtronics carries the tri-colour version at
  ₹1,199. About $10 from Waveshare.
- **Longevity.**
  - Rated for 1,000,000 refreshes.
  - The vendor's guidance is written for signage, not menus: refresh at most every 180 s, a
    full refresh after every ~5 partials, and sleep when idle. Interactive navigation breaks
    all of it.
- **Reliability.**
  - 0–50 °C only.
  - Full refresh takes ~2 s.
  - **For a wallet:** the panel keeps its last image with no power. A seed word on screen
    stays readable after power is cut, unless the firmware clears it first, and a pulled cable
    gives it no chance to.
- **Fit.** Excellent readability, but wrong for an interactive UI that shows secrets.

### Sharp Memory LCD

- **Strengths.** Daylight-readable and tiny power (4 µA at 1 Hz).
- **Against it.**
  - Single source (Sharp).
  - Not sold in India.
  - $25 as an Adafruit breakout. Bare panels come in 2,240-unit MOQs with 28-week lead times.
- **Verdict.** **Out** for a low-cost build.

## Tested on an ESP32-S3

The 20×4 LCD and the 0.91" OLED have been driven from MicroPython on an ESP32-S3, drawing
SeedSigner's main menu through the bridge. Photos: [`docs/esp32_s3_lcd_20x4.jpg`](../../docs/esp32_s3_lcd_20x4.jpg)
and [`docs/esp32_s3_oled_128x32.jpg`](../../docs/esp32_s3_oled_128x32.jpg).

- **The 20×4 LCD runs at 3.3 V.** The module tested (PCF8574 backpack at `0x27`) showed nothing
  until its contrast trimmer was turned well down, then read cleanly. A 3.3 V I2C header
  therefore works for at least this module; others may need more contrast range than 3.3 V
  gives.
- **A full LCD frame takes 141 ms** over I2C at 400 kHz. The 4-bit protocol sends each
  character as several I2C writes. Rendering the frame takes 6–13 ms. Since the bridge redraws
  the whole display on every poll, a character LCD needs changed-cells-only updates before
  navigation feels responsive.
- **The OLED shows no icons.** MicroPython's built-in 8×8 font is ASCII, so the bridge's
  fallbacks appear (`#` for Scan, `K` for Seeds). The LCD loads the same icons as custom
  characters. Drawing the icons as 8×8 bitmaps on pixel displays is a small follow-up.
- **Not yet tested on the ESP32:** the e-paper and the TFT. Both have run only on a Raspberry Pi
  Zero.

## Recommendation

**Generic carrier: one 4-pin I2C header, labelled, plus an SPI header.**
- The I2C header takes all three families that pass on every axis: character LCDs through their
  backpack, and SSD1306/SH1106 OLEDs. Label the GND and VCC order on the silkscreen, because
  OLED modules disagree on it.
- Power the header from 3.3 V, so no module can put 5 V on the microcontroller's pins. A
  character LCD then runs at 3.3 V (check its contrast) or brings its own level shifter.
- An SPI header with the Waveshare pin order keeps a TFT or e-paper possible without committing
  to either.

**Integrated board: a 128×64 OLED.**
- The 0.96" SSD1306 is the cheapest (₹130) and the only display with an official MicroPython
  driver. It's 3.3 V native, small, and gives 16×8 text, the renderer's tier 2.
- The 1.3" SH1106 is the same grid on larger glass for ~₹200 more, worth it if legibility at
  arm's length matters more than price.
- Its one weak axis, OLED life and burn-in, is answered by how a signing device is used: on
  for minutes, off otherwise, with a screensaver.
- Panels still die, so the board should make one cheap to replace: seat the OLED on a header,
  not soldered down, so a dead panel is a ₹130 swap rather than a new device.

**Upgrade option: the ST7789 240×240 IPS.** It's cheap as a bare module, colour, and the panel
class SeedSigner's LVGL screens target. Choosing it means an LVGL firmware, and drawing without
a full framebuffer on chips without PSRAM. That's a decision for a later revision, not the first
board.

**Out:**
- **Nokia 5110:** no new supply.
- **Sharp Memory LCD:** single source, not sold in India.
- **E-paper as the main display:** its refresh guidance and the image surviving power-off both
  argue against it on a device that shows secrets.

## Sources

Prices and listings:
- https://shop.controllerstech.com/products/16x2-lcd-display-with-attached-pcf8574-i2c-module
- https://m.indiamart.com/proddetail/2004-seven-segment-led-display-display-blue-with-i2c-2855246855630.html
- https://probots.co.in/2004a-20x4-character-lcd-display-blue-backlight.html
- https://probots.co.in/i2c-lcd-backpack-module-for-arduino-and-raspberry-pi-16x2-20x4.html
- https://www.jameco.com/z/SIC2004A-BLWIT-Jameco-ValuePro-20x4-Character-LCD-Module-Parallel-Display-with-I2C-Module-Blue-Backlight-for-Arduino_2304015.html
- https://ameridroid.com/products/i2c-20x4-lcd-module
- https://st.robu.in/product/0-96-inch-oled
- https://www.az-delivery.de/en/products/0-96zolldisplay
- https://zbotic.in/product/0-91-inch-i2c-iic-serial-4-pin-oled-display-module-white/
- https://www.robotshop.com/products/091-inch-128x32-i2c-oled-display-blue
- https://probots.co.in/1-3-inch-128x64-oled-blue-display-sh1106-i2c.html
- https://www.buydisplay.com/i2c-white-1-3-inch-oled-display-module-128x64-arduino-raspberry-pi
- https://aws.robu.in/product/goldenmorning-st7789t3-240x240-spi-1-54inch-tft-display
- https://www.buydisplay.com/size/tft-lcd-display-module/1-54-inch/1-54-inch-tft-lcd-display-ips-panel-screen-240x240-for-smart-watch
- https://www.adafruit.com/product/3787
- https://hubtronics.in/1.3inch-lcd-hat
- https://www.adafruit.com/product/358
- https://shop.controllerstech.com/products/nokia-5110-lcd-display-module
- https://probots.co.in/5110-lcd-display-module-pcd8544-48-84-pixels-matrix-controller.html
- https://az-delivery.de/en/products/lcd-display-84x48-pixel
- https://www.waveshare.com/1.54inch-e-paper-module.htm
- https://hubtronics.in/1-54inch-e-paper-module-b?tag=Epaper
- https://www.adafruit.com/product/3502
- https://www.futureelectronics.com/p/6117773

Datasheets and manufacturer notes:
- https://web.eng.fiu.edu/watsonh/intromicros/M14-I2C/ER-OLED0.96-1_Series_Datasheet.pdf
- https://cdn.sparkfun.com/assets/d/a/8/d/2/SparkFun_TeensyView_ER-OLED0.91-1_Datasheet.pdf
- https://ssd1306.readthedocs.io/en/1.5.0/_downloads/SH1106.pdf
- https://www.alldatasheet.net/datasheet-pdf/pdf/18170/PHILIPS/PCD8544.html
- https://www.waveshare.com/wiki/1.54inch_e-Paper_Module_Manual
- https://www.good-display.com/product/388.html
- https://www.waveshare.com/product/lcd1602-blue.htm

Availability:
- https://www.sparkfun.com/graphic-lcd-84x48-nokia-5110.html
- https://littlebirdelectronics.com.au/products/graphic-lcd-84x48-nokia-5110
- https://forum.crystalfontz.com/threads/whatever-happend-to-hd44780.4530

Field failures:
- https://d-central.tech/asic-troubleshooting/bitaxe-oled-display-blank-no-boot-screen/

Drivers:
- https://github.com/micropython/micropython-lib/tree/master/micropython/drivers/display
- https://github.com/dhylands/python_lcd
- https://github.com/robert-hh/SH1106
- https://github.com/russhughes/st7789_mpy
- https://github.com/boochow/MicroPython-ST7735
- https://github.com/mcauser/micropython-pcd8544
- https://github.com/mcauser/micropython-waveshare-epaper
- https://github.com/pramasoul/micropython-SHARP_Memory_Display
