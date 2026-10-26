# Airgapped MicroSD Architecture

For hardware devices utilizing the Constrained UI Runner (such as the Raspberry Pi Zero without a camera module), SeedSigner's standard QR-code based data ingestion is impossible. 

To solve this, this runner natively intercepts the SeedSigner OS camera and QR-display hardware calls, securely routing all data ingress (reading PSBTs) and data egress (writing XPUBs and signed PSBTs) through an attached SPI MicroSD card.

This document outlines the architectural rationale and working mechanisms of the airgapped MicroSD pipeline.

## 1. Architectural Rationale: SPI vs USB

While the Pi Zero supports USB Gadget mode to act as a virtual thumb drive, this approach was discarded in favor of a dedicated SPI MicroSD reader for several security and reliability reasons:
1. **Host-Machine Interference:** USB Gadget mode relies on the host laptop (e.g. Windows/macOS) properly interacting with the Pi's virtual filesystem. Modern OSs aggressively write hidden metadata files (like `.DS_Store` or `System Volume Information`) to USB drives the moment they are plugged in, which corrupts the strict binary formats required by the SeedSigner OS signing pipeline.
2. **Airgap Integrity:** Plugging the signing device directly into an internet-connected laptop violates strict airgap policies. Using a MicroSD card allows the user to transport the unsigned/signed PSBTs without the physical devices ever communicating electronically.

## 2. SPI Kernel Interception (Hot-Swapping)

Unlike native SDIO slots, SPI-based SD cards do not support hardware interrupts for insertion/removal (Card Detect). If a user removes the SD card, puts it in their laptop, and re-inserts it into the Pi, the Linux kernel will **not** detect the re-insertion, resulting in `No such device` errors.

To solve this without requiring rebooting the Pi, the runner implements a low-level kernel probe intercept. When the user selects a MicroSD action in the UI, the runner executes a `subprocess` call to unbind and rebind the specific SPI driver in `sysfs`:

```bash
echo spi0.0 > /sys/bus/spi/drivers/mmc_spi/unbind
echo spi0.0 > /sys/bus/spi/drivers/mmc_spi/bind
```

This forces the Linux kernel to immediately re-probe the SPI bus, discovering the freshly inserted SD card perfectly every time.

> **SPI Conflict Mitigation:** This re-probe targets specifically `spi0.0` (Chip Select 0). If you are using an SPI E-Paper display, you must wire the E-Paper's CS pin to `spi0.1` (Chip Select 1 / GPIO 7). Because the script only unbinds `spi0.0`, the E-Paper display will never flash or lose connection during SD card hot-swapping!

## 3. Mounting: read-only, and only for one operation

The card is mounted only while an operation runs, and unmounted straight after, even on error:

```bash
# list or read a PSBT: read-only, nothing on the card can change
mount -t vfat -o ro,uid=1000,gid=1000 /dev/mmcblk1p1 /mnt/sd

# write the signed PSBT or xpub: repair first, then read-write
fsck.fat -a -w /dev/mmcblk1p1
mount -t vfat -o rw,uid=1000,gid=1000 /dev/mmcblk1p1 /mnt/sd
```

Why:

- **Reading a PSBT must not modify the card.** Earlier builds ran `fsck.fat -a -w` before every mount, which could rewrite the FAT or recover clusters into new files just from loading a PSBT.
- **A mount left in place breaks hot-swapping.** Earlier builds mounted the card once, read-write, and never unmounted it. After a swap, the Pi kept using its cached view of the previous card. While a FAT is mounted read-write, Linux marks it dirty, and the mark is cleared only on a clean unmount. So every card pulled from the Pi was left dirty.
- **A dirty card is still readable and writable.** Linux mounts a FAT with the dirty bit set; it only warns (`fs/fat/inode.c`). The repair before writing stays, so a card that really was damaged by an unsafe ejection from a laptop gets fixed before anything is written into it.

## 4. Checking it on a real Pi

The kernel overlay and sudoers rules this needs are in [section 1.4 of the Constrained Build Guide](constrained_build_guide.md#14-hardware-configuration--sudoers).

[`tools/verify_microsd_pi.py`](../tools/verify_microsd_pi.py) checks the behaviour above against a real card, interactively:

```bash
python3 tools/verify_microsd_pi.py
```

It walks through three steps:

1. Listing and reading leave the card byte-identical, and leave it unmounted.
2. Writing works, leaves the card unmounted, and leaves the dirty bit clear.
3. A card pulled from a laptop without ejecting it is picked up without a reboot, reads without being changed, and still takes a write.

A passing run on a Pi Zero v1.3 is in [`research/microsd/2026-10-22-pi-zero-verify.txt`](../research/microsd/2026-10-22-pi-zero-verify.txt).

For PSBTs the device can actually sign, [`research/silicon/make_test_psbts.py`](../research/silicon/make_test_psbts.py) builds 1- and 10-input PSBTs owned by the standard BIP39 test mnemonic (`abandon` ×11, then `about`). Copy one onto the card and load that seed on the device. Never use the test mnemonic for real funds.
