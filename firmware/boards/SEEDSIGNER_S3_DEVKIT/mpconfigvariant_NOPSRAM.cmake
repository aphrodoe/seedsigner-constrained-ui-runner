# C3 proxy: the same board with PSRAM switched off, so the Python heap and every
# thread stack must fit in internal SRAM -- the position an ESP32-C3, which has no
# PSRAM, is in. The S3 still has 512 KB of SRAM to the C3's 400 KB, so this gives an
# optimistic bound, but a direct one.
list(REMOVE_ITEM SDKCONFIG_DEFAULTS
    boards/sdkconfig.spiram_sx
    boards/sdkconfig.spiram_oct
)

# No parentheses or commas in the name: CMake's legacy unquoted-argument parsing
# collapses the whole define to "" if it meets them.
list(APPEND MICROPY_DEF_BOARD
    MICROPY_HW_BOARD_NAME="SeedSigner constrained ESP32-S3 N16R8 PSRAM-off C3-proxy"
)
