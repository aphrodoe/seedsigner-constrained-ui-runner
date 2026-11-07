#!/bin/bash
# --dev images only: bring up USB Ethernet (g_ether) as 10.42.0.2, bypassing
# NetworkManager, which ignores usb0 (see 99-unmanaged-usb0.conf).
for i in $(seq 1 120); do
    if /sbin/ip link show usb0 > /dev/null 2>&1; then
        /sbin/ip link set usb0 up
        /sbin/ip addr add 10.42.0.2/24 dev usb0 2>/dev/null
        exit 0
    fi
    sleep 1
done
echo "usb0 never appeared after 120 s" >&2
exit 1
