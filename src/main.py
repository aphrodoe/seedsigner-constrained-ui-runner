import sys
import argparse
from src.display_manager import DisplayManager
from src.utils.json_parser import JSONParser
from src.screen_state import ScreenState
from src.input.keyboard_input import KeyboardInput, InputEvent

def main():
    parser = argparse.ArgumentParser(description="SeedSigner Constrained UI Runner")
    parser.add_argument("--display", help="Override display type from config", default=None)
    parser.add_argument("--scenario", help="Screen scenario name", default="button_list_screen")
    parser.add_argument("--variation", help="Scenario variation name", default=None)
    
    args = parser.parse_args()
    
    # Initialize Display
    display_manager = DisplayManager("config.json")
    if args.display:
        if "display" not in display_manager.config:
            display_manager.config["display"] = {}
        display_manager.config["display"]["type"] = args.display
        
    renderer = display_manager.create_renderer()
    
    # Load Scenario
    json_parser = JSONParser("scenarios/scenarios.json")
    
    try:
        context = json_parser.get_scenario_context(args.scenario, args.variation)
        if not context:
            # e.g. main_menu_screen is {} in scenarios.json
            raise ValueError("Empty context")
    except ValueError:
        # Fallback to synthetic screens if not found in scenarios.json
        try:
            json_parser = JSONParser("scenarios/synthetic_screens.json")
            context = json_parser.get_scenario_context(args.scenario, args.variation)
        except (ValueError, FileNotFoundError):
            print(f"Error: Scenario '{args.scenario}' not found in either scenarios.json or synthetic_screens.json")
            sys.exit(1)

    state = ScreenState(args.scenario, context, visible_rows=renderer.visible_rows)
    
    # Event Loop
    with KeyboardInput() as keyboard:
        while True:
            renderer.render(state)
            
            event = keyboard.read_event()
            
            needs_render = False
            
            if event == InputEvent.QUIT:
                renderer.clear()
                break
            elif event == InputEvent.UP:
                needs_render = state.move_up()
            elif event == InputEvent.DOWN:
                needs_render = state.move_down()
            elif event == InputEvent.LEFT:
                needs_render = state.page_up()
            elif event == InputEvent.RIGHT:
                needs_render = state.page_down()
            elif event == InputEvent.ENTER:
                if state.items and state.selected_index < len(state.items):
                    selected = state.items[state.selected_index]
                    label = selected.get("label", "Unknown")
                    value = selected.get("value", "Unknown")
                    renderer.clear()
                    print(f"Selected: {label} (Value: {value})")
                    break
                elif not state.items:
                    # e.g. status screen
                    renderer.clear()
                    print("Action executed")
                    break
            elif event == InputEvent.BACK:
                renderer.clear()
                print("Back pressed")
                break
                
            if needs_render:
                pass # The loop will re-render

if __name__ == "__main__":
    main()
