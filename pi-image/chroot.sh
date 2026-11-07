#!/bin/bash
# Runs inside the image's root filesystem (ARM, emulated as the Pi Zero's
# arm1176), called by build.sh with the repo already cloned to $APP.
# Usage: chroot.sh <dev: 0|1>
set -euo pipefail
DEV="$1"
APP=/home/pi/seedsigner-constrained-ui-runner
FILES="$APP/pi-image/files"
BOOT=/boot/firmware
export DEBIAN_FRONTEND=noninteractive

# Nothing installed here may start a service inside the chroot.
printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d
chmod +x /usr/sbin/policy-rc.d

# setup.sh pulls a submodule and pyzbar from git. piwheels' Pillow links
# against these instead of bundling them (found by ldd on a Pi, 8 Nov).
apt-get update
apt-get install -y --no-install-recommends git \
    libavif16 libfreetype6 liblcms2-2 libopenjp2-7 libwebpdemux2 libwebpmux3

# The app, installed the way docs/constrained_build_guide.md §1.3 says.
# sudo clears the environment, so QEMU_CPU has to be passed on explicitly, or
# pip runs as ARMv7 and installs wheels the Pi Zero can't execute.
sudo -u pi -H --preserve-env=QEMU_CPU bash -c "[ \"\$(uname -m)\" = armv6l ] && cd $APP && ./setup.sh"

# Every compiled module must find its system libraries.
MISSING=$(find "$APP/venv" -name '*.so*' -type f -exec ldd {} \; 2>/dev/null | grep 'not found' | sort -u || true)
if [ -n "$MISSING" ]; then
    echo "$MISSING"; echo "^ libraries the venv needs but the image lacks" >&2; exit 1
fi

# config.json lives on the boot partition, so a builder can pick their display
# from any computer.
mv "$APP/config.json" "$BOOT/seedsigner-config.json"
ln -s "$BOOT/seedsigner-config.json" "$APP/config.json"

# MicroSD over SPI: the overlay from the old install_spi_sd.sh, and the
# sudoers rules from the build guide §1.4.
dtc -@ -I dts -O dtb -o "$BOOT/overlays/spi-sd.dtbo" "$FILES/spi-sd.dts"
install -m 0440 "$FILES/010_seedsigner-sd" /etc/sudoers.d/010_seedsigner-sd
visudo -cf /etc/sudoers.d/010_seedsigner-sd
mkdir -p /mnt/sd

cat >> "$BOOT/config.txt" <<'EOF'

# SeedSigner constrained (pi-image/build.sh)
[all]
dtparam=i2c_arm=on
dtparam=spi=on
dtoverlay=spi-sd
# A signing device has no use for radios (Zero W / 2 W; the v1.3 has none).
dtoverlay=disable-wifi
dtoverlay=disable-bt
EOF
echo i2c-dev > /etc/modules-load.d/i2c-dev.conf

# The image's pi user has no shell and no password; the first-boot wizard would
# wait for a keyboard on tty8. Set the user up here instead.
usermod -s /bin/bash pi
for g in gpio i2c spi dialout; do getent group "$g" >/dev/null && usermod -aG "$g" pi; done
systemctl disable userconfig.service
echo seedsigner > /etc/hostname
sed -i 's/\braspberrypi\b/seedsigner/g' /etc/hosts

install -m 0644 "$FILES/seedsigner.service" /etc/systemd/system/
systemctl enable seedsigner.service

if [ "$DEV" = 1 ]; then
    # USB Ethernet at 10.42.0.2 + SSH as pi/pi, as in pi_zero_usb_workflow.md.
    echo pi:pi | chpasswd
    printf 'dtoverlay=dwc2\n' >> "$BOOT/config.txt"
    sed -i '1 s/$/ modules-load=dwc2,g_ether g_ether.host_addr=00:22:82:ff:ff:20 g_ether.dev_addr=00:22:82:ff:ff:22/' "$BOOT/cmdline.txt"
    install -m 0755 "$FILES/dev/usb-gadget-setup.sh" /usr/local/bin/
    install -m 0644 "$FILES/dev/usb-gadget.service" /etc/systemd/system/
    install -m 0644 "$FILES/dev/99-unmanaged-usb0.conf" /etc/NetworkManager/conf.d/
    systemctl enable usb-gadget.service ssh.service
else
    passwd -l pi
fi

apt-get clean
rm -rf /var/lib/apt/lists/* /home/pi/.cache /root/.cache
rm /usr/sbin/policy-rc.d
