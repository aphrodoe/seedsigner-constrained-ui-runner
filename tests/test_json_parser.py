import pytest
import os
import json
import tempfile
from src.utils.json_parser import JSONParser

@pytest.fixture
def temp_scenarios_file():
    data = {
        "button_list_screen": {
            "context": {
                "top_nav": {"title": "Settings"},
                "button_list": ["Language", "Network"]
            },
            "variations": [
                {
                    "name": "with_tuples",
                    "context": {
                        "button_list": [["Dog", "dog_val"], ["Cat", "cat_val"]]
                    }
                },
                {
                    "name": "with_dicts",
                    "context": {
                        "button_list": [{"label": "Scan", "icon": "scan_icon"}]
                    }
                },
                {
                    "name": "override_title",
                    "context": {
                        "top_nav": {"title": "Overridden Settings"}
                    }
                }
            ]
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(data, f)
        filepath = f.name
        
    yield filepath
    
    os.unlink(filepath)

def test_load_scenarios(temp_scenarios_file):
    parser = JSONParser(temp_scenarios_file)
    assert "button_list_screen" in parser.scenarios

def test_normalize_string_list(temp_scenarios_file):
    parser = JSONParser(temp_scenarios_file)
    context = parser.get_scenario_context("button_list_screen")
    
    expected = [
        {"label": "Language", "value": "Language"},
        {"label": "Network", "value": "Network"}
    ]
    assert context["button_list"] == expected
    assert context["top_nav"]["title"] == "Settings"

def test_normalize_tuple_list(temp_scenarios_file):
    parser = JSONParser(temp_scenarios_file)
    context = parser.get_scenario_context("button_list_screen", "with_tuples")
    
    expected = [
        {"label": "Dog", "value": "dog_val"},
        {"label": "Cat", "value": "cat_val"}
    ]
    assert context["button_list"] == expected

def test_normalize_dict_list(temp_scenarios_file):
    parser = JSONParser(temp_scenarios_file)
    context = parser.get_scenario_context("button_list_screen", "with_dicts")
    
    expected = [
        {"label": "Scan", "value": "Scan", "icon": "scan_icon"}
    ]
    assert context["button_list"] == expected

def test_merge_patch_override(temp_scenarios_file):
    parser = JSONParser(temp_scenarios_file)
    context = parser.get_scenario_context("button_list_screen", "override_title")
    
    assert context["top_nav"]["title"] == "Overridden Settings"
    # The button list should still be the base one, normalized
    assert len(context["button_list"]) == 2

def test_invalid_screen(temp_scenarios_file):
    parser = JSONParser(temp_scenarios_file)
    with pytest.raises(ValueError, match="Screen scenario 'nonexistent' not found."):
        parser.get_scenario_context("nonexistent")

def test_invalid_variation(temp_scenarios_file):
    parser = JSONParser(temp_scenarios_file)
    with pytest.raises(ValueError, match="Variation 'missing' not found for screen 'button_list_screen'."):
        parser.get_scenario_context("button_list_screen", "missing")
