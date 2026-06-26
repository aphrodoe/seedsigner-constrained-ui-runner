import os
import json
import sys

runner_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(runner_dir)
from src.renderers.text_renderer import TextRenderer
from src.screen_state import ScreenState

EXPORT_DIR = os.path.join(runner_dir, "tools", "screenshots_export")
JSON_PATH = os.path.join(EXPORT_DIR, "all_screens.json")
HTML_PATH = os.path.join(EXPORT_DIR, "index.html")

def generate_html():
    if not os.path.exists(JSON_PATH):
        print("JSON file not found. Run export_all_screens.py first.")
        return
        
    with open(JSON_PATH, "r") as f:
        screens = json.load(f)
        
    r16 = TextRenderer(2, 16)
    r20 = TextRenderer(4, 20)
    r16x8 = TextRenderer(8, 16)
    r25x16 = TextRenderer(16, 25)
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Constrained UI Screen Comparisons (All Tiers)</title>
        <style>
            body { font-family: sans-serif; background: #121212; color: #eee; margin: 0; padding: 20px; }
            h1 { text-align: center; color: #64B5F6; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(1400px, 1fr)); gap: 40px; margin-top: 40px; }
            .card { background: #1e1e1e; padding: 20px; border-radius: 8px; border: 1px solid #333; }
            .card h3 { margin-top: 0; margin-bottom: 20px; font-family: monospace; color: #90CAF9; border-bottom: 1px solid #333; padding-bottom: 10px; }
            .comparison { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
            .view { display: flex; flex-direction: column; align-items: center; gap: 10px; }
            .view-title { font-size: 0.9em; color: #aaa; font-weight: bold; }
            img { width: 240px; height: 240px; border: 1px solid #555; background: #000; }
            pre { 
                background: #0000AA; color: #FFFFFF; font-family: 'Courier New', Courier, monospace; 
                font-weight: bold; padding: 10px; margin: 0; border-radius: 4px;
                line-height: 1.2; font-size: 18px; letter-spacing: 2px;
                border: 2px solid #555;
            }
        </style>
    </head>
    <body>
        <h1>SeedSigner UI: LVGL vs 4 Adaptive Tiers</h1>
        <div class="grid">
    """
    
    for s in screens:
        # e.g., 'SPLASH' -> 'splash_screen'
        st_str = s['screen_type'].lower()
        if st_str == "splash": st_str = "splash_screen"
        if st_str == "button_list": st_str = "button_list_screen"
        if st_str == "main_menu": st_str = "main_menu_screen"
        if st_str == "large_icon_status": st_str = "large_icon_status_screen"
        if st_str == "seed_mnemonic_entry": st_str = "seed_mnemonic_entry_screen"
        if st_str == "synthetic_entry": st_str = "synthetic_entry_screen"
        if st_str == "seed_add_passphrase": st_str = "seed_add_passphrase_screen"
        
        state = ScreenState(st_str, s['context'])
        state.selected_index = s['selected_index']
        state.scroll_offset = s['scroll_offset']
        
        lines_16 = r16.render(state)
        lines_20 = r20.render(state)
        lines_16x8 = r16x8.render(state)
        lines_25x16 = r25x16.render(state)
        
        text_16 = "\n".join([line.replace('<', '&lt;').replace('>', '&gt;') for line in lines_16])
        text_20 = "\n".join([line.replace('<', '&lt;').replace('>', '&gt;') for line in lines_20])
        text_16x8 = "\n".join([line.replace('<', '&lt;').replace('>', '&gt;') for line in lines_16x8])
        text_25x16 = "\n".join([line.replace('<', '&lt;').replace('>', '&gt;') for line in lines_25x16])
        
        html += f"""
        <div class="card">
            <h3>{s['id']}</h3>
            <div class="comparison">
                <div class="view">
                    <span class="view-title">Original (240x240)</span>
                    <img src="{s['image_path']}" />
                </div>
                <div class="view">
                    <span class="view-title">Tier 0 (16x2)</span>
                    <pre>{text_16}</pre>
                </div>
                <div class="view">
                    <span class="view-title">Tier 1 (20x4)</span>
                    <pre>{text_20}</pre>
                </div>
                <div class="view">
                    <span class="view-title">Tier 2 (16x8 OLED)</span>
                    <pre style="background: #000; color: #fff;">{text_16x8}</pre>
                </div>
                <div class="view">
                    <span class="view-title">Tier 3 (25x16 E-Paper)</span>
                    <pre style="background: #ccc; color: #000;">{text_25x16}</pre>
                </div>
            </div>
        </div>
        """
        
    html += """
        </div>
    </body>
    </html>
    """
    
    with open(HTML_PATH, "w") as f:
        f.write(html)
        
    print(f"Gallery HTML generated at {HTML_PATH} with {len(screens)} screens!")

if __name__ == "__main__":
    generate_html()
