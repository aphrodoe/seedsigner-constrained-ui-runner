# Constrained SeedSigner on an ESP32-C3 SuperMini: ESP32-C3FH4, 4MB flash in the
# package, no PSRAM, native USB-Serial/JTAG and no USB-UART bridge. Mirrors
# ESP32_GENERIC_C3 minus sdkconfig.ble, as the S3 board does. The base config's
# 4MiBplus partition table fits: a 1.9MB app slot, the rest becomes the VFS.
set(IDF_TARGET esp32c3)

set(SDKCONFIG_DEFAULTS
    boards/sdkconfig.base
    boards/sdkconfig.riscv
    boards/ESP32_GENERIC_C3/sdkconfig.c3usb
    ${MICROPY_BOARD_DIR}/sdkconfig.board
)
