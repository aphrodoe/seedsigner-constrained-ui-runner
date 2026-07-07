import json
import os
from typing import Dict, Any, List

class JSONParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.scenarios = self._load_scenarios()

    def _load_scenarios(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Scenario file not found: {self.file_path}")
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _normalize_button_list(self, button_list: List[Any]) -> List[Dict[str, str]]:
        """
        Normalizes a button list where elements might be:
        - strings: "Language" -> {"label": "Language", "value": "Language"}
        - tuples/lists: ["Dog", "Dog"] -> {"label": "Dog", "value": "Dog"}
        - dicts: {"label": "Scan", "icon": "scan"} -> kept as is (values derived if missing)
        """
        normalized = []
        for item in button_list:
            if isinstance(item, str):
                normalized.append({"label": item, "value": item})
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                normalized.append({"label": str(item[0]), "value": item[1]})
            elif isinstance(item, dict):
                # Ensure it has a label, defaulting value to label if not present
                if "label" not in item:
                    item["label"] = ""
                if "value" not in item:
                    item["value"] = item["label"]
                normalized.append(item)
            else:
                # Fallback for unexpected formats
                normalized.append({"label": str(item), "value": str(item)})
        return normalized

    def _merge_patch(self, base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
        """Simple recursive merge patch (RFC 7396 style) for variation context overrides."""
        merged = base.copy()
        for key, value in patch.items():
            if value is None:
                if key in merged:
                    del merged[key]
            elif isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._merge_patch(merged[key], value)
            else:
                merged[key] = value
        return merged

    def get_scenario_context(self, screen_name: str, variation_name: str = None) -> Dict[str, Any]:
        """
        Retrieves the context for a screen scenario, optionally applying a variation.
        Normalizes button_list formatting automatically.
        """
        if screen_name not in self.scenarios:
            raise ValueError(f"Screen scenario '{screen_name}' not found.")

        screen_def = self.scenarios[screen_name]
        context = screen_def.get("context", {}).copy()

        if "screenshot" in screen_def and screen_def["screenshot"].get("animated"):
            context["animated"] = True

        if variation_name:
            variations = screen_def.get("variations", [])
            variation = next((v for v in variations if v.get("name") == variation_name), None)
            if not variation:
                raise ValueError(f"Variation '{variation_name}' not found for screen '{screen_name}'.")
            
            # Apply variation overrides
            var_context = variation.get("context", {})
            context = self._merge_patch(context, var_context)

            if "screenshot" in variation and variation["screenshot"].get("animated"):
                context["animated"] = True

        # Normalize button lists if present
        if "button_list" in context:
            context["button_list"] = self._normalize_button_list(context["button_list"])
            
        if "button_grid" in context:
            context["button_grid"] = self._normalize_button_list(context["button_grid"])
            
        if "button_data" in context:
            context["button_data"] = self._normalize_button_list(context["button_data"])
            
        return context
