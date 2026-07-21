import json
import os
from src.renderers.base_renderer import BaseRenderer

class DisplayManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def create_renderer(self) -> BaseRenderer:
        display_type = self.config.get("display", {}).get("type", "lcd_20x4_sim")

        # ── Hardware character LCDs ──────────────────────────────────
        if display_type == "lcd_16x2":
            from src.renderers.lcd_hardware_renderer import LCDHardwareRenderer
            return LCDHardwareRenderer(rows=2, cols=16)
        elif display_type == "lcd_20x4":
            from src.renderers.lcd_hardware_renderer import LCDHardwareRenderer
            return LCDHardwareRenderer(rows=4, cols=20)

        # ── Terminal simulators (Tier 0–3) ───────────────────────────
        elif display_type == "lcd_16x2_sim":
            from src.renderers.lcd_simulator_renderer import LCDSimulatorRenderer
            return LCDSimulatorRenderer(rows=2, cols=16)
        elif display_type == "lcd_20x4_sim":
            from src.renderers.lcd_simulator_renderer import LCDSimulatorRenderer
            return LCDSimulatorRenderer(rows=4, cols=20)
        elif display_type == "lcd_16x8_sim":
            from src.renderers.lcd_simulator_renderer import LCDSimulatorRenderer
            return LCDSimulatorRenderer(rows=8, cols=16)
        elif display_type == "lcd_25x16_sim":
            from src.renderers.lcd_simulator_renderer import LCDSimulatorRenderer
            return LCDSimulatorRenderer(rows=16, cols=25)

        # ── Pixel displays (stub — implemented in Week 9/10) ────────
        elif display_type == "oled_128x64":
            raise NotImplementedError("oled_128x64 renderer not yet implemented (Week 9)")
        elif display_type == "epaper_200x200":
            raise NotImplementedError("epaper_200x200 renderer not yet implemented (Week 10)")
            
        raise ValueError(f"Unknown display type: {display_type}")
