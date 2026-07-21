import sys
import argparse
from src.display_manager import DisplayManager
from src.utils.json_parser import JSONParser
from src.screen_state import ScreenState
from src.input.keyboard_input import KeyboardInput, InputEvent
from src.renderers.audio_renderer import AudioRenderer

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
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    state = ScreenState(args.scenario, context, visible_rows=renderer.visible_rows)
    audio = AudioRenderer(pin=18)
    
    # Event Loop
    with KeyboardInput() as keyboard:
        # Initial render
        renderer.render(state)
        audio.render_state(state)
        
        while True:
            event = keyboard.read_event(timeout=0.3)
            
            needs_render = False
            
            if event is None:
                # Timeout occurred, tick animation state
                needs_render = state.tick()
            elif event == InputEvent.QUIT:
                renderer.clear()
                break
            elif event == InputEvent.UP:
                audio.play_move()
                needs_render = state.move_up()
            elif event == InputEvent.DOWN:
                audio.play_move()
                needs_render = state.move_down()
            elif event == InputEvent.LEFT:
                audio.play_move()
                needs_render = state.move_left()
            elif event == InputEvent.RIGHT:
                audio.play_move()
                needs_render = state.move_right()
            elif event == InputEvent.ENTER:
                audio.play_select()
                if state.screen_type.is_keyboard():
                    action = state.on_enter()
                    if action == "UPDATE":
                        needs_render = True
                    elif action == "SUBMIT":
                        renderer.clear()
                        print(f"Submitted Text: {state.entered_text}")
                        break
                elif state.items and state.selected_index < len(state.items):
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
                renderer.render(state)

if __name__ == "__main__":
    main()
