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
        display_type = self.config.get("display", {}).get("type", "simulator")
        
        if display_type == "simulator":
            from src.renderers.simulator_renderer import SimulatorRenderer
            return SimulatorRenderer(visible_rows=5, cols=20)
        elif display_type == "lcd_16x2":
            # Will be implemented in Phase 2
            # from src.renderers.text_renderer import TextRenderer
            # return TextRenderer(visible_rows=2, cols=16)
            raise NotImplementedError("lcd_16x2 renderer not yet implemented")
        elif display_type == "lcd_20x4":
            # Will be implemented in Phase 2
            raise NotImplementedError("lcd_20x4 renderer not yet implemented")
        elif display_type == "oled_128x32":
            # Will be implemented in Phase 3
            raise NotImplementedError("oled_128x32 renderer not yet implemented")
            
        raise ValueError(f"Unknown display type: {display_type}")
