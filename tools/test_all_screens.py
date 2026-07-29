#!/usr/bin/env python3
import os
import sys
import time
import json
import traceback

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.json_parser import JSONParser
from src.screen_state import ScreenState
from src.renderers.text_renderer import TextRenderer

# Attempt to load hardware drivers
try:
    from src.drivers.lcd_i2c import LcdI2C
    has_lcd = True
except ImportError:
    has_lcd = False

try:
    from src.drivers.oled_ssd1306 import OledSSD1306
    has_oled = True
except ImportError:
    has_oled = False

try:
    from src.drivers.epaper_waveshare import EpaperWaveshare
    has_epd = True
except ImportError:
    has_epd = False

def init_displays():
    displays = {}
    
    # Tier 0 & 1: LCD
    if has_lcd:
        try:
            # You might need to configure i2c addresses if testing multiple simultaneously
            displays["16x2"] = LcdI2C(address=0x27, rows=2, cols=16)
            print("[OK] Connected to 16x2 LCD")
        except Exception as e:
            print(f"[FAIL] 16x2 LCD init failed: {e}")
            
        try:
            displays["20x4"] = LcdI2C(address=0x3F, rows=4, cols=20)
            print("[OK] Connected to 20x4 LCD")
        except Exception as e:
            print(f"[FAIL] 20x4 LCD init failed: {e}")
            
    # Tier 2: OLED
    if has_oled:
        try:
            displays["16x8"] = OledSSD1306(i2c_port=1, i2c_addr=0x3C, width=128, height=32)
            print("[OK] Connected to 128x32 OLED")
        except Exception as e:
            print(f"[FAIL] OLED init failed: {e}")
            
    # Tier 3: E-Paper
    if has_epd:
        try:
            displays["25x16"] = EpaperWaveshare()
            print("[OK] Connected to 200x200 E-Paper")
        except Exception as e:
            print(f"[FAIL] E-Paper init failed: {e}")
            
    return displays

def get_scenarios():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    scenarios_file = os.path.join(base_dir, 'scenarios/scenarios.json')
    parser = JSONParser(scenarios_file)
    
    synth_path = os.path.join(base_dir, 'scenarios/synthetic_screens.json')
    if os.path.exists(synth_path):
        with open(synth_path, 'r') as f:
            parser.scenarios.update(json.load(f))
            
    return parser

def main():
    print("="*50)
    print("Hardware Screen Walkthrough Tool")
    print("="*50)
    
    displays = init_displays()
    if not displays:
        print("\n[!] No physical displays detected. Exiting.")
        sys.exit(1)
        
    parser = get_scenarios()
    
    # Configuration mapping Tier Name -> (Renderer instance, Hardware Display instance)
    configs = {}
    if "16x2" in displays: configs["16x2"] = (TextRenderer(rows=2, cols=16), displays["16x2"], 1)
    if "20x4" in displays: configs["20x4"] = (TextRenderer(rows=4, cols=20), displays["20x4"], 3)
    if "16x8" in displays: configs["16x8"] = (TextRenderer(rows=8, cols=16), displays["16x8"], 7)
    if "25x16" in displays: configs["25x16"] = (TextRenderer(rows=16, cols=25), displays["25x16"], 15)
    
    for s_name, s_def in parser.scenarios.items():
        variations = [None] + [v.get("name") for v in s_def.get("variations", [])]
        
        for v_name in variations:
            ctx = parser.get_scenario_context(s_name, v_name)
            
            print(f"\n=> Rendering: {s_name} [{v_name or 'default'}]")
            
            for tier_name, (renderer, hw_display, visible_rows) in configs.items():
                try:
                    state = ScreenState(s_name, ctx, visible_rows=visible_rows)
                    lines = renderer.render(state)
                    hw_display.write_lines(lines)
                except Exception as e:
                    print(f"   [FAIL] {tier_name}: {e}")
                    traceback.print_exc()
                
            input("   [?] Press Enter for next screen...")

if __name__ == "__main__":
    main()
