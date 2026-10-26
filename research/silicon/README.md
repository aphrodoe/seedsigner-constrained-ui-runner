# Silicon profiling: how small a chip can run SeedSigner?

Which is the cheapest MCU that can run the constrained build? Measured on one
ESP32-S3 N16R8 devkit (16 MB flash, 8 MB octal PSRAM), twice: with PSRAM, and
with PSRAM switched off as a stand-in for an ESP32-C3, which has none; then on a
real ESP32-C3 SuperMini (ESP32-C3FH4: 400 KB SRAM, 4 MB flash in the package, no
PSRAM). All runs are on stock MicroPython 1.27.0 plus native secp256k1 and SHA-512/HMAC
(`firmware/`). Raw output is in `results/`.

## What's measured

| | S3, PSRAM | S3, PSRAM off (C3 proxy) | C3 SuperMini |
|---|---|---|---|
| firmware size, app + embit frozen (PSRAM-off build also has the renderer) | 1.35 MB | 1.41 MB | 1.32 MB (also has the renderer) |
| BIP39 mnemonic → seed | 142 ms | 139 ms | 724 ms |
| sign a 10-input PSBT | 616 ms | 620–842 ms | 881 ms |
| SeedSigner app resident (all views imported) | ~92 KB | ~92 KB | ~92 KB |
| renderer + bridge resident | — | 14 KB | 12 KB |
| render one frame (20×4 LCD or 16×8 OLED) | — | 6–13 ms | ~13 ms |
| full session's live Python heap peak | — | ~136 KB | ~135 KB |
| full session: 10 of 10 signatures | yes | yes | yes |

The session (`session_c3_proxy.py`) is boot → import the app and every view →
`Controller.get_instance()` → render the main menu and a PSBT overview → derive a
seed → parse and sign a 10-input PSBT, GC on, with no PSRAM to fall back on.

## Findings

1. **The whole stack fits in internal SRAM.** Without PSRAM the session completes.
   Its live Python heap peaks at ~136 KB, and the S3 boots with 286 KB of internal
   SRAM free.
2. **The internal-SRAM low-water mark measures MicroPython's growth policy, not the
   app.** The esp32 port grows its heap in steps of about the current heap size
   (`gc_try_add_heap`). The same session bottomed out at 186 KB free in one run and
   88 KB in another, depending on whether one allocation happened to miss. In the
   88 KB run, 170 KB of the Python heap was still empty right after the step.
   On the real C3 the two runs matched to the byte, so the yes/no answer there
   stands; an exact headroom figure would still need a fixed heap (patch
   `MICROPY_GC_SPLIT_HEAP_AUTO` off, set `MICROPY_GC_INITIAL_HEAP_SIZE`).
3. **Threads cost internal SRAM.** `BackgroundImportThread` takes a 32 KiB stack
   (`seedsigner/compat/threading.py`, sized assuming PSRAM) from internal SRAM even
   when PSRAM exists. The single-threaded facade planned for Month 3 removes it.
4. **The renderer had never run on MicroPython.** It took four fixes to get there:
   an unguarded `typing` import; `textwrap` and `base64`, which MicroPython doesn't
   ship; padding, which MicroPython measures in UTF-8 bytes; and dict order, which
   it doesn't keep. Now all 12 test frames match CPython byte for byte, and
   `tests/test_micropython_imports.py` keeps it that way.
5. **Radios are dead weight.** Turning Bluetooth off in sdkconfig freed ~68 KiB of
   internal SRAM (268 → 336 KiB).
6. **A real ESP32-C3 runs the whole session.** It boots with a 64 KB Python heap
   and 230 KB of internal SRAM free; the heap grows to 240 KB as the session needs
   it. At the tightest point 48 KB of internal SRAM was left, and afterwards the
   largest single allocation still possible was 26 KB. That's enough for this
   session but not generous: the 105 KB free inside the Python heap at the end is
   fragmented into small pieces, so much larger PSBTs are the thing to watch.
7. **Seed derivation is 5× slower on the C3 because it has no SHA-512 hardware.**
   BIP39 is 2,048 rounds of HMAC-SHA512. The S3's SHA accelerator does SHA-512
   (`SOC_SHA_SUPPORT_SHA512` in ESP-IDF's `soc_caps.h`); the C3's stops at
   SHA-256, so mbedtls falls back to software. 724 ms happens once per seed load,
   so it's slow but usable. Signing is 1.4× slower, about the clock ratio
   (160 MHz RISC-V vs 240 MHz Xtensa).

## Recommendation

- **ESP32-S3 works today**, with margin, and is the bring-up target.
- **ESP32-C3 works too**, measured on a real board: the full session signs 10 of
  10 inputs in under a second, with less margin than the S3 (48 KB of internal
  SRAM left at the tightest point). The cheapest chip measured so far.
- **ESP32-S2** (single core, 320 KB SRAM, optional PSRAM, no Bluetooth at all) is
  worth one run: less SRAM than the C3, but SHA-512 hardware
  (`SOC_SHA_SUPPORT_SHA512`) and, on the S2 Mini, 2 MB of PSRAM. **ESP32-C2** (272 KB) looks too small.
  **ESP32-H2** (96 MHz) looks too slow to sign comfortably. Neither is measured.

## Reproduce

```sh
firmware/build.sh SEEDSIGNER_S3_DEVKIT            # or: ... NOPSRAM
firmware/build.sh SEEDSIGNER_C3_SUPERMINI
# flash with esptool @flash_args from firmware/build/<board>/, hard reset, then:
mpremote run research/silicon/session_c3_proxy.py # first run after hard reset only
mpremote run research/silicon/profile_embit.py
mpremote run research/silicon/profile_app.py
mpremote run research/silicon/profile_renderer.py
```

`make_test_psbts.py` regenerates the deterministic PSBTs the profilers embed.
