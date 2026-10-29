# The same board with PSRAM switched off: the position of an ESP32-S2FN4, the
# PSRAM-less part, with 320 KB of SRAM to the C3's 400 KB.
list(REMOVE_ITEM SDKCONFIG_DEFAULTS boards/sdkconfig.spiram_sx)

# No parentheses or commas in the name: see the S3 board's NOPSRAM variant.
list(APPEND MICROPY_DEF_BOARD
    MICROPY_HW_BOARD_NAME="SeedSigner constrained ESP32-S2 Mini PSRAM-off"
)
