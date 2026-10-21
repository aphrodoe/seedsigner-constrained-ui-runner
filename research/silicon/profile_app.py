"""On-device SeedSigner app footprint: what the frozen app costs in RAM to import
and to instantiate, staged the way Keith's launcher boots it.

Run on the constrained firmware with the app frozen (see firmware/manifest.py):

    mpremote run profile_app.py

Frozen bytecode lives in flash. What importing a frozen module costs is the heap
objects it creates -- its dict, classes, functions, constants -- so `retained`
after a collect is a module's resident cost, and `alloc` (GC disabled) is the upper
bound on the transient peak while it loads. `int_*` is ESP-IDF's internal
(non-PSRAM) data heap: on a part with no PSRAM, everything has to fit there.
"""
import gc
import sys
import time

import esp32


def internal():
    regs = [r for r in esp32.idf_heap_info(esp32.HEAP_DATA) if r[0] < 1000000]
    return (sum(r[1] for r in regs), max(r[2] for r in regs), sum(r[3] for r in regs))


def measure(label, fn):
    gc.collect()
    a0 = gc.mem_alloc()
    i0 = internal()
    gc.disable()
    t0 = time.ticks_ms()
    try:
        fn()
    finally:
        ms = time.ticks_diff(time.ticks_ms(), t0)
        a1 = gc.mem_alloc()
        gc.enable()
    gc.collect()
    i1 = internal()
    print("%-34s %6d ms  alloc %8d  retained %7d  int_free %7d -> %7d"
          % (label, ms, a1 - a0, gc.mem_alloc() - a0, i0[0], i1[0]))


print("impl   ", sys.implementation._machine)
gc.collect()
i = internal()
base = gc.mem_alloc()
print("start  gc_alloc %d  int_free %d  int_largest %d" % (base, i[0], i[1]))
print()


def boot():
    import seedsigner.controller  # noqa: F401


measure("import seedsigner.controller", boot)
for name in ("seed_views", "psbt_views", "scan_views", "settings_views", "tools_views"):
    measure("import views." + name, lambda n=name: __import__("seedsigner.views." + n))

gc.collect()
print("\nwhole app resident: %d bytes over baseline" % (gc.mem_alloc() - base))
print()

try:
    from seedsigner.controller import Controller
    measure("Controller.get_instance()", Controller.get_instance)
except Exception as e:  # where it fails is itself the finding
    print("Controller.get_instance() FAILED:")
    sys.print_exception(e)

gc.collect()
i = internal()
print("\nend    gc_alloc %d  (+%d)  int_free %d  int_largest %d  int_low %d"
      % (gc.mem_alloc(), gc.mem_alloc() - base, i[0], i[1], i[2]))
