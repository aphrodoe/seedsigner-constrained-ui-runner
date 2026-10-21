#ifndef MICROPY_HW_BOARD_NAME
// Can be set by a variant (see mpconfigvariant_*.cmake).
#define MICROPY_HW_BOARD_NAME               "SeedSigner constrained, ESP32-S3 N16R8"
#endif
#define MICROPY_HW_MCU_NAME                 "ESP32S3"

// The devkit's CH343P bridge sits on UART0; keep the REPL there.
#define MICROPY_HW_ENABLE_UART_REPL         (1)

#define MICROPY_HW_I2C0_SCL                 (9)
#define MICROPY_HW_I2C0_SDA                 (8)

// No radios at the MicroPython level. Same set Keith's S3 boards disable.
#define MICROPY_PY_NETWORK                  (0)
#define MICROPY_PY_NETWORK_WLAN             (0)
#define MICROPY_PY_NETWORK_LAN              (0)
#define MICROPY_PY_NETWORK_PPP_LWIP         (0)
#define MICROPY_PY_SOCKET                   (0)
#define MICROPY_PY_BLUETOOTH                (0)
#define MICROPY_BLUETOOTH_NIMBLE            (0)
#define MICROPY_PY_ESPNOW                   (0)
