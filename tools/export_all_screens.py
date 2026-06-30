import os
import sys
import json
import inspect
import shutil

runner_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
seedsigner_root = os.path.abspath(os.path.join(runner_dir, "..", "seedsigner"))
sys.path.append(os.path.join(seedsigner_root, "src"))
sys.path.append(seedsigner_root)
sys.path.append(os.path.join(seedsigner_root, "tests"))

sys.path.append(runner_dir)
from src.screen_state import ScreenState

from screenshot_generator.generator import generate_screenshots
from screenshot_generator.utils import ScreenshotRenderer

from seedsigner.gui.screens.screen import (
    ButtonListScreen, LargeButtonScreen, LargeIconStatusScreen, 
    KeyboardScreen, BaseTopNavScreen
)
from seedsigner.views.screensaver import OpeningSplashScreen
from seedsigner.gui.screens.seed_screens import SeedAddPassphraseScreen, SeedMnemonicEntryScreen
from seedsigner.gui.screens.psbt_screens import PSBTOverviewScreen, PSBTMathScreen
from seedsigner.gui.screens.screen import QRDisplayScreen

EXPORT_DIR = os.path.join(runner_dir, "tools", "screenshots_export")
os.makedirs(EXPORT_DIR, exist_ok=True)
IMG_DIR = os.path.join(EXPORT_DIR, "img")
os.makedirs(IMG_DIR, exist_ok=True)

all_screens_data = []

def map_screen_to_state(screen_obj) -> ScreenState:
    context = {}
    screen_name = "unknown_screen"
    
    title = getattr(screen_obj, 'title', 'Menu')
    if hasattr(screen_obj, 'top_nav') and hasattr(screen_obj.top_nav, 'title'):
        title = screen_obj.top_nav.title
        
    if type(title).__name__ == 'IconTextLine':
        lbl = getattr(title, 'label_text', '') or ''
        val = getattr(title, 'value_text', '') or ''
        title = f"{lbl} {val}".strip()
    elif hasattr(title, 'text'):
        title = title.text
    elif not isinstance(title, str):
        title = str(title)
        
    context["top_nav"] = {"title": title}
    
    if isinstance(screen_obj, LargeButtonScreen):
        screen_name = "main_menu_screen"
        items = []
        for btn in getattr(screen_obj, 'buttons', []):
            if hasattr(btn, 'text'):
                items.append({"label": btn.text})
        context["items"] = items
        state = ScreenState(screen_name, context)
        state.selected_index = getattr(screen_obj, 'selected_button', 0)
        return state
        
    elif isinstance(screen_obj, LargeIconStatusScreen):
        screen_name = "large_icon_status_screen"
        context["title"] = title
        context["status_icon_name"] = getattr(screen_obj, 'status_icon_name', '')
        context["status_headline"] = getattr(screen_obj, 'status_headline', '')
        
        extra_text = []
        if getattr(screen_obj, 'text', ''):
            extra_text.append(getattr(screen_obj, 'text'))
            
        for comp in getattr(screen_obj, 'components', []):
            if type(comp).__name__ == 'IconTextLine':
                lbl = getattr(comp, 'label_text', '') or ''
                val = getattr(comp, 'value_text', '') or ''
                txt = f"{lbl} {val}".strip()
                if txt: extra_text.append(txt)
            elif type(comp).__name__ == 'TextArea':
                txt = getattr(comp, 'text', '') or ''
                if txt: extra_text.append(txt)
            elif type(comp).__name__ == 'FormattedAddress':
                txt = getattr(comp, 'address', '') or ''
                if txt: extra_text.append(txt)
                
        if extra_text:
            context["text"] = "\n".join(extra_text)
        
        color = getattr(screen_obj, 'status_color', '').upper()
        if color == '#FF1B0A' or color == '#FF4D4D':
            context["status_type"] = "error"
        elif color == '#FF5700':
            context["status_type"] = "error"
            context["is_dire_warning"] = True
        elif color == '#FFD60A' or color == '#FFD600' or color == 'ORANGE':
            context["status_type"] = "warning"
        else:
            context["status_type"] = "success"
            
        items = []
        for btn in getattr(screen_obj, 'button_data', []):
            if hasattr(btn, 'text'):
                items.append({"label": btn.text})
            elif hasattr(btn, 'button_label'):
                items.append({"label": btn.button_label})
        context["items"] = items
        state = ScreenState(screen_name, context)
        return state

    elif isinstance(screen_obj, PSBTOverviewScreen):
        screen_name = "button_list_screen"
        items = []
        items.append({"label": f"Spend: {screen_obj.spend_amount}"})
        items.append({"label": f"Fee: {screen_obj.fee_amount}"})
        items.append({"label": f"Change: {screen_obj.change_amount}"})
        items.append({"label": f"Inputs: {screen_obj.num_inputs}"})
        items.append({"label": f"Outputs: {len(screen_obj.destination_addresses) if screen_obj.destination_addresses else 0}"})
        
        btns = getattr(screen_obj, 'button_data', getattr(screen_obj, 'buttons', []))
        for btn in btns:
            label = getattr(btn, 'button_label', getattr(btn, 'text', 'Item'))
            items.append({"label": label, "value": label})
            
        context["items"] = items
        state = ScreenState(screen_name, context)
        state.selected_index = getattr(screen_obj, 'selected_button', 0)
        return state

    elif isinstance(screen_obj, PSBTMathScreen):
        screen_name = "button_list_screen"
        items = []
        items.append({"label": f"In: {screen_obj.input_amount}"})
        items.append({"label": f"Out: {screen_obj.spend_amount}"})
        items.append({"label": f"Fee: {screen_obj.fee_amount}"})
        items.append({"label": f"Change: {screen_obj.change_amount}"})
        
        btns = getattr(screen_obj, 'button_data', getattr(screen_obj, 'buttons', []))
        for btn in btns:
            label = getattr(btn, 'button_label', getattr(btn, 'text', 'Item'))
            items.append({"label": label, "value": label})
            
        context["items"] = items
        state = ScreenState(screen_name, context)
        state.selected_index = getattr(screen_obj, 'selected_button', 0)
        return state

    elif isinstance(screen_obj, ButtonListScreen):
        screen_name = "button_list_screen"
        items = []
        btns = getattr(screen_obj, 'button_data', getattr(screen_obj, 'buttons', []))
        for btn in btns:
            label = getattr(btn, 'button_label', getattr(btn, 'text', 'Item'))
            val = getattr(btn, 'right_text', label)
            items.append({"label": label, "value": val})
        context["items"] = items
        
        extra_text = []
        
        if hasattr(screen_obj, 'amount') and getattr(screen_obj, 'amount') is not None:
            extra_text.append(f"Amount: {getattr(screen_obj, 'amount')} sats")
            
        if hasattr(screen_obj, 'address') and getattr(screen_obj, 'address'):
            extra_text.append(getattr(screen_obj, 'address'))
        
        if hasattr(screen_obj, 'words') and getattr(screen_obj, 'words'):
            extra_text.extend(getattr(screen_obj, 'words'))
            
        for comp in getattr(screen_obj, 'components', []):
            if type(comp).__name__ == 'IconTextLine':
                lbl = getattr(comp, 'label_text', '') or ''
                val = getattr(comp, 'value_text', '') or ''
                txt = f"{lbl} {val}".strip()
                if txt: extra_text.append(txt)
            elif type(comp).__name__ == 'TextArea':
                txt = getattr(comp, 'text', '') or ''
                if txt: extra_text.append(txt)
            elif type(comp).__name__ == 'FormattedAddress':
                txt = getattr(comp, 'address', '') or ''
                if txt: extra_text.append(txt)
                
        if extra_text:
            context["text"] = "\n".join(extra_text)
        
        state = ScreenState(screen_name, context)
        state.selected_index = getattr(screen_obj, 'selected_button', 0)
        state.scroll_offset = max(0, state.selected_index - 1)
        return state
        
    elif isinstance(screen_obj, KeyboardScreen):
        screen_name = "synthetic_entry_screen"
        context["top_nav"]["title"] = title
        
        charset = None
        if hasattr(screen_obj, 'keys_to_values') and screen_obj.keys_to_values:
            charset = "".join(list(screen_obj.keys_to_values.values()))
        elif hasattr(screen_obj, 'keys_charset') and screen_obj.keys_charset:
            charset = screen_obj.keys_charset
            
        if charset:
            context["charset_modes"] = {
                "default": charset
            }
            context["initial_mode"] = "default"
            
        state = ScreenState(screen_name, context)
        return state
        
    elif isinstance(screen_obj, SeedAddPassphraseScreen):
        screen_name = "seed_add_passphrase_screen"
        context["top_nav"]["title"] = title
        context["initial_text"] = getattr(screen_obj, 'passphrase', '')
        
        initial_kb = getattr(screen_obj, 'initial_keyboard', None)
        if initial_kb == SeedAddPassphraseScreen.KEYBOARD__LOWERCASE_BUTTON_TEXT:
            context["initial_mode"] = "lower"
        elif initial_kb == SeedAddPassphraseScreen.KEYBOARD__UPPERCASE_BUTTON_TEXT:
            context["initial_mode"] = "upper"
        elif initial_kb == SeedAddPassphraseScreen.KEYBOARD__DIGITS_BUTTON_TEXT:
            context["initial_mode"] = "digits"
        elif initial_kb in (SeedAddPassphraseScreen.KEYBOARD__SYMBOLS_1_BUTTON_TEXT, SeedAddPassphraseScreen.KEYBOARD__SYMBOLS_2_BUTTON_TEXT):
            context["initial_mode"] = "symbols"
            
        state = ScreenState(screen_name, context)
        return state

    elif isinstance(screen_obj, OpeningSplashScreen):
        screen_name = "splash_screen"
        state = ScreenState(screen_name, context)
        return state

    elif isinstance(screen_obj, SeedMnemonicEntryScreen):
        screen_name = "seed_mnemonic_entry_screen"
        context["entered_text"] = "".join(getattr(screen_obj, 'letters', [])).strip()
        context["suggestions"] = getattr(screen_obj, 'possible_words', [])
        if hasattr(screen_obj, 'keyboard'):
            context["active_keys"] = getattr(screen_obj.keyboard, 'active_keys', "")
        
        state = ScreenState(screen_name, context)
        return state

    elif isinstance(screen_obj, QRDisplayScreen):
        screen_name = "button_list_screen"
        context["items"] = [{"label": "[Scan QR Code on Device]"}]
        state = ScreenState(screen_name, context)
        return state

    elif isinstance(screen_obj, BaseTopNavScreen):
        screen_name = "button_list_screen"
        extra_text = []
        for comp in getattr(screen_obj, 'components', []):
            if type(comp).__name__ == 'IconTextLine':
                lbl = getattr(comp, 'label_text', '') or ''
                val = getattr(comp, 'value_text', '') or ''
                txt = f"{lbl} {val}".strip()
                if txt: extra_text.append(txt)
            elif type(comp).__name__ == 'TextArea':
                txt = getattr(comp, 'text', '') or ''
                if txt: extra_text.append(txt)
            elif type(comp).__name__ == 'FormattedAddress':
                txt = getattr(comp, 'address', '') or ''
                if txt: extra_text.append(txt)
                
        if extra_text:
            context["text"] = "\n".join(extra_text)
            
        return ScreenState(screen_name, context)

    return ScreenState("button_list_screen", context)

original_show_image = ScreenshotRenderer.show_image

def patched_show_image(self, image=None, alpha_overlay=None, is_background_thread: bool = False):
    fname = getattr(self, "screenshot_filename", "unknown.png")
    
    try:
        original_show_image(self, image, alpha_overlay, is_background_thread)
    except Exception as e:
        if e.__class__.__name__ == "ScreenshotComplete":
            screen_obj = None
            frame = inspect.currentframe().f_back
            while frame:
                if 'self' in frame.f_locals:
                    obj = frame.f_locals['self']
                    if hasattr(obj, 'renderer') and hasattr(obj, '_render'):
                        screen_obj = obj
                        break
                frame = frame.f_back
            
            if screen_obj:
                state = map_screen_to_state(screen_obj)
                
                # Check for toast thread in generator frame
                frame_g = frame
                while frame_g:
                    if 'screenshot_config' in frame_g.f_locals:
                        config = frame_g.f_locals['screenshot_config']
                        if getattr(config, 'toast_thread', None) is not None:
                            toast_thread = config.toast_thread
                            toast_overlay = getattr(toast_thread, 'toast', None)
                            state.context["toast"] = getattr(toast_thread, 'label_text', getattr(toast_overlay, 'label_text', getattr(toast_thread, 'message', getattr(toast_thread, 'text', 'Toast Event'))))
                        break
                    frame_g = frame_g.f_back
                
                all_screens_data.append({
                    "id": fname.replace('.png', ''),
                    "image_path": f"img/{fname}",
                    "screen_type": state.screen_type.name,
                    "context": state.context,
                    "selected_index": state.selected_index,
                    "scroll_offset": state.scroll_offset
                })
                print(f"Exported data for: {fname}")
            
            # Always copy the original image to our export dir, even if screen_obj is None.
            # This is crucial for Toasts, which run in a background thread and raise
            # ScreenshotComplete without a Screen object in the frame, but they DO update
            # the underlying image on disk.
            full_path = os.path.join(self.screenshot_path, self.screenshot_filename)
            target_img = os.path.join(IMG_DIR, fname)
            shutil.copy2(full_path, target_img)
            
        raise e

ScreenshotRenderer.show_image = patched_show_image

if __name__ == "__main__":
    print("Exporting all SeedSigner screens...")
    ScreenshotRenderer.configure_instance()
    try:
        generate_screenshots("en")
    except Exception as e:
        print(f"Generator finished (some modules missing in hardware/camera.py): {e}")
        
    with open(os.path.join(EXPORT_DIR, "all_screens.json"), "w") as f:
        json.dump(all_screens_data, f, indent=4)
        
    print(f"Exported {len(all_screens_data)} screens to {EXPORT_DIR}/all_screens.json")
