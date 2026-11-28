# Carrier schematic: connections

Every connection on the S2 Mini carrier, for drawing and checking the schematic. Pin
assignments come from [`pin_map.md`](../../docs/pin_map.md) and parts from
[`bom.md`](../../docs/bom.md). Symbol and footprint names are KiCad 10's standard
libraries, except the `carrier:` parts. Those are in `lib/`, fetched from LCSC with
easyeda2kicad and checked against the datasheet drawings. The project's library tables
load them automatically.

Use **net labels** with the names below rather than long wires: `UP`, `SDA` and so on.
Two pins with the same label are connected.

## Power nets

| Net | Comes from | Notes |
|---|---|---|
| `+3V3` | S2 Mini 3V3 pin | `power:+3V3` symbol |
| `VBUS` | S2 Mini VBUS pin (5 V from USB) | `power:VBUS` symbol |
| `GND` | S2 Mini GND pins (both) | `power:GND` symbol |
| `VDISP` | JP3 (3.3 V or 5 V) | I2C display power only |

The I2C displays' VCC and GND are `VDISP` and `GND` directly.

## J1, J2: the S2 Mini sockets

Two `Connector_Generic:Conn_02x08_Odd_Even`, footprint
`Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical`. Rows run from the
end away from USB-C (row 1) to the USB-C end (row 8). In each row, the odd pin is
the left column of that header, viewed from the top.

The part soldered there is a female socket, but the footprint is the **pin header**
one on purpose. KiCad's `PinSocket_2x08` footprint puts pad 2 to the *left* of pad 1:
it's drawn for a socket that mates face-down with a header on another board. The S2
Mini sits face-up, so its pins are where `PinHeader_2x08` puts them. The drill
pattern is the same.

**J1, left header** (odd = outer column, even = inner column):

| Pin | S2 Mini | Net | | Pin | S2 Mini | Net |
|---|---|---|---|---|---|---|
| 1 | EN | `EN` | | 2 | GPIO 1 | `KEY1` |
| 3 | GPIO 3 | `KEY3` | | 4 | GPIO 2 | `KEY2` |
| 5 | GPIO 5 | `DOWN` | | 6 | GPIO 4 | `UP` |
| 7 | GPIO 7 | `RIGHT` | | 8 | GPIO 6 | `LEFT` |
| 9 | GPIO 9 | `SCL` | | 10 | GPIO 8 | `SDA` |
| 11 | GPIO 11 | no connect | | 12 | GPIO 10 | `ENTER` |
| 13 | GPIO 12 | no connect | | 14 | GPIO 13 | no connect |
| 15 | 3V3 | `+3V3` | | 16 | GPIO 14 | no connect |

**J2, right header** (odd = inner column, even = outer column):

| Pin | S2 Mini | Net | | Pin | S2 Mini | Net |
|---|---|---|---|---|---|---|
| 1 | GPIO 40 | `DISP_RST` | | 2 | GPIO 39 | `DISP_DC` |
| 3 | GPIO 38 | `DISP_CS` | | 4 | GPIO 37 | `SPI_MISO` |
| 5 | GPIO 36 | `SPI_SCK` | | 6 | GPIO 35 | `SPI_MOSI` |
| 7 | GPIO 34 | `SD_CS` | | 8 | GPIO 33 | `DISP_BUSY` |
| 9 | GPIO 21 | no connect | | 10 | GPIO 18 | no connect |
| 11 | GPIO 17 | no connect | | 12 | GPIO 16 | no connect |
| 13 | GND | `GND` | | 14 | GND | `GND` |
| 15 | GPIO 15 (on-board LED) | no connect | | 16 | VBUS | `VBUS` |

Put a **no-connect flag** (X) on every unused pin, or the electrical rules check (ERC)
will flag it.

> **Layout warning.** Whether J1/J2's pin 1 ends up on the correct side depends on
> how the S2 Mini sits on the carrier. Before ordering, check it against the real
> board on a 1:1 paper print. The S2 Mini's own pin labels are printed on its
> underside, mirrored.

## Buttons

Every switch connects its net to `GND`. The firmware enables internal pull-ups, so
there are no resistors.

| Ref | Symbol | Footprint | Connections |
|---|---|---|---|
| SW1 | `carrier:K1-1506SN-01` | `carrier:KEY-SMD_K1-1506SN-01` | 1 (A) → `UP`, 2 (B) → `LEFT`, 3 (C) → `DOWN`, 5 (D) → `RIGHT`, 6 (centre) → `ENTER`, 4 (common) → `GND` |
| SW2 | `Switch:SW_Push` | `Button_Switch_THT:SW_PUSH_6mm` | `UP` – `GND` (alternative to SW1) |
| SW3 | same | same | `DOWN` – `GND` (alternative) |
| SW4 | same | same | `LEFT` – `GND` (alternative) |
| SW5 | same | same | `RIGHT` – `GND` (alternative) |
| SW6 | same | same | `ENTER` – `GND` (alternative) |
| SW7 | same | same | `KEY1` – `GND` |
| SW8 | same | same | `KEY2` – `GND` |
| SW9 | same | same | `KEY3` – `GND` |

The K1-1506SN-01 pinout is on its datasheet drawing (LCSC C145910). The pad layout is
the `carrier:KEY-SMD_K1-1506SN-01` footprint; check it on a 1:1 print with the real
switch before ordering.

## EN filter

| Ref | Symbol | Footprint | Connections |
|---|---|---|---|
| R1 | `Device:R_Small`, 10 kΩ | `Resistor_SMD:R_0805_2012Metric` | `EN` – `+3V3` |
| C1 | `Device:C_Small`, 1 µF | `Capacitor_SMD:C_0805_2012Metric` | `EN` – `GND` |

## I2C display header

OLED modules ship as both GND-VCC-SCL-SDA and VCC-GND-SCL-SDA, and powering one
backwards can destroy it. So there are **two** 4-pin footprints side by side, one for
each order. The builder fits a socket in the one that matches their module and leaves
the other empty. There are no jumpers to get wrong.

Both are `Connector_Generic:Conn_01x04` with footprint
`Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical`.

| Ref | Pin 1 | Pin 2 | Pin 3 | Pin 4 | Silkscreen |
|---|---|---|---|---|---|
| J3 | `GND` | `VDISP` | `SCL_D` | `SDA_D` | `GND VCC SCL SDA` |
| J7 | `VDISP` | `GND` | `SCL_D` | `SDA_D` | `VCC GND SCL SDA` |

PCF8574 LCD backpacks are usually GND VCC **SDA SCL**. They connect with jumper
wires anyway, so cross SDA and SCL.

**Display voltage.** JP3 is a 3-pin header with a jumper cap, so it can only select one
supply at a time: `Jumper:Jumper_3_Open` with footprint
`Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical`.

| Ref | Pin 1 | Pin 2 (common) | Pin 3 | Silkscreen |
|---|---|---|---|---|
| JP3 | `+3V3` | `VDISP` | `VBUS` | `3V3 · VCC · 5V` |

It ships without a cap, so the display gets no power until the builder chooses.

**Level shifter, always fitted.** Two BSS138 MOSFETs, each wired gate to `+3V3`,
source to the S2 side, drain to the display side. It works the same at 3.3 V and at
5 V, so there's no bypass, and no setting can put 5 V on GPIO 8/9.

| Ref | Symbol | Footprint | Connections |
|---|---|---|---|
| Q1 | `Transistor_FET:BSS138` | `Package_TO_SOT_SMD:SOT-23` | G → `+3V3`, S → `SDA`, D → `SDA_D` |
| Q2 | same | same | G → `+3V3`, S → `SCL`, D → `SCL_D` |
| R2 | `Device:R_Small`, 4.7 kΩ | `R_0805_2012Metric` | `SDA` – `+3V3` |
| R3 | same | same | `SCL` – `+3V3` |
| R4 | same | same | `SDA_D` – `VDISP` |
| R5 | same | same | `SCL_D` – `VDISP` |
| C2 | `Device:C_Small`, 100 nF | `C_0805_2012Metric` | `VDISP` – `GND`, close to J3/J7 |

4.7 kΩ rather than 10 kΩ, because the firmware runs I2C at 400 kHz.

## SPI display header

J4 is a `Connector_Generic:Conn_01x08` with footprint
`PinSocket_1x08_P2.54mm_Vertical`, in Waveshare e-paper order:

| Pin | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Net | `+3V3` | `GND` | `SPI_MOSI` (DIN) | `SPI_SCK` (CLK) | `DISP_CS` | `DISP_DC` | `DISP_RST` | `DISP_BUSY` |

R11 (`Device:R_Small`, 10 kΩ, `R_0805_2012Metric`): `DISP_CS` – `+3V3`. It keeps the
display deselected while the S2 boots and while the SD card is in use.

## MicroSD

J5 is the `carrier:TF-01A` symbol with footprint `carrier:TF-SMD_TF-01A` (HRO TF-01A,
LCSC C91145: push-push, 9 pads at 1.10 mm pitch, 4 shell pads, 2 locating holes).

| Socket pin | Net | Plus |
|---|---|---|
| DAT2 (1) | `SD_DAT2` | R6 10 kΩ to `+3V3` |
| DAT3/CD (2) | `SD_CS` | R7 10 kΩ to `+3V3` |
| CMD (3) | `SPI_MOSI` | R8 10 kΩ to `+3V3` |
| VDD (4) | `+3V3` | C3 10 µF + C4 100 nF to `GND`, close to the socket |
| CLK (5) | `SPI_SCK` | |
| VSS (6) | `GND` | |
| DAT0 (7) | `SPI_MISO` | R9 10 kΩ to `+3V3` |
| DAT1 (8) | `SD_DAT1` | R10 10 kΩ to `+3V3` |
| CD (9) | no connect | card-detect switch, unused |
| GND (10–13), the shell | `GND` | |

The optional plug-in SD module, J6, is a `Connector_Generic:Conn_01x06` with
footprint `PinSocket_1x06_P2.54mm_Vertical`:
- Pin 1: `GND`.
- Pin 2: `VBUS`. The common module has its own 1117 3.3 V regulator and needs 5 V;
  its level shifter drives MISO at 3.3 V.
- Pin 3: `SPI_MISO`.
- Pin 4: `SPI_MOSI`.
- Pin 5: `SPI_SCK`.
- Pin 6: `SD_CS`.

Fit **either** the socket (J5) **or** the module (J6), not both: they share CS and MISO.

## Mounting

H1–H4 are `Mechanical:MountingHole`, footprint `MountingHole:MountingHole_3.2mm_M3`,
one in each corner.

## Before calling the schematic done

- [ ] ERC passes. Every unused pin has a no-connect flag, and the power nets have
      `PWR_FLAG`s where KiCad asks for them.
- [ ] Every part has a footprint (Tools → Assign Footprints).
- [ ] The netlist matches this file.
