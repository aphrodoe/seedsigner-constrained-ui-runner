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

> [!NOTE]
> **SPI Conflict Mitigation:** This re-probe targets specifically `spi0.0` (Chip Select 0). If you are using an SPI E-Paper display, you must wire the E-Paper's CS pin to `spi0.1` (Chip Select 1 / GPIO 7). Because the script only unbinds `spi0.0`, the E-Paper display will never flash or lose connection during SD card hot-swapping!

## 3. Automated Filesystem Repair (`fsck.fat`)

A major issue with airgapped workflows is "lazy ejection." If a user unplugs the SD card from their laptop without safely ejecting it, the FAT32 filesystem is marked with a "dirty bit."

When the Pi attempts to mount a dirty FAT32 partition via the SPI bus, the kernel refuses to mount it in Read-Write mode to protect data integrity, which causes the entire signing flow to crash when it attempts to save the signed PSBT.

To guarantee flawlessly robust operation, the `MicroSDManager` intercepts the mount command and forcefully runs a non-interactive filesystem repair just milliseconds before mounting:

```bash
fsck.fat -a -w /dev/mmcblk2p1
mount -t vfat -o uid=1000,gid=1000 /dev/mmcblk2p1 /mnt/sd
```

This instantly clears the dirty bit and recovers any orphaned clusters, ensuring the SD card is always ready for I/O operations without user intervention.
