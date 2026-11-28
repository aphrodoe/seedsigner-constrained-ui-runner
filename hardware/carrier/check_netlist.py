#!/usr/bin/env python3
"""Check the carrier schematic against connections.md.

    python3 hardware/carrier/check_netlist.py carrier.kicad_sch [--kicad-cli CMD]
    python3 hardware/carrier/check_netlist.py carrier.net        # an exported netlist
    python3 hardware/carrier/check_netlist.py --selftest

Exports the netlist with kicad-cli, then reports every pin on the wrong net, every
expected part that's missing, and every part this file doesn't know about.
For a KiCad AppImage:  --kicad-cli "~/Applications/kicad-10.0.8-x86_64.AppImage kicad-cli"
"""
import os
import re
import shlex
import subprocess
import sys
import tempfile

NC = None  # pin must not be connected to anything

# Multi-pin parts: (ref, pin) -> net.
PINS = {}
J1 = ["EN", "KEY1", "KEY3", "KEY2", "DOWN", "UP", "RIGHT", "LEFT",
      "SCL", "SDA", NC, "ENTER", NC, NC, "+3V3", NC]
J2 = ["DISP_RST", "DISP_DC", "DISP_CS", "SPI_MISO", "SPI_SCK", "SPI_MOSI", "SD_CS", "DISP_BUSY",
      NC, NC, NC, NC, "GND", "GND", NC, "VBUS"]
J3 = ["P1", "P2", "SCL_D", "SDA_D"]
J4 = ["+3V3", "GND", "SPI_MOSI", "SPI_SCK", "DISP_CS", "DISP_DC", "DISP_RST", "DISP_BUSY"]
J6 = ["GND", "+3V3", "SPI_MISO", "SPI_MOSI", "SPI_SCK", "SD_CS"]
for ref, nets in (("J1", J1), ("J2", J2), ("J3", J3), ("J4", J4), ("J6", J6)):
    for i, net in enumerate(nets, 1):
        PINS[(ref, str(i))] = net
PINS.update({
    ("SW1", "1"): "UP", ("SW1", "2"): "LEFT", ("SW1", "3"): "DOWN",
    ("SW1", "4"): "GND", ("SW1", "5"): "RIGHT", ("SW1", "6"): "ENTER",
    ("J5", "1"): "SD_DAT2", ("J5", "2"): "SD_CS", ("J5", "3"): "SPI_MOSI", ("J5", "4"): "+3V3",
    ("J5", "5"): "SPI_SCK", ("J5", "6"): "GND", ("J5", "7"): "SPI_MISO", ("J5", "8"): "SD_DAT1",
    ("J5", "9"): NC, ("J5", "10"): "GND", ("J5", "11"): "GND", ("J5", "12"): "GND", ("J5", "13"): "GND",
    # SolderJumper_3: pin 2 is the common (centre) pad.
    ("JP1", "1"): "GND", ("JP1", "2"): "P1", ("JP1", "3"): "VDISP",
    ("JP2", "1"): "GND", ("JP2", "2"): "P2", ("JP2", "3"): "VDISP",
    ("JP3", "1"): "+3V3", ("JP3", "2"): "VDISP", ("JP3", "3"): "VBUS",
    # BSS138: 1 gate, 2 source (S2 side), 3 drain (display side).
    ("Q1", "1"): "+3V3", ("Q1", "2"): "SDA", ("Q1", "3"): "SDA_D",
    ("Q2", "1"): "+3V3", ("Q2", "2"): "SCL", ("Q2", "3"): "SCL_D",
})

# Two-pin parts, either way round: ref -> {net, net}.
PAIRS = {
    "SW2": {"UP", "GND"}, "SW3": {"DOWN", "GND"}, "SW4": {"LEFT", "GND"},
    "SW5": {"RIGHT", "GND"}, "SW6": {"ENTER", "GND"},
    "SW7": {"KEY1", "GND"}, "SW8": {"KEY2", "GND"}, "SW9": {"KEY3", "GND"},
    "R1": {"EN", "+3V3"}, "C1": {"EN", "GND"},
    "R2": {"SDA", "+3V3"}, "R3": {"SCL", "+3V3"},
    "R4": {"SDA_D", "VDISP"}, "R5": {"SCL_D", "VDISP"},
    "JP4": {"SDA", "SDA_D"}, "JP5": {"SCL", "SCL_D"}, "C2": {"VDISP", "GND"},
    "R6": {"SD_DAT2", "+3V3"}, "R7": {"SD_CS", "+3V3"}, "R8": {"SPI_MOSI", "+3V3"},
    "R9": {"SPI_MISO", "+3V3"}, "R10": {"SD_DAT1", "+3V3"},
    "C3": {"+3V3", "GND"}, "C4": {"+3V3", "GND"},
}
NO_PINS = {"H1", "H2", "H3", "H4"}


def parse(text):
    """KiCad s-expression netlist -> {(ref, pin): net name}, unconnected pins as None."""
    pins = {}
    text = re.sub(r"\s+", " ", text)  # KiCad 10 writes one field per line
    for block in re.split(r"\(net \(code", text)[1:]:
        name = re.search(r'\(name "([^"]*)"', block).group(1).lstrip("/")
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', block)
        # A labelled pin keeps its net name even before the other end is drawn.
        real = None if name.startswith("unconnected-") else name
        for node in nodes:
            pins[node] = real
    return pins


def check(pins):
    errors = []
    refs = {ref for ref, _ in pins}
    for (ref, pin), want in sorted(PINS.items()):
        got = pins.get((ref, pin), "MISSING")
        if got != want:
            errors.append(f"{ref} pin {pin}: expected {want or 'no connection'}, got {got or 'no connection'}")
    for ref, want in sorted(PAIRS.items()):
        got = {net for (r, _), net in pins.items() if r == ref}
        if got != want:
            errors.append(f"{ref}: expected between {sorted(want)}, got {sorted(got, key=str) or 'MISSING'}")
    known = {r for r, _ in PINS} | set(PAIRS) | NO_PINS
    errors += [f"{ref}: not in connections.md" for ref in sorted(refs - known)]
    return errors


def selftest():
    good = dict(PINS)
    for ref, nets in PAIRS.items():
        a, b = sorted(nets)
        good[(ref, "1")], good[(ref, "2")] = b, a
    def netlist(pins):
        by_net = {}
        for (ref, pin), net in pins.items():
            by_net.setdefault(net or f"unconnected-({ref}-{pin})", []).append((ref, pin))
        return "".join(f'(net (code "{i}") (name "/{n}")' + "".join(
            f' (node (ref "{r}") (pin "{p}"))' for r, p in nodes) + ")"
            for i, (n, nodes) in enumerate(by_net.items()))
    assert check(parse(netlist(good))) == [], check(parse(netlist(good)))
    bad = {**good, ("J1", "6"): "DOWN"}  # UP wired to DOWN by mistake
    assert any("J1 pin 6" in e for e in check(parse(netlist(bad))))
    print("selftest ok")


def main(argv):
    if argv[:1] == ["--selftest"]:
        return selftest()
    path, cli = argv[0], "kicad-cli"
    if "--kicad-cli" in argv:
        cli = argv[argv.index("--kicad-cli") + 1]
    if path.endswith(".kicad_sch"):
        out = os.path.join(tempfile.mkdtemp(), "carrier.net")
        subprocess.run(shlex.split(os.path.expanduser(cli)) +
                       ["sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, path], check=True)
        path = out
    errors = check(parse(open(path).read()))
    print("\n".join(errors) or "Netlist matches connections.md.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
