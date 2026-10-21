# Crypto-only user C modules: the native secp256k1 and SHA-512 / PBKDF2-HMAC /
# RIPEMD-160 that embit needs on MicroPython, and nothing else -- no LVGL, no
# display manager, no camera. This is the "crypto half" of Keith's usermod.
#
# Both libraries stay ESP-IDF components (passed in via EXTRA_COMPONENT_DIRS) so
# their headers never enter MicroPython's QSTR scan, which cannot evaluate
# mbedtls's generator-expression include dirs. Only the two thin bindings compile
# as part of MicroPython.
#
# Why not INTERFACE_SOURCES, the usual user-module pattern (and the one in
# esp-secp256k1/micropython.cmake)? In stock MicroPython that property is how
# user-module sources get compiled at all: esp32_common.cmake's transitive
# `target_link_libraries(${MICROPY_TARGET} usermod)` hands it to the main
# component. But it hands it on to the final executable too, which compiles every
# binding a second time with bare flags -- no -O2, no -ffunction-sections -- and
# that is the copy the linker keeps. For the secp256k1 binding, unoptimised and in
# one monolithic .text section, Xtensa's L32R literal loads fall outside their
# 256KB range and the link fails. (Invisible on the RISC-V P4: no L32R.)
#
# So the bindings go in two places instead:
#   * MICROPY_SOURCE_USERMOD -- feeds the QSTR scan and the builtin-module table.
#     It does NOT compile anything.
#   * the main component, PRIVATE -- compiled once, with the component's flags, and
#     private sources don't propagate to the executable. The main target doesn't
#     exist yet when user modules are included, so the call is deferred to the end
#     of this directory's scope, when it does.
# ponytail: sources come from the sibling seedsigner-micropython-builder checkout.
# Vendor them as submodules when this graduates from profiling spike to D1 firmware.
set(SS_BUILDER ${CMAKE_CURRENT_LIST_DIR}/../../seedsigner-micropython-builder)

set(_SS_CRYPTO_BINDINGS
    ${SS_BUILDER}/deps/esp-secp256k1/mpy/modsecp256k1.c
    ${SS_BUILDER}/bindings/modhashlibext.c
)
list(APPEND MICROPY_SOURCE_USERMOD ${_SS_CRYPTO_BINDINGS})
list(APPEND MICROPY_INC_USERMOD
    ${SS_BUILDER}/deps/esp-secp256k1/secp256k1-zkp/include
    ${SS_BUILDER}/deps/esp-hashlib-ext
)

# Read inside a function so MICROPY_TARGET resolves when the call runs, not now.
function(_ss_compile_crypto_bindings)
    target_sources(${MICROPY_TARGET} PRIVATE ${_SS_CRYPTO_BINDINGS})
endfunction()
cmake_language(DEFER CALL _ss_compile_crypto_bindings)

# Link only -- no sources -- so nothing propagates to the executable but the libs.
target_link_libraries(usermod INTERFACE __idf_esp-secp256k1 __idf_esp-hashlib-ext)
