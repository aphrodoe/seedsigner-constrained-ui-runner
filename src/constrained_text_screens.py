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
                from gpiozero import Button
                # Standard SeedSigner / Waveshare HAT GPIO pins
                self.buttons = {
                    "UP": Button(6, pull_up=True),
                    "DOWN": Button(19, pull_up=True),
                    "LEFT": Button(5, pull_up=True),
                    "RIGHT": Button(26, pull_up=True),
                    "ENTER": Button(13, pull_up=True),
                    "KEY1": Button(21, pull_up=True),
                    "KEY2": Button(20, pull_up=True),
                    "KEY3": Button(16, pull_up=True)
                }
            except Exception as e:
                print(f"WARNING: gpiozero failed to init: {e}. Running without physical buttons.")
                self.buttons = None

    def read(self):
        event = None
        if IS_MICROPYTHON:
            if self.btn_up.value() == 0: event = "UP"
            elif self.btn_down.value() == 0: event = "DOWN"
            elif self.btn_left.value() == 0: event = "LEFT"
            elif self.btn_right.value() == 0: event = "RIGHT"
            elif self.btn_enter.value() == 0: event = "ENTER"
        elif self.buttons:
            for key, btn in self.buttons.items():
                if btn.is_pressed:
                    event = key
                    break
        
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

    # Monkey-patch lvgl_screen_runner to intercept optical flows
    try:
        import seedsigner.gui.lvgl_screen_runner as runner
        runner.run_camera_scan = _intercept_run_camera_scan
        runner.run_camera_entropy = _intercept_run_camera_entropy
        runner.run_qr_display_screen = _intercept_run_qr_display_screen
        
        # Prevent upstream Renderer from trying to claim SPI0 for ST7789
        from seedsigner.hardware.displays.display_driver import DisplayDriverFactory
        class DummyDisplay:
            width = 240
            height = 240
            def show_image(self, *args, **kwargs): pass
            def clear(self, *args, **kwargs): pass
            def show(self, *args, **kwargs): pass
        DisplayDriverFactory.instantiate_display_driver = lambda *args, **kwargs: DummyDisplay()
        
        # Patch UrPsbtQrEncoder to avoid cUR dependency crash on Pi
        import seedsigner.models.encode_qr
        class DummyEncoder:
            def __init__(self, psbt, **kwargs):
                self.psbt = psbt
        seedsigner.models.encode_qr.UrPsbtQrEncoder = DummyEncoder
        
        print("constrained_text_screens: monkey-patched lvgl_screen_runner and upstream display.")
    except ImportError:
        pass

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

# --- Optical Flow Interception ---
def _intercept_run_camera_entropy(*, seed_hash=None):
    global _current_state
    from src.screen_state import ScreenState, ScreenType
    # Fallback to Dice for constrained displays
    cfg = {
        "title": "Camera Offline",
        "text": "Image Entropy is not supported on this hardware. Please use Dice Rolls.",
        "status_type": "warning",
        "button_data": [{"text": "OK"}]
    }
    state = ScreenState(ScreenType.LARGE_ICON_STATUS, cfg)
    _current_state = state
    _renderer.render(state)
    
    # Flush pending inputs to avoid auto-dismissal
    clear_result_queue()
    if hasattr(HardwareInput, '_keyboard_hook'):
        while HardwareInput._keyboard_hook.read_event(timeout=0): pass
        
    time.sleep(0.5) # Network debounce for SSH keyboard emulator
    
    # Wait for user input to clear the warning
    while True:
        event = poll_for_result()
        if event is not None:
            if event[0] == "button_selected":
                break
        time.sleep(0.05)
        
    return None # Upstream treats None as Cancelled and returns gracefully

def _intercept_run_camera_scan(decoder, *, instructions_text=None):
    global _current_state
    try:
        from src.hardware.microsd import MicroSDManager
    except ImportError:
        class MicroSDManager:
            @classmethod
            def list_files(cls): return []
    
    from seedsigner.hardware.scan_consumer import ScanResult
    
    files = MicroSDManager.list_files()
    if not files:
        cfg = {
            "title": "No SD Card",
            "text": "Please insert an SD card with .psbt or .json files.",
            "status_type": "error",
            "button_data": [{"text": "OK"}]
        }
        state = ScreenState(ScreenType.LARGE_ICON_STATUS, cfg)
        _current_state = state
        _renderer.render(state)
        
        # Flush pending inputs
        clear_result_queue()
        if hasattr(HardwareInput, '_keyboard_hook'):
            while HardwareInput._keyboard_hook.read_event(timeout=0): pass
            
        time.sleep(0.5) # Network debounce
        while True:
            event = poll_for_result()
            if event is not None and event[0] == "button_selected":
                break
            time.sleep(0.05)
        return ScanResult(decoder, False, True, "cancelled", 0, 0)
        
    # Build list for user
    button_data = [{"text": f} for f in files]
    cfg = {
        "title": "Load from SD Card",
        "button_data": button_data
    }
    
    state = ScreenState(ScreenType.BUTTON_LIST, cfg)
    _current_state = state
    _renderer.render(state)
    
    time.sleep(0.5) # Network debounce
    
    selected_index = None
    while True:
        event = poll_for_result()
        if event is not None:
            if event[0] == "button_selected":
                if event[1] == RET_CODE__BACK_BUTTON:
                    return ScanResult(decoder, False, True, "cancelled", 0, 0)
                selected_index = event[1]
                break
        time.sleep(0.05)
        
    filename = files[selected_index]
    file_bytes = MicroSDManager.read_file(filename)
    # If the file is a raw binary PSBT, convert it to base64 so the QR decoder can parse it
    if file_bytes.startswith(b"psbt\xff"):
        import base64
        file_text = base64.b64encode(file_bytes).decode('utf-8')
    else:
        file_text = file_bytes.decode('utf-8').strip()
        
    # Feed it into the decoder as if it was scanned from a camera frame
    decoder.add_data(file_text)
    
    return ScanResult(decoder, True, False, "complete", 1, 0)

def _intercept_run_qr_display_screen(encoder, *, allow_screensaver=False):
    global _current_state
    try:
        from src.hardware.microsd import MicroSDManager
    except ImportError:
        class MicroSDManager:
            @classmethod
            def write_file(cls, name, data): pass
            
    status_text = "Data written to SD Card."
    
    if hasattr(encoder, "psbt"):
        psbt_bytes = encoder.psbt.serialize()
        MicroSDManager.write_file("signed_tx.psbt", psbt_bytes)
        status_text = "Signed PSBT saved to SD Card!"
    elif hasattr(encoder, "xpub_data") or hasattr(encoder, "derivation"):
        from seedsigner.models.encode_qr import build_xpub_data
        xd = build_xpub_data(getattr(encoder, "seed", None), 
                             getattr(encoder, "derivation", ""), 
                             getattr(encoder, "network", "main"), 
                             getattr(encoder, "sig_type", ""))
        MicroSDManager.write_file("xpub.txt", xd.xpubstring.encode())
        status_text = "XPUB saved to SD Card!"
        
    cfg = {
        "title": "Success",
        "text": status_text,
        "status_type": "success",
        "button_data": [{"text": "OK"}]
    }
    state = ScreenState(ScreenType.LARGE_ICON_STATUS, cfg)
    _current_state = state
    _renderer.render(state)
    
    # Flush pending inputs
    clear_result_queue()
    if hasattr(HardwareInput, '_keyboard_hook'):
        while HardwareInput._keyboard_hook.read_event(timeout=0): pass
        
    time.sleep(0.5) # Network debounce
    while True:
        event = poll_for_result()
        if event is not None and event[0] == "button_selected":
            break
        time.sleep(0.05)

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
        if event == "KEY1" or event == "KEY2" or event == "ESC":
            # Map physical hardware buttons to standard topnav actions
            if _current_state.screen_type == "main_menu_screen" or _current_state.context.get("show_back_button", True) == False:
                # Main menu has no back button, ignore
                needs_render = True
            else:
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
