"""On-device embit profile: heap and time for the operations a signer runs.

Run on MicroPython with embit, the hashlib.py + hmac.py shims from seedsigner-micropython-builder, and the two
test PSBTs on the filesystem:

    mpremote run profile_embit.py

Methodology
-----------
* Code loading is measured ONCE, as its own line. On the filesystem embit's
  bytecode lives in the GC heap; in a frozen build it lives in flash and costs
  no RAM. So the import line is NOT part of any operation's footprint.
* Each operation runs with the GC disabled: `alloc` is every byte allocated
  during it, an UPPER BOUND on its peak working set. `retained` is what is
  still live after a collect. The true peak lies between them.
* `int_free` / `int_low` track ESP-IDF's internal (non-PSRAM) data heap, where
  native code such as libsecp256k1 allocates. `int_low` is the summed per-region
  low-water mark — the tightest internal memory got, ever.
"""
import gc
import sys
import time

import esp32

# --- refuse to profile the wrong thing -------------------------------------
try:
    import secp256k1  # noqa: F401  native module, not embit's py fallback
except ImportError:
    raise SystemExit("ABORT: no native secp256k1 -- embit would silently use "
                     "py_secp256k1 and every number below would be wrong")
import hashlib
if not hasattr(hashlib, "sha512") or not hasattr(hashlib, "pbkdf2_hmac"):
    raise SystemExit("ABORT: hashlib lacks sha512/pbkdf2_hmac -- hashlib.py shim missing")


def internal():
    regs = [r for r in esp32.idf_heap_info(esp32.HEAP_DATA) if r[0] < 1000000]
    return (sum(r[1] for r in regs), max(r[2] for r in regs), sum(r[3] for r in regs))


def row(label, ms, alloc, retained, i0, i1):
    print("%-24s %7d ms  alloc %8d  retained %7d  int_free %7d -> %7d  int_low %7d"
          % (label, ms, alloc, retained, i0[0], i1[0], i1[2]))


def measure(label, fn):
    gc.collect()
    a0 = gc.mem_alloc()
    i0 = internal()
    gc.disable()
    t0 = time.ticks_ms()
    result = fn()
    ms = time.ticks_diff(time.ticks_ms(), t0)
    a1 = gc.mem_alloc()
    gc.enable()
    gc.collect()
    row(label, ms, a1 - a0, gc.mem_alloc() - a0, i0, internal())
    return result


print("impl   ", sys.implementation._machine)
print("version", sys.version)
gc.collect()
i = internal()
print("start  gc_alloc %d  gc_free %d  int_free %d  int_largest %d  int_low %d"
      % (gc.mem_alloc(), gc.mem_free(), i[0], i[1], i[2]))
print()


def load():
    from embit import bip32, bip39, psbt  # noqa: F401


measure("import embit (code load)", load)
from embit import bip32, bip39, psbt  # already loaded; binds names

MNEMONIC = "abandon " * 11 + "about"
seed = measure("bip39 mnemonic->seed", lambda: bip39.mnemonic_to_seed(MNEMONIC))
root = measure("bip32 root from seed", lambda: bip32.HDKey.from_seed(seed))
measure("bip32 m/84h/0h/0h/0/0", lambda: root.derive("m/84h/0h/0h/0/0"))

for n in (1, 10):
    raw = open("psbt_%din.psbt" % n, "rb").read()
    tx = measure("psbt parse   %2d in" % n, lambda: psbt.PSBT.parse(raw))
    sigs = measure("psbt sign    %2d in" % n, lambda: tx.sign_with(root))
    if sigs != n:
        print("  !! expected %d signatures, got %d" % (n, sigs))

print()
gc.collect()
i = internal()
print("end    gc_alloc %d  int_free %d  int_largest %d  int_low %d"
      % (gc.mem_alloc(), i[0], i[1], i[2]))
