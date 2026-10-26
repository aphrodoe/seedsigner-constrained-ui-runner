"""A realistic signing session with the GC on, for the no-PSRAM (C3 proxy) build.

profile_embit.py and profile_app.py run each step with the GC disabled to bound
its peak. Without PSRAM that bound can exhaust RAM by itself, which says nothing
about real use: no device runs with its GC off. This runs the session the way the
device would -- boot the app, start the Controller, load the text renderer and draw, derive
keys, parse and sign a 10-input PSBT -- with the GC working normally, and records whether each step fits
and how tight internal SRAM gets.

    mpremote run session_c3_proxy.py      (psbt_10in.psbt on the filesystem)

`int_low` is ESP-IDF's summed per-region low-water mark: the tightest internal RAM
has been at any point so far, including transients between the samples.
"""
import gc
import sys
import time

import esp32


def internal():
    regs = [r for r in esp32.idf_heap_info(esp32.HEAP_DATA) if r[0] < 1000000]
    return (sum(r[1] for r in regs), max(r[2] for r in regs), sum(r[3] for r in regs))


def step(label, fn):
    t0 = time.ticks_ms()
    try:
        result = fn()
    except MemoryError:
        print("%-30s OOM" % label)
        raise SystemExit
    ms = time.ticks_diff(time.ticks_ms(), t0)
    gc.collect()
    i = internal()
    print("%-30s %6d ms  gc_alloc %7d  gc_free %7d  int_free %7d  int_largest %7d  int_low %7d"
          % (label, ms, gc.mem_alloc(), gc.mem_free(), i[0], i[1], i[2]))
    return result


def largest_alloc():
    """Biggest single block the heap will still hand out, to within 1 KB."""
    lo, hi = 0, 512 * 1024
    while hi - lo > 1024:
        mid = (lo + hi) // 2
        try:
            b = bytearray(mid)
            del b
            lo = mid
        except MemoryError:
            hi = mid
        gc.collect()
    return lo


print("impl ", sys.implementation._machine)
step("boot (nothing loaded)", lambda: None)


def load_app():
    import seedsigner.controller  # noqa: F401
    for name in ("seed_views", "psbt_views", "scan_views", "settings_views", "tools_views"):
        __import__("seedsigner.views." + name)


step("import app, all views", load_app)
from seedsigner.controller import Controller  # noqa: E402

step("Controller.get_instance()", Controller.get_instance)
step("import thread exited", lambda: time.sleep_ms(1000))

# Two real upstream cfgs (scenarios/scenarios.json), drawn at 20x4 as the device would.
SCREENS = {'main_menu_screen': {'top_nav': {'title': 'Home',
                                  'show_back_button': False,
                                  'show_power_button': True},
                      'button_list': ['Scan', 'Seeds', 'Tools', 'Settings']},
 'psbt_overview_screen': {'top_nav': {'title': 'Review Transaction', 'show_back_button': True},
                          'btc_amount': {'primary': '841,234', 'unit': 'sats', 'network': 'M'},
                          'num_inputs': 3,
                          'destination_addresses': ['bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq',
                                                    '3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy'],
                          'num_self_transfer_outputs': 0,
                          'num_change_outputs': 1,
                          'has_op_return': False,
                          'button': 'Review details'}}


def load_renderer():
    __import__("src.renderers.text_renderer")
    __import__("src.constrained_text_screens")


step("import renderer + bridge", load_renderer)
from src.renderers.text_renderer import TextRenderer  # noqa: E402
from src.screen_state import ScreenState  # noqa: E402

tr = TextRenderer(4, 20)
step("render main menu + PSBT overview", lambda: [tr.render(ScreenState(n, dict(c), visible_rows=3))
                                                   for n, c in SCREENS.items()])

from embit import bip32, bip39, psbt  # noqa: E402

seed = step("bip39 mnemonic->seed", lambda: bip39.mnemonic_to_seed("abandon " * 11 + "about"))
root = step("bip32 root from seed", lambda: bip32.HDKey.from_seed(seed))
step("bip32 m/84h/0h/0h/0/0", lambda: root.derive("m/84h/0h/0h/0/0"))
raw = open("psbt_10in.psbt", "rb").read()
tx = step("psbt parse 10 in", lambda: psbt.PSBT.parse(raw))
sigs = step("psbt sign 10 in", lambda: tx.sign_with(root))
print("signatures: %d of 10%s" % (sigs, "" if sigs == 10 else "  !! FAILED"))

# Read the low-water mark BEFORE probing: the probe deliberately takes the biggest
# block it can, which would otherwise become the "lowest" point of the session.
session_low = internal()[2]
print("\ninternal SRAM low-water over the session: %d bytes" % session_low)
print("largest single allocation still possible: %d bytes" % largest_alloc())

# "total" is the Python heap as it ended up; above the initial size means MicroPython
# grew it during the session (it only grows after a full collection has failed).
import micropython  # noqa: E402
micropython.mem_info()
