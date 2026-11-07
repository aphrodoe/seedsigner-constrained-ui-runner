# Pi Zero image

A flashable SD card image of the constrained SeedSigner for the Raspberry Pi
Zero, so it runs without repeating the manual setup in the
[build guide](../docs/constrained_build_guide.md).

> **Tested on a Pi Zero v1.3**, both images (128×32 OLED, six buttons, SPI
> MicroSD module): boots, starts SeedSigner on the display, the buttons drive
> it, and a PSBT loaded from the card was signed and saved back to it. The
> image without `--dev` offers no network on the USB port.

## What's in it

- Raspberry Pi OS Lite, 32-bit (Trixie, 2026-10-06), pinned by URL and SHA-256
- this repo at `/home/pi/seedsigner-constrained-ui-runner`, installed by
  `setup.sh`
- I2C and SPI on, the `spi-sd` MicroSD overlay
  ([`files/spi-sd.dts`](files/spi-sd.dts)), and the MicroSD sudoers rules
- Wi-Fi and Bluetooth off (they only exist on the Zero W)
- SeedSigner starts at boot (`seedsigner.service`)

## Build

Needs Docker and about 8 GB free. No `sudo`. It builds the committed `HEAD`
and takes about 15 minutes; the result is a ~830 MB `.img.xz` that fits a
4 GB card.

```sh
pi-image/build.sh          # pi-image/build/seedsigner-constrained-pi0-<date>-<commit>.img.xz
pi-image/build.sh --dev    # same, plus USB Ethernet at 10.42.0.2 and SSH as pi/pi
```

The build runs in a privileged container, which registers QEMU's ARM emulator
with the host kernel until the next reboot.

## Flash and configure

Flash the `.img.xz` with Raspberry Pi Imager ("Use custom") or
`xzcat <image>.img.xz | sudo dd of=/dev/sdX bs=4M conv=fsync`. Skip Imager's OS
customisation: the image already sets up its user.

Before the first boot, pick your display in `seedsigner-config.json` on the
card's boot partition. The options are in the
[build guide, section 3](../docs/constrained_build_guide.md#3-configuration-configjson).

The first boot takes about 4 minutes: it grows the root partition to fill the
card. The normal image has no login and no SSH. The `--dev` image is for
development only: it has a known password (pi/pi) and SSH over USB Ethernet.
Plug the Pi's inner USB port into a laptop, give the laptop's new interface
`10.42.0.1/24`, then `ssh pi@10.42.0.2`.
