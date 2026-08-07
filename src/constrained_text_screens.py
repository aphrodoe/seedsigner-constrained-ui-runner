"""
Bridging module that satisfies the seedsigner_lvgl_screens API contract
as defined in view-to-screen-json-contract.md.

This allows the unmodified SeedSigner Views to run our text renderer.
"""
import time
import sys

from src.screen_state import ScreenState, ScreenType
from src.renderers.text_renderer import TextRenderer
from src.display_manager import DisplayManager

try:
    import machine
    IS_MICROPYTHON = True
except ImportError:
    IS_MICROPYTHON = False

# Global state
_current_state = None
_renderer = None
_hardware_input = None
_result_queue = []
_initialized = False

# Sentinel values for BACK and POWER from the contract
RET_CODE__BACK_BUTTON = 1000
RET_CODE__POWER_BUTTON = 1001

class HardwareInput:
    def __init__(self):
        self.last_pressed = None
        self.last_press_time = 0
        
        if IS_MICROPYTHON:
            self.btn_up = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
            self.btn_down = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)
            self.btn_left = machine.Pin(6, machine.Pin.IN, machine.Pin.PULL_UP)
            self.btn_right = machine.Pin(7, machine.Pin.IN, machine.Pin.PULL_UP)
            self.btn_enter = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)
            self.GPIO = None
        else:
            try:
                import RPi.GPIO as GPIO
                current_mode = GPIO.getmode()
                if current_mode is None:
                    GPIO.setmode(GPIO.BCM)
                elif current_mode != GPIO.BCM:
                    print(f"WARNING: GPIO mode is {current_mode}, expected {GPIO.BCM}")
                GPIO.setwarnings(False)
                
                # Standard SeedSigner / Waveshare HAT GPIO pins
                self.pins = {
                    "UP": 6,
                    "DOWN": 19,
                    "LEFT": 5,
                    "RIGHT": 26,
                    "ENTER": 13,
                    "KEY1": 21,  # Often used as back/power/shortcut
                    "KEY2": 20,
                    "KEY3": 16
                }
                for pin in self.pins.values():
                    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                
                self.GPIO = GPIO
            except Exception as e:
                print(f"WARNING: RPi.GPIO failed to init: {e}. Running without physical buttons.")
                self.GPIO = None

    def read(self):
        event = None
        if IS_MICROPYTHON:
            if self.btn_up.value() == 0: event = "UP"
            elif self.btn_down.value() == 0: event = "DOWN"
            elif self.btn_left.value() == 0: event = "LEFT"
            elif self.btn_right.value() == 0: event = "RIGHT"
            elif self.btn_enter.value() == 0: event = "ENTER"
        elif self.GPIO:
            if self.GPIO.input(self.pins["UP"]) == self.GPIO.LOW: event = "UP"
            elif self.GPIO.input(self.pins["DOWN"]) == self.GPIO.LOW: event = "DOWN"
            elif self.GPIO.input(self.pins["LEFT"]) == self.GPIO.LOW: event = "LEFT"
            elif self.GPIO.input(self.pins["RIGHT"]) == self.GPIO.LOW: event = "RIGHT"
            elif self.GPIO.input(self.pins["ENTER"]) == self.GPIO.LOW: event = "ENTER"
            elif self.GPIO.input(self.pins["KEY1"]) == self.GPIO.LOW: event = "KEY1"
            elif self.GPIO.input(self.pins["KEY2"]) == self.GPIO.LOW: event = "KEY2"
            elif self.GPIO.input(self.pins["KEY3"]) == self.GPIO.LOW: event = "KEY3"
        
        # Debounce
        now = time.time() if not IS_MICROPYTHON else time.ticks_ms()
        diff = (now - self.last_press_time) * 1000 if not IS_MICROPYTHON else time.ticks_diff(now, self.last_press_time)
        
        if event:
            if event != self.last_pressed or diff > 300:
                self.last_pressed = event
                self.last_press_time = now
                return event
        else:
            self.last_pressed = None
            
        return None

def init():
    global _renderer, _hardware_input, _initialized
    
    if _initialized:
        return
        
    print("constrained_text_screens: init() called by SeedSigner View layer.")
    
    if IS_MICROPYTHON:
        try:
            i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8), freq=400000)
            import ssd1306
            from src.drivers.framebuf_mpy import MicroPythonFramebufRenderer
            oled = ssd1306.SSD1306_I2C(128, 64, i2c)
            _renderer = MicroPythonFramebufRenderer(oled)
            print("constrained_text_screens: OLED framebuf initialized.")
        except Exception as e:
            print("constrained_text_screens: Failed to init OLED on MPY", e)
    else:
        manager = DisplayManager("config.json")
        _renderer = manager.create_renderer()
        print(f"constrained_text_screens: CPython display initialized ({manager.config.get('display', {}).get('type')})")
        
    _hardware_input = HardwareInput()
    _initialized = True

# --- LVGL Stubs for unmodified upstream SeedSigner ---
def native_display_init(width=0, height=0):
    # Upstream Pi Zero initialization calls this instead of init()
    init()

def lvgl_init(hor_res=0, ver_res=0):
    pass

def set_camera_rotation(degrees):
    pass

def set_screensaver_timeout(ms):
    pass

def get_inactive_time_ms():
    global _hardware_input
    if getattr(_hardware_input, 'last_press_time', 0):
        now = time.time() if not IS_MICROPYTHON else time.ticks_ms()
        diff = (now - _hardware_input.last_press_time) * 1000 if not IS_MICROPYTHON else time.ticks_diff(now, _hardware_input.last_press_time)
        return int(diff)
    return 0

def clear_result_queue():
    global _result_queue
    _result_queue.clear()

def poll_for_result():
    global _current_state, _renderer, _hardware_input, _result_queue
    
    if _result_queue:
        return _result_queue.pop(0)
        
    if not _current_state or not _hardware_input or not _renderer:
        return None
        
    # Read from Pi GPIO buttons (if wired)
    event = _hardware_input.read()
    
    # Also read from SSH Terminal Keyboard for easy testing!
    if not event and not IS_MICROPYTHON:
        from src.input.keyboard_input import KeyboardInput
        if not hasattr(HardwareInput, '_keyboard_hook'):
            HardwareInput._keyboard_hook = KeyboardInput()
            HardwareInput._keyboard_hook.__enter__()
        
        kbd_event = HardwareInput._keyboard_hook.read_event(timeout=0.01)
        if kbd_event:
            # Map KeyboardInput string constants directly
            if kbd_event == "BACK":
                event = "KEY1"
            else:
                event = kbd_event

    needs_render = False
    result_tuple = None
    
    if event:
        # SeedSigner OS contract expects certain return tuples
        if event == "KEY1" or event == "KEY2":
            # Map physical hardware buttons to standard topnav actions
            # LVGL native API expects ("button_selected", 1000, "topnav_back")
            return ("button_selected", 1000, "topnav_back")
            
        if ScreenType.is_keyboard(_current_state.screen_type):
            if event == "UP":
                needs_render = _current_state.move_up()
            elif event == "DOWN":
                needs_render = _current_state.move_down()
            elif event == "LEFT":
                needs_render = _current_state.move_left()
            elif event == "RIGHT":
                needs_render = _current_state.move_right()
            elif event == "ENTER":
                action = _current_state.on_enter()
                if action == "UPDATE":
                    needs_render = True
                elif action == "SUBMIT":
                    result_tuple = ("text_entered", -1, _current_state.entered_text)
        elif getattr(_current_state, "items", None):
            # Button list selection
            if event == "UP":
                needs_render = _current_state.move_up()
            elif event == "DOWN":
                needs_render = _current_state.move_down()
            elif event == "ENTER":
                if _current_state.selected_index < len(_current_state.items):
                    selected = _current_state.items[_current_state.selected_index]
                    label = selected.get("label", "")
                    
                    # Intercept dynamic back button if mapped directly to an item
                    if "back" in label.lower() or "cancel" in label.lower():
                        result_tuple = ("button_selected", 1000, "topnav_back")
                    else:
                        result_tuple = ("button_selected", _current_state.selected_index, label)
        else:
            # Static screen without items (like Splash Screen or Status Screen)
            # ANY button press dismisses it.
            result_tuple = ("button_selected", 0, "OK")
            
    # Auto-timeout for Splash Screen (SeedSigner expects the view driver to self-dismiss)
    if _current_state.screen_type == "opening_splash_screen" and result_tuple is None:
        now = time.time() if not IS_MICROPYTHON else time.ticks_ms()
        diff = (now - _current_state.start_time) if not IS_MICROPYTHON else (time.ticks_diff(now, _current_state.start_time) / 1000.0)
        if diff > 2.5:
            result_tuple = ("button_selected", 0, "OK")

    # Animation ticking
    if _current_state.tick():
        needs_render = True
        
    if needs_render:
        if hasattr(_renderer, 'render'):
            _renderer.render(_current_state)
        else:
            # Re-wrap pure hardware driver in TextRenderer logic
            from src.renderers.text_renderer import TextRenderer
            tr = TextRenderer(rows=getattr(_renderer, 'rows', 4), cols=getattr(_renderer, 'cols', 20))
            _renderer.write_lines(tr._render_screen(_current_state))
            
    # Polling should not block heavily, but a small sleep prevents thrashing
    if not IS_MICROPYTHON:
        time.sleep(0.01)
        
    return result_tuple

# Generate dynamic builder functions for all ScreenTypes.
# e.g., button_list_screen(cfg), large_icon_status_screen(cfg)
def _make_screen_builder(screen_name):
    def builder(cfg=None):
        global _current_state, _renderer
        cfg = cfg or {}
        
        # Determine how many item rows can fit on screen.
        # Total rows minus 1 for the top navigation bar.
        item_rows = 2
        if hasattr(_renderer, "rows"):
            item_rows = _renderer.rows - 1
        elif hasattr(_renderer, "visible_rows"):
            item_rows = _renderer.visible_rows
            
        _current_state = ScreenState(screen_name, cfg, visible_rows=item_rows)
        _current_state.start_time = time.time() if not IS_MICROPYTHON else time.ticks_ms()

        
        # Immediate render upon building (pure builder contract expects side-effect of drawing)
        if hasattr(_renderer, 'render'):
            _renderer.render(_current_state)
        else:
            from src.renderers.text_renderer import TextRenderer
            tr = TextRenderer(_renderer)
            _renderer.write_lines(tr._render_screen(_current_state))
            
    return builder

# Automatically expose all screen types from ScreenType as module-level functions
current_module = sys.modules[__name__]
for attr in dir(ScreenType):
    if not attr.startswith("_") and isinstance(getattr(ScreenType, attr), str):
        screen_name = getattr(ScreenType, attr)
        setattr(current_module, screen_name, _make_screen_builder(screen_name))

# Add a generic fallback for any unknown screen requested by SeedSigner View layer
def __getattr__(name):
    if name.endswith("_screen"):
        return _make_screen_builder(name)
    raise AttributeError(f"module {__name__} has no attribute {name}")
