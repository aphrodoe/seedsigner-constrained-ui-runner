#ifndef MICROPY_HW_BOARD_NAME
// Can be set by a variant (see mpconfigvariant_*.cmake).
#define MICROPY_HW_BOARD_NAME               "SeedSigner constrained, ESP32-S2 Mini"
#endif
#define MICROPY_HW_MCU_NAME                 "ESP32-S2FN4R2"

// No USB-UART bridge on this board: the REPL is on the native USB.
#define MICROPY_HW_ENABLE_UART_REPL         (0)

// Same pins as the S3 and C3 boards, so the bridge's display setup needs no
// per-chip branch. (LOLIN's own default is SCL 35 / SDA 33.)
#define MICROPY_HW_I2C0_SCL                 (9)
#define MICROPY_HW_I2C0_SDA                 (8)

// No radios at the MicroPython level. Same set as the S3 board; the S2 has no
// Bluetooth hardware.
#define MICROPY_PY_NETWORK                  (0)
#define MICROPY_PY_NETWORK_WLAN             (0)
#define MICROPY_PY_NETWORK_LAN              (0)
#define MICROPY_PY_NETWORK_PPP_LWIP         (0)
#define MICROPY_PY_SOCKET                   (0)
#define MICROPY_PY_BLUETOOTH                (0)
#define MICROPY_BLUETOOTH_NIMBLE            (0)
#define MICROPY_PY_ESPNOW                   (0)
