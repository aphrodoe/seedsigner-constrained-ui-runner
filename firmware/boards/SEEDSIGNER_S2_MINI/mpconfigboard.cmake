# Constrained SeedSigner on a LOLIN-style S2 Mini: ESP32-S2FN4R2, 4MB flash and 2MB
# quad PSRAM in the package, native USB-OTG and no USB-UART bridge. Mirrors
# LOLIN_S2_MINI (no Bluetooth on the S2 at all) without its frozen extras. The base
# config's 4MiBplus partition table fits, as on the C3. 240 MHz like the S3 board:
# the stock S2 config leaves the CPU at 160.
set(IDF_TARGET esp32s2)

set(SDKCONFIG_DEFAULTS
    boards/sdkconfig.base
    boards/sdkconfig.spiram_sx
    boards/sdkconfig.240mhz
    ${MICROPY_BOARD_DIR}/sdkconfig.board
)
