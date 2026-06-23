import tkinter as tk
from tkinter import ttk
import json
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.json_parser import JSONParser
from src.screen_state import ScreenState, ScreenType
from src.renderers.text_renderer import TextRenderer
from src.input.keyboard_input import InputEvent

class DualRunnerApp:
    def __init__(self, root, lvgl_dir=None, scenarios_file=None):
        self.root = root
        self.root.title("SeedSigner Dual Runner")
        self.root.geometry("750x520")
        
        # Colors
        self.bg_color = "#151515"
        self.fg_color = "#E0E0E0"
        self.accent_color = "#3478C6"
        self.panel_bg = "#1E1E1E"
        self.header_bg = "#151515"
        
        self.root.configure(bg=self.bg_color)
        
        # Paths
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.lvgl_img_dir = lvgl_dir if lvgl_dir else os.path.abspath(os.path.join(self.base_dir, '../seedsigner-c-modules/tools/apps/screenshot_generator/screenshots/img'))
        self.scenarios_file = scenarios_file if scenarios_file else os.path.abspath(os.path.join(self.base_dir, '../seedsigner-c-modules/tools/scenarios/scenarios.json'))
        
        # Renderers
        self.renderer_16x2 = TextRenderer(rows=2, cols=16)
        self.renderer_20x4 = TextRenderer(rows=4, cols=20)
        
        # State
        self.parser = JSONParser(self.scenarios_file)
        self.load_scenarios()
        self.current_state = None
        self.current_screen_name = None
        self.current_variation_name = None
        
        self.setup_styles()
        self.setup_ui()
        self.populate_sidebar()
        self.start_animation_loop()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frames
        style.configure('TFrame', background=self.bg_color)
        style.configure('Panel.TFrame', background=self.panel_bg)
        style.configure('Header.TFrame', background=self.header_bg)
        
        # Labels
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color, font=('Helvetica', 11))
        style.configure('Panel.TLabel', background=self.panel_bg, foreground=self.fg_color, font=('Helvetica', 11))
        style.configure('Title.TLabel', background=self.header_bg, foreground="#FFFFFF", font=('Helvetica', 16, 'bold'))
        style.configure('Subtitle.TLabel', background=self.bg_color, foreground="#AAAAAA", font=('Helvetica', 10))
        
        # Buttons
        style.configure('TButton', background="#2A2A2A", foreground=self.fg_color, borderwidth=0, font=('Helvetica', 10, 'bold'))
        style.map('TButton', background=[('active', self.accent_color)])
        
    def load_scenarios(self):
        synth_path = os.path.join(self.base_dir, 'scenarios/synthetic_screens.json')
        if os.path.exists(synth_path):
            with open(synth_path, 'r') as f:
                self.parser.scenarios.update(json.load(f))

    def setup_ui(self):
        # 1. Header Frame
        header_frame = ttk.Frame(self.root, style='Header.TFrame')
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Fake logo (orange background)
        logo_lbl = tk.Label(header_frame, text=" SEED SIGNER ", bg="#FF8C00", fg="#FFFFFF", font=('Helvetica', 12, 'bold'))
        logo_lbl.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(header_frame, text="Constrained UI Dual Runner", style='Title.TLabel').pack(side=tk.LEFT)
        
        # 2. Main Layout (Sidebar + Viewer)
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Sidebar (Scenarios)
        self.sidebar_frame = ttk.Frame(main_pane, style='Panel.TFrame', width=200)
        main_pane.add(self.sidebar_frame, weight=1)
        
        # Listbox styling
        self.listbox = tk.Listbox(
            self.sidebar_frame, 
            bg=self.panel_bg, fg=self.fg_color, 
            selectbackground=self.accent_color, selectforeground="#ffffff",
            font=('Helvetica', 10), borderwidth=0, highlightthickness=0,
            activestyle='none'
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.listbox.bind('<<ListboxSelect>>', self.on_select_scenario)
        
        # Content Pane
        content_frame = ttk.Frame(main_pane, style='TFrame')
        main_pane.add(content_frame, weight=3)
        
        # Top half of content pane: Viewers
        viewers_frame = ttk.Frame(content_frame, style='TFrame')
        viewers_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # LVGL Canvas
        lvgl_container = ttk.Frame(viewers_frame, style='Panel.TFrame')
        lvgl_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 2))
        ttk.Label(lvgl_container, text="Upstream LVGL", style='Panel.TLabel', font=('Helvetica', 11, 'bold')).pack(pady=(15, 10))
        
        # Center the canvas
        canvas_wrapper = ttk.Frame(lvgl_container, style='Panel.TFrame')
        canvas_wrapper.pack(expand=True)
        self.lvgl_canvas = tk.Canvas(canvas_wrapper, width=240, height=240, bg='#000000', highlightthickness=0)
        self.lvgl_canvas.pack(pady=(0, 20))
        self.lvgl_img_label = self.lvgl_canvas.create_text(120, 120, text="No Image", fill="#555555", font=('Helvetica', 10))
        
        # Text Simulators
        text_container = ttk.Frame(viewers_frame, style='Panel.TFrame')
        text_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0))
        ttk.Label(text_container, text="Constrained UI", style='Panel.TLabel', font=('Helvetica', 11, 'bold')).pack(pady=(15, 10))
        
        # Center the LCDs
        lcd_wrapper = ttk.Frame(text_container, style='Panel.TFrame')
        lcd_wrapper.pack(expand=True)
        
        ttk.Label(lcd_wrapper, text="16x2 LCD", style='Panel.TLabel').pack(pady=(0, 2))
        self.lcd_16x2_label = tk.Label(lcd_wrapper, text="", font=('Courier', 14, 'bold'), bg='#0000aa', fg='#ffffff', width=16, height=2, justify=tk.LEFT, anchor='nw')
        self.lcd_16x2_label.pack()
        
        ttk.Label(lcd_wrapper, text="20x4 LCD", style='Panel.TLabel').pack(pady=(20, 2))
        self.lcd_20x4_label = tk.Label(lcd_wrapper, text="", font=('Courier', 14, 'bold'), bg='#0000aa', fg='#ffffff', width=20, height=4, justify=tk.LEFT, anchor='nw')
        self.lcd_20x4_label.pack(pady=(0, 20))
        
        # Bottom half of content pane: Controls
        controls_container = ttk.Frame(content_frame, style='Panel.TFrame')
        controls_container.pack(fill=tk.X, pady=(5, 0), padx=(5, 0))
        
        controls_frame = ttk.Frame(controls_container, style='Panel.TFrame')
        controls_frame.pack(pady=10)
        
        ttk.Button(controls_frame, text="Up (W)", command=lambda: self.handle_input(InputEvent.UP)).grid(row=0, column=1, padx=1, pady=1)
        ttk.Button(controls_frame, text="Left (A)", command=lambda: self.handle_input(InputEvent.LEFT)).grid(row=1, column=0, padx=1, pady=1)
        ttk.Button(controls_frame, text="Enter (Space)", command=lambda: self.handle_input(InputEvent.ENTER)).grid(row=1, column=1, padx=1, pady=1)
        ttk.Button(controls_frame, text="Right (D)", command=lambda: self.handle_input(InputEvent.RIGHT)).grid(row=1, column=2, padx=1, pady=1)
        ttk.Button(controls_frame, text="Down (S)", command=lambda: self.handle_input(InputEvent.DOWN)).grid(row=2, column=1, padx=1, pady=1)
        
        # Keyboard bindings
        self.root.bind('<Up>', lambda e: self.handle_input(InputEvent.UP))
        self.root.bind('<w>', lambda e: self.handle_input(InputEvent.UP))
        self.root.bind('<Down>', lambda e: self.handle_input(InputEvent.DOWN))
        self.root.bind('<s>', lambda e: self.handle_input(InputEvent.DOWN))
        self.root.bind('<Left>', lambda e: self.handle_input(InputEvent.LEFT))
        self.root.bind('<a>', lambda e: self.handle_input(InputEvent.LEFT))
        self.root.bind('<Right>', lambda e: self.handle_input(InputEvent.RIGHT))
        self.root.bind('<d>', lambda e: self.handle_input(InputEvent.RIGHT))
        self.root.bind('<Return>', lambda e: self.handle_input(InputEvent.ENTER))
        self.root.bind('<space>', lambda e: self.handle_input(InputEvent.ENTER))

    def populate_sidebar(self):
        self.scenario_map = []
        for s_name, s_def in self.parser.scenarios.items():
            # Add a visual header for the screen type
            display_header = s_name.replace("_screen", "").replace("_", " ").title() + " Screen"
            self.listbox.insert(tk.END, display_header)
            self.listbox.itemconfig(tk.END, fg="#3478C6", bg="#151515") # Highlight header
            self.scenario_map.append(None) # Header isn't clickable
            
            variations = s_def.get("variations", [{"name": "default"}])
            for v in variations:
                v_name = v.get("name", "default")
                self.listbox.insert(tk.END, f"    {v_name}")
                self.scenario_map.append((s_name, v_name))
                
    def start_animation_loop(self):
        if self.current_state:
            needs_render = self.current_state.tick()
            if needs_render:
                self.update_displays()
        self.root.after(300, self.start_animation_loop)

    def on_select_scenario(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        mapped = self.scenario_map[index]
        if mapped is None:
            return # Clicked a header
            
        s_name, v_name = mapped
        self.current_screen_name = s_name
        self.current_variation_name = v_name if v_name != "default" else None
        
        try:
            ctx = self.parser.get_scenario_context(self.current_screen_name, self.current_variation_name)
            self.current_state = ScreenState(self.current_screen_name, ctx)
            self.update_displays()
            self.load_lvgl_image(s_name, v_name)
        except Exception as e:
            self.lcd_16x2_label.config(text=f"Error:\n{e}")
            self.lcd_20x4_label.config(text=f"Error:\n{e}")

    def update_displays(self):
        if not self.current_state:
            return
        
        lines_16x2 = self.renderer_16x2.render(self.current_state)
        self.lcd_16x2_label.config(text="\n".join(lines_16x2))
        
        lines_20x4 = self.renderer_20x4.render(self.current_state)
        self.lcd_20x4_label.config(text="\n".join(lines_20x4))
        
    def load_lvgl_image(self, s_name, v_name):
        self.lvgl_canvas.delete("all")
        
        # Build path based on screenshot_gen output rules:
        # img/240x240/button_list_screen__scroll_many_240x240.png
        # img/240x240/button_list_screen_240x240.png
        if v_name == "default":
            img_filename = f"{s_name}_240x240.png"
            gif_filename = f"{s_name}_240x240.gif"
        else:
            img_filename = f"{s_name}__{v_name}_240x240.png"
            gif_filename = f"{s_name}__{v_name}_240x240.gif"
            
        img_path = os.path.join(self.lvgl_img_dir, "240x240", img_filename)
        gif_path = os.path.join(self.lvgl_img_dir, "240x240", gif_filename)
        
        # Try GIF first if animated
        target_path = gif_path if os.path.exists(gif_path) else img_path
        
        if os.path.exists(target_path):
            try:
                # Store reference to prevent garbage collection
                self.lvgl_img = tk.PhotoImage(file=target_path)
                self.lvgl_canvas.create_image(120, 120, image=self.lvgl_img)
            except Exception as e:
                self.lvgl_canvas.create_text(120, 120, text=f"Error Loading Image:\n{e}", fill="red")
        else:
            self.lvgl_canvas.create_text(120, 120, text="LVGL Image Not Found\n(Wait for upstream CI)", fill="#555555", justify=tk.CENTER)

    def handle_input(self, key: InputEvent):
        if self.current_state:
            needs_render = False
            if key == InputEvent.UP:
                needs_render = self.current_state.move_up()
            elif key == InputEvent.DOWN:
                needs_render = self.current_state.move_down()
            elif key == InputEvent.LEFT:
                needs_render = self.current_state.move_left()
            elif key == InputEvent.RIGHT:
                needs_render = self.current_state.move_right()
            elif key == InputEvent.ENTER:
                if self.current_state.screen_type.is_keyboard() or self.current_state.screen_type.name == "SEED_MNEMONIC_ENTRY":
                    action = self.current_state.on_enter()
                    if action == "UPDATE":
                        needs_render = True
                
            if needs_render:
                self.update_displays()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Constrained UI Dual Runner")
    parser.add_argument("--lvgl-dir", help="Path to LVGL screenshots/img directory", 
                        default=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../seedsigner-c-modules/tools/apps/screenshot_generator/screenshots/img')))
    parser.add_argument("--scenarios-file", help="Path to upstream scenarios.json",
                        default=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../seedsigner-c-modules/tools/scenarios/scenarios.json')))
    
    args = parser.parse_args()
    
    root = tk.Tk()
    app = DualRunnerApp(root, lvgl_dir=args.lvgl_dir, scenarios_file=args.scenarios_file)
    root.mainloop()
