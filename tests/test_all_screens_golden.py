import os
import sys
import json
import pytest

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.json_parser import JSONParser
from src.screen_state import ScreenState
from src.renderers.text_renderer import TextRenderer

TIERS = {
    "16x2": (2, 16, 1),
    "20x4": (4, 20, 3),
    "16x8": (8, 16, 7),
    "25x16": (16, 25, 15)
}

@pytest.fixture(scope="session")
def update_golden(request):
    return request.config.getoption("--update-golden")

@pytest.fixture(scope="session")
def scenarios_data():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    scenarios_file = os.path.join(base_dir, 'scenarios/scenarios.json')
    parser = JSONParser(scenarios_file)
    
    synth_path = os.path.join(base_dir, 'scenarios/synthetic_screens.json')
    if os.path.exists(synth_path):
        with open(synth_path, 'r') as f:
            parser.scenarios.update(json.load(f))
            
    return parser

def generate_test_cases():
    # Since we can't easily parse scenarios.json at collect time without duplicating code,
    # we will dynamically generate test cases or just loop inside a single test.
    # To keep pytest output clean, we will yield parameters.
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    scenarios_file = os.path.join(base_dir, 'scenarios/scenarios.json')
    
    if not os.path.exists(scenarios_file):
        return []
        
    parser = JSONParser(scenarios_file)
    synth_path = os.path.join(base_dir, 'scenarios/synthetic_screens.json')
    if os.path.exists(synth_path):
        with open(synth_path, 'r') as f:
            parser.scenarios.update(json.load(f))
            
    cases = []
    for s_name, s_def in parser.scenarios.items():
        # default variation
        for tier_name in TIERS:
            cases.append((s_name, "(default)", tier_name))
        
        for v in s_def.get("variations", []):
            v_name = v.get("name", "variation")
            for tier_name in TIERS:
                cases.append((s_name, v_name, tier_name))
                
    return cases

@pytest.mark.parametrize("screen_name,variation_name,tier_name", generate_test_cases())
def test_screen_snapshot(scenarios_data, update_golden, screen_name, variation_name, tier_name):
    # Get context
    var_param = None if variation_name == "(default)" else variation_name
    ctx = scenarios_data.get_scenario_context(screen_name, var_param)
    
    # Configure renderer and state
    rows, cols, visible_rows = TIERS[tier_name]
    renderer = TextRenderer(rows=rows, cols=cols)
    state = ScreenState(screen_name, ctx, visible_rows=visible_rows)
    
    # Render
    output_lines = renderer.render(state)
    output_text = "\n".join(output_lines) + "\n"
    
    # Check against golden
    golden_dir = os.path.join(os.path.dirname(__file__), "golden", screen_name, variation_name.replace(" ", "_"))
    os.makedirs(golden_dir, exist_ok=True)
    
    golden_file = os.path.join(golden_dir, f"{tier_name}.txt")
    
    if update_golden:
        with open(golden_file, "w") as f:
            f.write(output_text)
    else:
        assert os.path.exists(golden_file), f"Golden file missing: {golden_file}. Run with --update-golden"
        with open(golden_file, "r") as f:
            expected = f.read()
        assert output_text == expected, f"Output mismatch for {screen_name} -> {variation_name} on {tier_name}"
