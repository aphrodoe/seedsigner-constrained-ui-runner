#define MICROPY_HW_BOARD_NAME               "SeedSigner constrained, ESP32-C3 SuperMini"
#define MICROPY_HW_MCU_NAME                 "ESP32C3"

// No USB-UART bridge on this board: the REPL is on the native USB-Serial/JTAG.
#define MICROPY_HW_ENABLE_UART_REPL         (0)

// GPIO 8 (the on-board LED) and 9 (BOOT) are strapping pins, but both only need
// to be high at reset, which the I2C pull-ups give them. Same pins as the S3 board,
// so the bridge's display setup needs no per-chip branch.
#define MICROPY_HW_I2C0_SCL                 (9)
#define MICROPY_HW_I2C0_SDA                 (8)

// No radios at the MicroPython level. Same set as the S3 board.
#define MICROPY_PY_NETWORK                  (0)
#define MICROPY_PY_NETWORK_WLAN             (0)
#define MICROPY_PY_NETWORK_LAN              (0)
#define MICROPY_PY_NETWORK_PPP_LWIP         (0)
#define MICROPY_PY_SOCKET                   (0)
#define MICROPY_PY_BLUETOOTH                (0)
#define MICROPY_BLUETOOTH_NIMBLE            (0)
#define MICROPY_PY_ESPNOW                   (0)
