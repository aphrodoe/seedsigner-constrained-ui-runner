# Silicon profiling: how small a chip can run SeedSigner?

Which is the cheapest MCU that can run the constrained build? Measured on one
ESP32-S3 N16R8 devkit (16 MB flash, 8 MB octal PSRAM), twice: with PSRAM, and
with PSRAM switched off as a stand-in for an ESP32-C3, which has none. All runs
are on stock MicroPython 1.27.0 plus native secp256k1 and SHA-512/HMAC
(`firmware/`). Raw output is in `results/`.

## What's measured

| | S3, PSRAM | S3, PSRAM off (C3 proxy) |
|---|---|---|
| firmware size, app + embit frozen (PSRAM-off build also has the renderer) | 1.35 MB | 1.41 MB |
| BIP39 mnemonic → seed | 142 ms | 139 ms |
| sign a 10-input PSBT | 616 ms | 620–842 ms |
| SeedSigner app resident (all views imported) | ~92 KB | ~92 KB |
| renderer + bridge resident | — | 14 KB |
| render one frame (20×4 LCD or 16×8 OLED) | — | 6–13 ms |
| full session's live Python heap peak | — | ~136 KB |
| full session: 10 of 10 signatures | yes | yes |

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
   Sizing a C3 needs a fixed heap (patch `MICROPY_GC_SPLIT_HEAP_AUTO` off, set
   `MICROPY_GC_INITIAL_HEAP_SIZE`), not this number.
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

## Recommendation

- **ESP32-S3 works today**, with margin, and is the bring-up target.
- **ESP32-C3 is plausible but not proven.** The S3 has 512 KB of SRAM to the C3's
  400 KB, and a 160 MHz RISC-V core instead of 240 MHz Xtensa, so the proxy is
  optimistic on both memory and speed. A C3 devkit costs a few hundred rupees.
  Running `session_c3_proxy.py` on one, with a fixed heap, settles it.
- **ESP32-S2** (single core, 320 KB SRAM, optional PSRAM, no Bluetooth at all) is
  worth one run for the same reason. **ESP32-C2** (272 KB) looks too small.
  **ESP32-H2** (96 MHz) looks too slow to sign comfortably. Neither is measured.

## Reproduce

```sh
firmware/build.sh SEEDSIGNER_S3_DEVKIT            # or: ... NOPSRAM
# flash with esptool @flash_args from firmware/build/<board>/, hard reset, then:
mpremote run research/silicon/session_c3_proxy.py # first run after hard reset only
mpremote run research/silicon/profile_embit.py
mpremote run research/silicon/profile_app.py
mpremote run research/silicon/profile_renderer.py
```

`make_test_psbts.py` regenerates the deterministic PSBTs the profilers embed.
