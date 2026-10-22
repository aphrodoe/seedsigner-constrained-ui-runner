"""Check src/hardware/microsd.py against a real card on the Pi, interactively.

    python3 tools/verify_microsd_pi.py

Needs the SPI card reader set up as in docs/constrained_build_guide.md, and a card
holding at least one .psbt/.txt/.json file, last ejected safely. It checks:

1. listing and reading leave the card byte-identical, and leave it unmounted;
2. writing works, and leaves the card unmounted with a clean dirty bit;
3. a card pulled from a laptop without ejecting it is picked up without a reboot,
   reads without being changed, and still takes a write.

"Byte-identical" is checked on the partition's first 64 MiB: the boot sector, both
FATs and the start of the data area on a small card. Hashing all of it over SPI
would take hours.
"""
import hashlib
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.hardware.microsd import MicroSDManager as SD  # noqa: E402

HEAD = 64 * 1024 * 1024
failures = []


def check(ok, what):
    print(("  PASS  " if ok else "  FAIL  ") + what)
    if not ok:
        failures.append(what)


def device():
    return next((d for d in SD.DEVICES if os.path.exists(d)), None)


def card_hash(dev):
    out = subprocess.run(["sudo", "head", "-c", str(HEAD), dev], capture_output=True, check=True).stdout
    return hashlib.sha256(out).hexdigest()


def dirty(dev):
    """fsck.fat -n only reads: it reports, it never repairs."""
    out = subprocess.run(["sudo", "fsck.fat", "-n", dev], capture_output=True, text=True)
    return "dirty bit" in (out.stdout + out.stderr).lower()


def step(title, prompt):
    print("\n== " + title)
    input("   " + prompt + " Then press Enter. ")


step("1. Reading changes nothing",
     "Insert a card holding a .psbt/.txt/.json file, last ejected safely.")
SD.list_files()  # lets the module rescan the SPI bus if the node isn't there yet
dev = device()
if not dev:
    sys.exit("No card device found under " + ", ".join(SD.DEVICES))
print("   card:", dev)
before = card_hash(dev)
files = SD.list_files()
data = SD.read_file(files[0]) if files else b""
check(bool(files) and bool(data), "listed %d file(s), read %s (%d bytes)" % (len(files), files[:1], len(data)))
check(not SD.is_mounted(), "unmounted after list and read")
check(card_hash(dev) == before, "card byte-identical after list and read")

print("\n== 2. Writing")
stamp = time.strftime("%Y-%m-%d %H:%M:%S").encode()
SD.write_file("verify_microsd.txt", b"written by verify_microsd_pi.py at " + stamp)
check(not SD.is_mounted(), "unmounted after write")
check(stamp in SD.read_file("verify_microsd.txt"), "write reads back")
check(not dirty(dev), "dirty bit clear after write")

step("3. Card pulled from a laptop without ejecting",
     "Take the card to your laptop, copy any new file named laptop_<something>.txt onto it, "
     "and pull the card out WITHOUT ejecting. Put it back in the Pi.")
was_dirty = dirty(dev)
print("   laptop left the dirty bit set:", was_dirty, "(depends on the laptop's OS; informational)")
before = card_hash(dev)
files = SD.list_files()
check(any(f.startswith("laptop_") for f in files), "new laptop file listed without a reboot: %s" % files)
check(card_hash(dev) == before, "card byte-identical after listing it")
SD.write_file("verify_microsd.txt", b"second write at " + time.strftime("%H:%M:%S").encode())
check(b"second write" in SD.read_file("verify_microsd.txt"), "write after an unsafe ejection works")
check(not SD.is_mounted(), "unmounted at the end")

print("\n%s: %d check(s) failed" % ("FAILED" if failures else "ALL PASSED", len(failures)))
for f in failures:
    print("  - " + f)
