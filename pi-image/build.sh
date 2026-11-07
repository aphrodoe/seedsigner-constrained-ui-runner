#!/bin/bash
# Build a flashable Raspberry Pi Zero image of the constrained SeedSigner:
# Raspberry Pi OS Lite (32-bit) + this repo installed by setup.sh, the MicroSD
# overlay and sudoers rules, and a service that starts SeedSigner at boot.
#
#   pi-image/build.sh          -> pi-image/build/<name>.img.xz (no login, no SSH)
#   pi-image/build.sh --dev    -> also USB Ethernet at 10.42.0.2 and SSH as pi/pi
#
# Builds from the committed HEAD of this repo. Needs Docker (run privileged, for
# loop devices and ARM emulation) and ~8 GB free. No sudo on the host.
set -euo pipefail

BASE_URL=https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2026-10-06/2026-10-06-raspios-trixie-armhf-lite.img.xz
BASE_SHA256=2c302771f34c67a0b7ae7aa2e0dcdd3eac660504be59193c011ba79d412e1632
GROW=512M    # room for the install (~0.8 GB left after it); fits a 4 GB card. The Pi grows the partition to the card on first boot

if [ "${1:-}" = --inside ]; then
    DEV="$2" NAME="$3"
    cd /work
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
        ca-certificates curl git xz-utils fdisk e2fsprogs qemu-user-static binutils >/dev/null

    # ARM binaries in the chroot run under QEMU. F = the interpreter is opened
    # now, so it works inside the chroot. Global to the host kernel until reboot.
    mountpoint -q /proc/sys/fs/binfmt_misc || mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc
    [ -e /proc/sys/fs/binfmt_misc/qemu-arm ] || cat /usr/lib/binfmt.d/qemu-arm.conf > /proc/sys/fs/binfmt_misc/register

    BASE=$(basename "$BASE_URL")
    [ -f "$BASE" ] || curl -fsSLo "$BASE" "$BASE_URL"
    echo "$BASE_SHA256  $BASE" | sha256sum -c -
    xz -dc "$BASE" > "$NAME.img"
    truncate -s +"$GROW" "$NAME.img"
    echo ', +' | sfdisk -q -N 2 "$NAME.img"

    # Partition devices (loopNp1) don't appear inside containers; use offsets.
    # The container's /dev is a snapshot: the free loop device the kernel picks
    # may have no node here, so make it.
    loop() {
        read -r s n < <(partx -g -o START,SECTORS -n "$1" "$NAME.img")
        local dev; dev=$(losetup -f | cut -d" " -f1)   # may print "/dev/loopN (lost)"
        [ -b "$dev" ] || mknod "$dev" b 7 "${dev#/dev/loop}"
        losetup -o $((s*512)) --sizelimit $((n*512)) "$dev" "$NAME.img" && echo "$dev"
    }
    BOOTDEV=$(loop 1)
    ROOTDEV=$(loop 2)
    trap 'umount -R /mnt 2>/dev/null; losetup -d "$ROOTDEV" "$BOOTDEV" 2>/dev/null' EXIT
    e2fsck -pf "$ROOTDEV" || [ $? -le 1 ]   # 1 = fixed something, fine
    resize2fs -p "$ROOTDEV"
    mount "$ROOTDEV" /mnt
    mount "$BOOTDEV" /mnt/boot/firmware
    for d in proc sys dev dev/pts; do mount --bind /$d /mnt/$d; done

    APP=/mnt/home/pi/seedsigner-constrained-ui-runner
    git config --global --add safe.directory '*'
    git clone -q --depth 1 --recurse-submodules --shallow-submodules file:///src "$APP"
    git -C "$APP" remote set-url origin https://github.com/aphrodoe/seedsigner-constrained-ui-runner.git
    chown -R 1000:1000 "$APP"

    cp --remove-destination /etc/resolv.conf /mnt/etc/resolv.conf.build
    mv /mnt/etc/resolv.conf /mnt/etc/resolv.conf.orig
    mv /mnt/etc/resolv.conf.build /mnt/etc/resolv.conf
    # arm1176 = the Pi Zero's CPU, so pip picks ARMv6 wheels, not ARMv7 ones.
    QEMU_CPU=arm1176 chroot /mnt /bin/bash "/home/pi/seedsigner-constrained-ui-runner/pi-image/chroot.sh" "$DEV"
    mv /mnt/etc/resolv.conf.orig /mnt/etc/resolv.conf

    # Every compiled module in the venv must be built for ARMv6. Not the wheel
    # tags: piwheels publishes the same ARMv6 builds under armv7l tags.
    ARCHS=$(find "$APP/venv" -name '*.so*' -type f -exec readelf -A {} \; | sed -n 's/.*Tag_CPU_arch: //p' | sort | uniq -c)
    echo "compiled modules by CPU architecture:"; echo "$ARCHS"
    if echo "$ARCHS" | grep -qvE ' v(4T|5TE|6|6KZ)$'; then
        echo "^ code the Pi Zero (ARMv6) can't run" >&2; exit 1
    fi

    umount -R /mnt
    e2fsck -pf "$ROOTDEV" || [ $? -le 1 ]
    losetup -d "$ROOTDEV" "$BOOTDEV"
    trap - EXIT
    xz -T0 -6 -f "$NAME.img"
    sha256sum "$NAME.img.xz" > "$NAME.img.xz.sha256"
    chown "$OWNER" "$NAME.img.xz" "$NAME.img.xz.sha256"
    exit 0
fi

DEV=0 SUFFIX=
if [ "${1:-}" = --dev ]; then DEV=1 SUFFIX=-dev; fi
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
OUT="$REPO/pi-image/build"
NAME="seedsigner-constrained-pi0-$(date +%Y%m%d)-$(git -C "$REPO" rev-parse --short HEAD)$SUFFIX"
[ -z "$(git -C "$REPO" status --porcelain --untracked-files=no)" ] || echo "note: uncommitted changes are not in the image (it builds HEAD)" >&2
mkdir -p "$OUT"

docker run --rm --privileged \
    -e OWNER="$(id -u):$(id -g)" -e BASE_URL="$BASE_URL" -e BASE_SHA256="$BASE_SHA256" -e GROW="$GROW" \
    -v "$REPO:/src:ro" -v "$OUT:/work" -v "$REPO/pi-image/build.sh:/build.sh:ro" \
    debian:trixie-slim bash /build.sh --inside "$DEV" "$NAME"

echo "built: $OUT/$NAME.img.xz"
