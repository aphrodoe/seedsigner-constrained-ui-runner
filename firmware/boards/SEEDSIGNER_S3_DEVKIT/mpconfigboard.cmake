# Constrained SeedSigner on an ESP32-S3 devkit: N16R8 (16MB flash, 8MB octal PSRAM).
# Mirrors ESP32_GENERIC_S3 + its SPIRAM_OCT variant, minus sdkconfig.ble: a
# signing device has no use for Bluetooth.
set(IDF_TARGET esp32s3)

# ESP-IDF resolves a custom partition CSV against the project dir (ports/esp32),
# where this out-of-tree board's CSV doesn't live, but passes absolute paths
# through. Generate the one line that needs one, so nothing absolute is committed.
set(_ss_partitions ${CMAKE_BINARY_DIR}/sdkconfig.partitions)
file(WRITE ${_ss_partitions}
    "CONFIG_PARTITION_TABLE_CUSTOM_FILENAME=\"${MICROPY_BOARD_DIR}/partitions-16MiB.csv\"\n")

set(SDKCONFIG_DEFAULTS
    boards/sdkconfig.base
    boards/sdkconfig.spiram_sx
    boards/sdkconfig.240mhz
    boards/sdkconfig.spiram_oct
    ${MICROPY_BOARD_DIR}/sdkconfig.board
    ${_ss_partitions}
)
