"""On-device footprint of this repo's text renderer and the bridge: what they cost
to import, and to draw a frame, at two display tiers -- a 20x4 character
LCD and a 128x64 OLED (16x8 characters).

Run on the constrained firmware with src/ frozen (see firmware/manifest.py):

    mpremote run profile_renderer.py

The screens are real upstream cfgs, copied from scenarios/scenarios.json rather
than read from the filesystem, which would compile them on-device and pollute the
heap being measured. 'alloc' (GC disabled) bounds each step's peak; 'retained' is
resident after a collect.
"""
import gc
import sys
import time

import esp32

SCREENS = {'main_menu_screen': {'top_nav': {'title': 'Home',
                                  'show_back_button': False,
                                  'show_power_button': True},
                      'button_list': ['Scan', 'Seeds', 'Tools', 'Settings']},
 'button_list_screen': {'button_list': ['Language',
                                        'Persistent settings',
                                        'Camera rotation',
                                        'Bitcoin network'],
                        'top_nav': {'title': 'Settings',
                                    'show_back_button': True,
                                    'show_power_button': False}},
 'large_icon_status_screen': {'top_nav': {'title': 'Backup Verified',
                                          'show_back_button': False,
                                          'show_power_button': False},
                              'status_type': 'success',
                              'status_headline': 'Success!',
                              'text': 'All mnemonic backup words were successfully verified!',
                              'button_list': ['OK'],
                              'is_bottom_list': True,
                              'warning_edges': False},
 'psbt_overview_screen': {'top_nav': {'title': 'Review Transaction', 'show_back_button': True},
                          'btc_amount': {'primary': '841,234', 'unit': 'sats', 'network': 'M'},
                          'num_inputs': 3,
                          'destination_addresses': ['bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq',
                                                    '3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy'],
                          'num_self_transfer_outputs': 0,
                          'num_change_outputs': 1,
                          'has_op_return': False,
                          'button': 'Review details'},
 'psbt_math_screen': {'top_nav': {'title': 'Transaction Math', 'show_back_button': True},
                      'denomination': 'sats',
                      'num_recipients': 1,
                      'amounts': {'input': '1,000,000',
                                  'spend': '841,234',
                                  'fee': '2,500',
                                  'change': '156,266'},
                      'labels': {'inputs': 'inputs',
                                 'recipients': 'recipients',
                                 'fee': 'fee',
                                 'change': 'sats change'},
                      'button_list': ['Review recipients']},
 'seed_add_passphrase_screen': {'top_nav': {'title': 'BIP-39 Passphrase',
                                            'show_back_button': True,
                                            'show_power_button': False}}}


def internal():
    regs = [r for r in esp32.idf_heap_info(esp32.HEAP_DATA) if r[0] < 1000000]
    return (sum(r[1] for r in regs), max(r[2] for r in regs))


def measure(label, fn):
    gc.collect()
    a0 = gc.mem_alloc()
    i0 = internal()
    gc.disable()
    t0 = time.ticks_ms()
    try:
        result = fn()
    finally:
        ms = time.ticks_diff(time.ticks_ms(), t0)
        a1 = gc.mem_alloc()
        gc.enable()
    gc.collect()
    print("%-36s %5d ms  alloc %7d  retained %6d  int_free %7d -> %7d"
          % (label, ms, a1 - a0, gc.mem_alloc() - a0, i0[0], internal()[0]))
    return result


print("impl ", sys.implementation._machine)
gc.collect()
base = gc.mem_alloc()
print()

measure("import renderer core", lambda: __import__("src.renderers.text_renderer"))
measure("import bridge", lambda: __import__("src.constrained_text_screens"))

from src.renderers.text_renderer import TextRenderer  # noqa: E402
from src.screen_state import ScreenState  # noqa: E402

sample = None
for rows, cols, tier in ((4, 20, "20x4 LCD"), (8, 16, "OLED 16x8")):
    tr = TextRenderer(rows, cols)
    for name, cfg in SCREENS.items():
        frame = measure("%-10s %s" % (tier, name[:-7]),
                        lambda tr=tr, n=name, c=cfg, r=rows: tr.render(ScreenState(n, dict(c), visible_rows=r - 1)))
        assert len(frame) == rows and all(len(line) == cols for line in frame), "malformed frame"
        if sample is None:
            sample = (name, frame)

gc.collect()
print("\nrenderer + bridge resident: %d bytes over baseline" % (gc.mem_alloc() - base))
print("\nfirst frame, rendered on-device (20x4, %s):" % sample[0])
for line in sample[1]:
    print("  |%s|" % line)
