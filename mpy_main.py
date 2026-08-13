"""
MicroPython Entrypoint for SeedSigner Constrained UI
Target: ESP32-S3 (or any MicroPython board)
"""
import time
import machine

# Import our pure Python core logic
from src.utils.json_parser import JSONParser
from src.screen_state import ScreenState, ScreenType

# Import our new MicroPython-specific hardware drivers
from src.drivers.lcd_i2c_mpy import LCDI2CMPY
from src.drivers.framebuf_mpy import MicroPythonFramebufRenderer

class InputEvent:
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    ENTER = "ENTER"

def main():
    print("Booting SeedSigner Constrained UI on MicroPython...")
    
    # --- 1. HARDWARE SETUP ---
    # Setup I2C Bus (ESP32-S3 typical pins: SCL=9, SDA=8)
    # Adjust pins according to your actual wiring!
    try:
        i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8), freq=400000)
        devices = i2c.scan()
        print("I2C devices found:", [hex(d) for d in devices])
    except Exception as e:
        print("I2C initialization failed:", e)
        return

    # Choose your display type here by commenting/uncommenting!
    DISPLAY_TYPE = "OLED" # or "LCD"
    
    if DISPLAY_TYPE == "OLED":
        try:
            import ssd1306
            # 128x64 OLED
            oled = ssd1306.SSD1306_I2C(128, 64, i2c)
            # Create our MicroPython Framebuf renderer
            # Char height/width is 8x8 for MicroPython's default font
            renderer = MicroPythonFramebufRenderer(oled, width=128, height=64)
            print("OLED initialized.")
        except Exception as e:
            print("OLED init failed:", e)
            return
            
    elif DISPLAY_TYPE == "LCD":
        # 20x4 LCD
        lcd_driver = LCDI2CMPY(i2c=i2c, i2c_addr=0x27, rows=4, cols=20)
        from src.renderers.text_renderer import TextRenderer
        text_renderer = TextRenderer(rows=4, cols=20)
        # Wrap so render() outputs to the LCD hardware
        class LCDRendererWrapper:
            def __init__(self, driver, tr):
                self.driver = driver
                self.text_renderer = tr
                self.rows = tr.rows
                self.cols = tr.cols
                self.visible_rows = tr.item_rows
            def render(self, state):
                lines = self.text_renderer.render(state)
                self.driver.write_lines(lines)
        renderer = LCDRendererWrapper(lcd_driver, text_renderer)
        print("LCD initialized.")

    # Setup Buttons (GPIO Pins with Pull-Ups)
    # Adjust these to match your actual wiring!
    btn_up = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_down = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_left = machine.Pin(6, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_right = machine.Pin(7, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_enter = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)
    
    # --- 2. LOAD SCENARIO ---
    print("Loading scenarios.json...")
    parser = JSONParser("scenarios/scenarios.json")
    
    scenario_name = "main_menu_screen"
    try:
        context = parser.get_scenario_context(scenario_name)
    except Exception as e:
        print("Failed to load scenario:", e)
        return
        
    state = ScreenState(scenario_name, context, visible_rows=renderer.rows)
    
    # --- 3. EVENT LOOP ---
    print("Starting event loop...")
    if hasattr(renderer, 'render'):
        renderer.render(state)
    elif hasattr(renderer, 'write_lines'):
        # For the framebuf renderer directly
        from src.renderers.text_renderer import TextRenderer
        text_r = TextRenderer(renderer)
        text_r.render(state)

    def read_buttons():
        # Active low (0) because of pull-ups
        if btn_up.value() == 0: return InputEvent.UP
        if btn_down.value() == 0: return InputEvent.DOWN
        if btn_left.value() == 0: return InputEvent.LEFT
        if btn_right.value() == 0: return InputEvent.RIGHT
        if btn_enter.value() == 0: return InputEvent.ENTER
        return None

    # Debounce tracking
    last_pressed = None
    last_press_time = 0

    while True:
        event = read_buttons()
        needs_render = False
        
        if event:
            # Simple debounce: require button release or 300ms delay between same-key presses
            now = time.ticks_ms()
            if event != last_pressed or time.ticks_diff(now, last_press_time) > 300:
                last_pressed = event
                last_press_time = now
                
                print("Key Pressed:", event)
                
                # Dismiss toast on any keypress
                if state.screen_type == ScreenType.TOAST_OVERLAY:
                    bg_ctx = state.context.get("background", {})
                    state.context.update(bg_ctx)
                    state.screen_type = ScreenType.MAIN_MENU
                    needs_render = True
                else:
                    if event == InputEvent.UP:
                        needs_render = state.move_up()
                    elif event == InputEvent.DOWN:
                        needs_render = state.move_down()
                    elif event == InputEvent.LEFT:
                        needs_render = state.move_left()
                    elif event == InputEvent.RIGHT:
                        needs_render = state.move_right()
                    elif event == InputEvent.ENTER:
                        if ScreenType.is_keyboard(state.screen_type):
                            action = state.on_enter()
                            if action == "UPDATE":
                                needs_render = True
                            elif action == "SUBMIT":
                                print(f"Submitted Text: {state.entered_text}")
                        elif state.items and state.selected_index < len(state.items):
                            selected = state.items[state.selected_index]
                            print(f"Selected: {selected.get('label')}")
        else:
            last_pressed = None
            
        # Tick the animation state every 100ms
        if state.tick():
            needs_render = True
            
        if needs_render:
            # We must use TextRenderer to format the lines, then output them to the driver
            if hasattr(renderer, 'render'):
                renderer.render(state)
            else:
                lines = text_r._render_screen(state)
                renderer.write_lines(lines)
                
        time.sleep(0.05) # 50ms poll loop

if __name__ == "__main__":
    main()
