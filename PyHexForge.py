import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
from PIL import Image, ImageTk # Requires Pillow: pip install Pillow
import json
import math
import os

# --- Constants & Configuration ---
HEX_SIZE = 30 # Size (radius) of the hexagon
HEX_WIDTH = math.sqrt(3) * HEX_SIZE
HEX_HEIGHT = 2 * HEX_SIZE

# Default terrains if nothing is loaded
DEFAULT_TERRAINS = {
    # ID: [Display Name, Color, ImagePath (None or str), PropertiesDict]
    "0": ["Desert",   "#facc15", None, {"isWalkable": True, "moveCost": 1}],
    "1": ["Grass",    "#4ade80", None, {"isWalkable": True, "moveCost": 1}],
    "2": ["Forest",   "#16a34a", None, {"isWalkable": True, "moveCost": 2}],
    "3": ["Water",    "#38bdf8", None, {"isWalkable": False, "moveCost": 99}],
    "4": ["Mountain", "#a8a29e", None, {"isWalkable": False, "moveCost": 99}],
    "5": ["Wall",     "#57534e", None, {"isWalkable": False, "moveCost": 99}],
}
DEFAULT_TERRAIN_ID = "1" # Grass (use string)
ERASE_ID = "-1" # Special ID for erasing

ZOOM_SENSITIVITY = 1.1 # Multiplier for zoom steps
MIN_ZOOM = 0.1
MAX_ZOOM = 5.0

# Default filenames (can be changed via browse dialogs)
DEFAULT_MAP_FILENAME = 'map_data.json'
DEFAULT_TERRAINS_FILENAME = 'terrains.json'

# --- Helper Functions: Hex Grid Math ---
# [Functions hex_to_pixel, pixel_to_fractional_hex, hex_round, get_hex_vertices remain the same]
def hex_to_pixel(q, r):
    x = HEX_SIZE * (math.sqrt(3) * q + math.sqrt(3)/2 * r)
    y = HEX_SIZE * (3./2 * r)
    return x, y
def pixel_to_fractional_hex(x, y):
    q = (math.sqrt(3)/3 * x - 1./3 * y) / HEX_SIZE
    r = (2./3 * y) / HEX_SIZE
    return q, r
def hex_round(frac_q, frac_r):
    frac_s = -frac_q - frac_r
    q = round(frac_q); r = round(frac_r); s = round(frac_s)
    q_diff = abs(q - frac_q); r_diff = abs(r - frac_r); s_diff = abs(s - frac_s)
    if q_diff > r_diff and q_diff > s_diff: q = -r - s
    elif r_diff > s_diff: r = -q - s
    else: s = -q - r
    return q, r
def get_hex_vertices(cx, cy):
    vertices = []
    for i in range(6):
        angle = math.pi / 180 * (60 * i - 30)
        vx = cx + HEX_SIZE * math.cos(angle); vy = cy + HEX_SIZE * math.sin(angle)
        vertices.append((vx, vy))
    return vertices

# --- Main Application Class ---
class HexMapEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Hex Map Editor")
        self.root.geometry("950x700") # Adjusted size
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # State Variables
        self.map_data = {}
        self.terrains = DEFAULT_TERRAINS.copy()
        self.current_brush_id = DEFAULT_TERRAIN_ID
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.scale = 1.0
        self.is_panning = False
        self.is_painting = False
        self.is_erasing = False
        self.last_pan_x = 0
        self.last_pan_y = 0
        self.last_painted_hex_key = None
        self.terrain_buttons = {}
        self.selected_brush_var = tk.StringVar(value=self.current_brush_id)
        self.loaded_images = {} # Cache for loaded PhotoImage objects {path: PhotoImage}
        self.script_dir = os.path.dirname(os.path.abspath(__file__)) # More robust way to get script dir
        
        # Character data support
        self.characters = {}  # Will store character data if loaded
        self.show_characters = tk.BooleanVar(value=True)  # Toggle for showing characters

        # Define editor variables BEFORE creating the toolbar that uses them
        self.edit_name_var = tk.StringVar()
        self.edit_color_var = tk.StringVar()
        self.edit_image_path_var = tk.StringVar()
        self.edit_walkable_var = tk.BooleanVar()
        self.edit_move_cost_var = tk.IntVar()

        # Load data early
        self.load_terrains(os.path.join(self.script_dir, DEFAULT_TERRAINS_FILENAME), silent=True)
        self.load_map(os.path.join(self.script_dir, DEFAULT_MAP_FILENAME), silent=True)

        # --- Create UI Elements ---
        self._create_toolbar() # This now relies on editor variables being defined
        self._create_canvas()
        self._create_statusbar()

        # --- Bind Events ---
        self._bind_events()

        # Update editor UI for the initially selected brush AFTER toolbar is fully created
        self._update_terrain_editor_ui()

        # Center view initially if map is empty
        self.root.update_idletasks()
        if not self.map_data:
            self.offset_x = self.canvas.winfo_width() / 2
            self.offset_y = self.canvas.winfo_height() / 2

        # Initial render
        self.redraw_canvas()
        print("Hex editor initialized.")

    def _create_toolbar(self):
        self.toolbar_frame = ttk.Frame(self.root, padding="5", relief="raised", borderwidth=1)
        self.toolbar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)
        # Add row configurations if needed for layout adjustments

        current_row = 0
        # --- Terrain Brushes ---
        ttk.Label(self.toolbar_frame, text="Terrain Brushes", font="-weight bold").grid(row=current_row, column=0, columnspan=3, pady=(0, 5), sticky="w"); current_row += 1
        self.terrain_buttons_frame = ttk.Frame(self.toolbar_frame)
        self.terrain_buttons_frame.grid(row=current_row, column=0, columnspan=3, pady=5, sticky="nsew"); current_row += 1
        # Call this AFTER the editor widgets below are created
        # self._update_toolbar_buttons() # MOVED

        ttk.Separator(self.toolbar_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=3, sticky='ew', pady=10); current_row += 1
        
        # --- Character Controls ---
        ttk.Label(self.toolbar_frame, text="Characters", font="-weight bold").grid(row=current_row, column=0, columnspan=3, pady=(0, 5), sticky="w"); current_row += 1
        characters_frame = ttk.Frame(self.toolbar_frame)
        characters_frame.grid(row=current_row, column=0, columnspan=3, pady=5, sticky="nsew"); current_row += 1
        
        ttk.Checkbutton(characters_frame, text="Show Characters", variable=self.show_characters, command=self.redraw_canvas).pack(anchor="w")
        ttk.Button(characters_frame, text="Load Characters...", command=self._load_characters_action).pack(fill='x', pady=2)
        
        ttk.Separator(self.toolbar_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=3, sticky='ew', pady=10); current_row += 1

        # --- Edit Selected Tile ---
        ttk.Label(self.toolbar_frame, text="Edit Selected Tile", font="-weight bold").grid(row=current_row, column=0, columnspan=3, pady=(0, 5), sticky="w"); current_row += 1
        self.edit_tile_frame = ttk.Frame(self.toolbar_frame)
        self.edit_tile_frame.grid(row=current_row, column=0, columnspan=3, pady=5, sticky="nsew"); current_row += 1
        self.edit_tile_frame.columnconfigure(1, weight=1) # Allow entry/label to expand

        # Create editor widgets (variables are already defined in __init__)
        ttk.Label(self.edit_tile_frame, text="Name:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.edit_name_entry = ttk.Entry(self.edit_tile_frame, textvariable=self.edit_name_var, width=18)
        self.edit_name_entry.grid(row=0, column=1, columnspan=2, sticky="ew")

        ttk.Label(self.edit_tile_frame, text="Color:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5,0))
        self.edit_color_button = tk.Button(self.edit_tile_frame, text="Pick", width=5, command=self._pick_edit_tile_color)
        self.edit_color_button.grid(row=1, column=1, sticky="w", pady=(5,0))
        self.edit_color_preview = tk.Label(self.edit_tile_frame, text="", width=3, background="#ffffff", relief="sunken", borderwidth=1)
        self.edit_color_preview.grid(row=1, column=2, sticky="e", padx=(5,0), pady=(5,0))

        ttk.Label(self.edit_tile_frame, text="Image:").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=(5,0))
        self.edit_image_button = ttk.Button(self.edit_tile_frame, text="Browse...", width=8, command=self._browse_tile_image)
        self.edit_image_button.grid(row=2, column=1, sticky="w", pady=(5,0))
        self.edit_image_clear_button = ttk.Button(self.edit_tile_frame, text="Clear", width=5, command=self._clear_tile_image)
        self.edit_image_clear_button.grid(row=2, column=2, sticky="e", padx=(5,0), pady=(5,0))
        self.edit_image_label = ttk.Label(self.edit_tile_frame, textvariable=self.edit_image_path_var, wraplength=180, justify="left", foreground="grey") # Display path
        self.edit_image_label.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(2,0))

        ttk.Label(self.edit_tile_frame, text="Walkable:").grid(row=4, column=0, sticky="w", padx=(0, 5), pady=(5,0))
        self.edit_walkable_check = ttk.Checkbutton(self.edit_tile_frame, variable=self.edit_walkable_var)
        self.edit_walkable_check.grid(row=4, column=1, columnspan=2, sticky="w", pady=(5,0))

        # Add Move Cost later if needed
        # ttk.Label(self.edit_tile_frame, text="Move Cost:").grid(row=5, column=0, sticky="w", padx=(0, 5), pady=(5,0))
        # self.edit_move_cost_spin = ttk.Spinbox(self.edit_tile_frame, from_=1, to=99, width=5, textvariable=self.edit_move_cost_var)
        # self.edit_move_cost_spin.grid(row=5, column=1, columnspan=2, sticky="w", pady=(5,0))

        ttk.Button(self.edit_tile_frame, text="Apply Changes", command=self._apply_tile_changes).grid(row=6, column=0, columnspan=3, pady=(10, 0), sticky="ew")

        ttk.Separator(self.toolbar_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=3, sticky='ew', pady=10); current_row += 1

        # --- Create Custom Tile ---
        ttk.Label(self.toolbar_frame, text="Create New Tile", font="-weight bold").grid(row=current_row, column=0, columnspan=3, pady=(0, 5), sticky="w"); current_row += 1
        create_tile_frame = ttk.Frame(self.toolbar_frame)
        create_tile_frame.grid(row=current_row, column=0, columnspan=3, pady=5, sticky="nsew"); current_row += 1
        create_tile_frame.columnconfigure(1, weight=1)

        ttk.Label(create_tile_frame, text="Name:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.create_tile_name_entry = ttk.Entry(create_tile_frame, width=18)
        self.create_tile_name_entry.grid(row=0, column=1, columnspan=2, sticky="ew")

        ttk.Label(create_tile_frame, text="Color:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5,0))
        self.create_tile_color_var = tk.StringVar(value="#cccccc")
        self.create_tile_color_button = tk.Button(create_tile_frame, text="Pick", width=5, command=self._pick_create_tile_color)
        self.create_tile_color_button.grid(row=1, column=1, sticky="w", pady=(5,0))
        self.create_tile_color_preview = tk.Label(create_tile_frame, text="", width=3, background=self.create_tile_color_var.get(), relief="sunken", borderwidth=1)
        self.create_tile_color_preview.grid(row=1, column=2, sticky="e", padx=(5,0), pady=(5,0))

        ttk.Button(create_tile_frame, text="Create Tile", command=self._add_custom_tile).grid(row=2, column=0, columnspan=3, pady=(10, 0), sticky="ew")

        ttk.Separator(self.toolbar_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=3, sticky='ew', pady=10); current_row += 1

        # --- Map Actions ---
        ttk.Label(self.toolbar_frame, text="Map Actions", font="-weight bold").grid(row=current_row, column=0, columnspan=3, pady=(0, 5), sticky="w"); current_row += 1
        map_actions_frame = ttk.Frame(self.toolbar_frame)
        map_actions_frame.grid(row=current_row, column=0, columnspan=3, pady=5, sticky="nsew"); current_row += 1
        ttk.Button(map_actions_frame, text="Save Map As...", command=self._save_map_as).pack(fill='x', pady=2)
        ttk.Button(map_actions_frame, text="Load Map...", command=self._load_map_action).pack(fill='x', pady=2)
        ttk.Button(map_actions_frame, text="Clear Map", command=self.clear_map).pack(fill='x', pady=2)

        ttk.Separator(self.toolbar_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=3, sticky='ew', pady=10); current_row += 1

        # --- Controls Info ---
        controls_label = ttk.Label(self.toolbar_frame, text=(
            "Controls:\n"
            "Left Click/Drag: Paint\n"
            "Right Click/Drag: Erase\n"
            "Middle Drag: Pan\n"
            "Scroll Wheel: Zoom"
        ), justify="left")
        controls_label.grid(row=current_row, column=0, columnspan=3, sticky='w', pady=5); current_row += 1

        # --- NOW update the terrain buttons ---
        # This ensures the editor widgets exist before _update_terrain_editor_ui is potentially called
        self._update_toolbar_buttons()


    def _update_toolbar_buttons(self):
        for widget in self.terrain_buttons_frame.winfo_children():
            widget.destroy()
        self.terrain_buttons.clear()
        sorted_ids = sorted(self.terrains.keys(), key=lambda x: int(x))

        for terrain_id in sorted_ids:
            data = self.terrains[terrain_id]
            name = data[0]
            color = data[1]
            image_path = data[2] if len(data) > 2 else None

            btn_frame = ttk.Frame(self.terrain_buttons_frame)
            btn_frame.pack(fill='x', anchor='w')

            # Display image thumb or color swatch
            img_label = tk.Label(btn_frame, text="", width=2, height=1, relief="sunken", borderwidth=1)
            if image_path:
                thumb = self._get_cached_image(image_path, size=(20, 20)) # Load/get thumbnail
                if thumb:
                    img_label.config(image=thumb, width=20, height=20) # Keep ref via widget
                else:
                    img_label.config(background=color) # Fallback color
            else:
                img_label.config(background=color)
            img_label.pack(side="left", padx=(0, 5))


            rb = ttk.Radiobutton(
                btn_frame, text=name, variable=self.selected_brush_var,
                value=terrain_id, command=self._on_brush_selected
            )
            rb.pack(side="left", anchor='w', fill='x', expand=True)
            self.terrain_buttons[terrain_id] = rb

        if self.current_brush_id not in self.terrains:
            self.current_brush_id = DEFAULT_TERRAIN_ID if DEFAULT_TERRAIN_ID in self.terrains else (sorted_ids[0] if sorted_ids else None)

        if self.current_brush_id:
            self.selected_brush_var.set(self.current_brush_id)
            # Don't call _on_brush_selected here, it will be called by the variable trace or explicitly in __init__
            # self._on_brush_selected() # REMOVED


    def _pick_color(self, initial_color, callback):
        """Helper to pick color and call callback with hex result."""
        color_code = colorchooser.askcolor(title="Choose color", initialcolor=initial_color)
        if color_code and color_code[1]:
            callback(color_code[1])

    def _pick_edit_tile_color(self):
        self._pick_color(self.edit_color_var.get(), self._update_edit_color)

    def _update_edit_color(self, hex_color):
        self.edit_color_var.set(hex_color)
        self.edit_color_preview.config(background=hex_color)

    def _pick_create_tile_color(self):
        self._pick_color(self.create_tile_color_var.get(), self._update_create_color)

    def _update_create_color(self, hex_color):
        self.create_tile_color_var.set(hex_color)
        self.create_tile_color_preview.config(background=hex_color)

    def _browse_tile_image(self):
        filepath = filedialog.askopenfilename(
            title="Select Tile Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif *.ico"), ("All Files", "*.*")]
        )
        if filepath:
            # Try to make path relative to script dir if possible
            try:
                rel_path = os.path.relpath(filepath, self.script_dir)
                self.edit_image_path_var.set(rel_path)
            except ValueError: # If path is on a different drive (Windows)
                self.edit_image_path_var.set(filepath) # Use absolute path
            print(f"Selected image: {self.edit_image_path_var.get()}")


    def _clear_tile_image(self):
        self.edit_image_path_var.set("") # Set path to empty string

    def _add_custom_tile(self):
        name = self.create_tile_name_entry.get().strip()
        color = self.create_tile_color_var.get()

        if not name: messagebox.showwarning("Input Error", "Please enter a name."); return
        if not color or not color.startswith("#"): messagebox.showwarning("Input Error", "Please pick a valid color."); return

        existing_ids = [int(id_str) for id_str in self.terrains.keys()]
        next_id = str(max(existing_ids) + 1 if existing_ids else 0)

        # Create new terrain with default properties
        self.terrains[next_id] = [name, color, None, {"isWalkable": True, "moveCost": 1}]
        print(f"Added custom tile: ID {next_id}, Name: {name}, Color: {color}")

        self._update_toolbar_buttons()
        self.save_terrains()

        self.selected_brush_var.set(next_id)
        self._on_brush_selected() # Also updates editor UI

        self.create_tile_name_entry.delete(0, tk.END)

    def _apply_tile_changes(self):
        """Apply changes made in the 'Edit Selected Tile' section."""
        edit_id = self.selected_brush_var.get()
        if not edit_id or edit_id not in self.terrains:
            messagebox.showerror("Error", "No valid tile selected to apply changes to.")
            return

        old_data = self.terrains[edit_id]
        new_name = self.edit_name_var.get().strip()
        new_color = self.edit_color_var.get()
        new_image_path = self.edit_image_path_var.get().strip()
        new_walkable = self.edit_walkable_var.get()
        # new_move_cost = self.edit_move_cost_var.get() # Add if using move cost editor

        if not new_name: messagebox.showwarning("Input Error", "Tile name cannot be empty."); return
        if not new_color or not new_color.startswith("#"): messagebox.showwarning("Input Error", "Invalid color."); return

        # Prepare properties dictionary
        new_props = {"isWalkable": new_walkable}
        # new_props["moveCost"] = new_move_cost # Add if using move cost editor

        # Handle empty image path as None
        if not new_image_path:
            new_image_path = None
        elif new_image_path != old_data[2]: # If image path changed, clear old image from cache
            # Construct the full path for cache key comparison/deletion
            old_full_path = old_data[2]
            if old_full_path and not os.path.isabs(old_full_path):
                old_full_path = os.path.join(self.script_dir, old_full_path)

            # Clear cache entries related to the old path
            keys_to_delete = [k for k in self.loaded_images if k.startswith(old_full_path)]
            for k in keys_to_delete:
                print(f"Clearing image cache for old path: {k}")
                del self.loaded_images[k]


        # Update the terrains dictionary
        self.terrains[edit_id] = [new_name, new_color, new_image_path, new_props]

        print(f"Applied changes to tile ID {edit_id}")

        # Update UI and save
        self._update_toolbar_buttons() # Reflect name/image changes
        self._update_terrain_editor_ui() # Refresh editor fields (might be redundant but safe)
        self.save_terrains()
        self.redraw_canvas() # Redraw map in case color/image changed


    def _on_brush_selected(self):
        """Update internal state and the editor UI when brush changes."""
        self.current_brush_id = self.selected_brush_var.get()
        self._update_terrain_editor_ui()
        # print(f"Selected brush ID: {self.current_brush_id}")

    def _update_terrain_editor_ui(self):
        """Populate the 'Edit Selected Tile' fields based on current brush."""
        edit_id = self.current_brush_id # Get the currently selected ID string
        if edit_id and edit_id in self.terrains:
            data = self.terrains[edit_id]
            # Ensure data has the expected structure (list with at least 4 elements)
            if isinstance(data, list) and len(data) >= 4:
                props = data[3] if isinstance(data[3], dict) else {} # Get props dict safely
                name = data[0]
                color = data[1]
                image_path = data[2] if data[2] else "" # Use empty string if None
                walkable = props.get("isWalkable", True) # Default to True if missing

                self.edit_name_var.set(name)
                self.edit_color_var.set(color)
                self.edit_image_path_var.set(image_path)
                self.edit_walkable_var.set(walkable)
                # self.edit_move_cost_var.set(props.get("moveCost", 1)) # Add if using move cost

                self.edit_color_preview.config(background=color)
                # Enable editing widgets
                for widget in self.edit_tile_frame.winfo_children():
                    widget.config(state=tk.NORMAL)
            else:
                print(f"Warning: Invalid data structure for terrain ID {edit_id}: {data}")
                self._disable_editor_ui() # Disable UI if data is bad
        else:
            self._disable_editor_ui() # Disable UI if no valid selection

    def _disable_editor_ui(self):
         """Clears and disables the editor fields."""
         self.edit_name_var.set("")
         self.edit_color_var.set("#ffffff")
         self.edit_image_path_var.set("")
         self.edit_walkable_var.set(False)
         # self.edit_move_cost_var.set(1)
         self.edit_color_preview.config(background="#ffffff")
         # Disable editing widgets
         for widget in self.edit_tile_frame.winfo_children():
             if isinstance(widget, (ttk.Entry, ttk.Button, tk.Button, ttk.Checkbutton, ttk.Spinbox)):
                 widget.config(state=tk.DISABLED)


    def _create_canvas(self):
        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky="nsew")

    def _create_statusbar(self):
        self.statusbar_frame = ttk.Frame(self.root, padding="2", relief="sunken", borderwidth=1)
        self.statusbar_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.coord_label = ttk.Label(self.statusbar_frame, text="Q: -, R: -")
        self.coord_label.pack(side="right", padx=5)

    def _bind_events(self):
        # [Event bindings remain mostly the same]
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<ButtonPress-1>", self._on_left_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_release)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonPress-3>", self._on_right_press)
        self.canvas.bind("<ButtonRelease-3>", self._on_right_release)
        self.canvas.bind("<B3-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonPress-2>", self._on_middle_press)
        self.canvas.bind("<ButtonRelease-2>", self._on_middle_release)
        self.canvas.bind("<B2-Motion>", self._on_pan_drag)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", self._on_mouse_leave)

    # --- Event Handlers ---
    # [_on_canvas_resize, _screen_to_world, _world_to_screen, _get_hex_at_screen_pos,
    #  _on_mouse_move, _on_mouse_leave, _on_left_press, _on_left_release,
    #  _on_right_press, _on_right_release, _on_mouse_drag, _on_middle_press,
    #  _on_middle_release, _on_pan_drag, _on_mouse_wheel remain the same]
    def _on_canvas_resize(self, event): self.redraw_canvas()
    def _screen_to_world(self, screen_x, screen_y):
        world_x = (screen_x - self.offset_x) / self.scale; world_y = (screen_y - self.offset_y) / self.scale
        return world_x, world_y
    def _world_to_screen(self, world_x, world_y):
        screen_x = world_x * self.scale + self.offset_x; screen_y = world_y * self.scale + self.offset_y
        return screen_x, screen_y
    def _get_hex_at_screen_pos(self, screen_x, screen_y):
        world_x, world_y = self._screen_to_world(screen_x, screen_y)
        q, r = pixel_to_fractional_hex(world_x, world_y); return hex_round(q, r)
    def _on_mouse_move(self, event):
        q, r = self._get_hex_at_screen_pos(event.x, event.y); self.coord_label.config(text=f"Q: {q}, R: {r}")
    def _on_mouse_leave(self, event): self.coord_label.config(text="Q: -, R: -")
    def _on_left_press(self, event):
        self.is_painting = True; self.last_painted_hex_key = None; self._paint_or_erase_at(event.x, event.y, True)
    def _on_left_release(self, event): self.is_painting = False; self.last_painted_hex_key = None
    def _on_right_press(self, event):
        self.is_erasing = True; self.last_painted_hex_key = None; self._paint_or_erase_at(event.x, event.y, False)
    def _on_right_release(self, event): self.is_erasing = False; self.last_painted_hex_key = None
    def _on_mouse_drag(self, event):
        if self.is_painting: self._paint_or_erase_at(event.x, event.y, True)
        elif self.is_erasing: self._paint_or_erase_at(event.x, event.y, False)
    def _on_middle_press(self, event):
        self.is_panning = True; self.last_pan_x = event.x; self.last_pan_y = event.y; self.canvas.config(cursor="fleur")
    def _on_middle_release(self, event): self.is_panning = False; self.canvas.config(cursor="")
    def _on_pan_drag(self, event):
        if self.is_panning:
            dx = event.x - self.last_pan_x; dy = event.y - self.last_pan_y
            self.offset_x += dx; self.offset_y += dy
            self.last_pan_x = event.x; self.last_pan_y = event.y
            self.redraw_canvas()
    def _on_mouse_wheel(self, event):
        delta = 0
        if event.num == 5 or event.delta < 0: delta = -1
        elif event.num == 4 or event.delta > 0: delta = 1
        else: return
        zoom_factor = ZOOM_SENSITIVITY if delta > 0 else 1 / ZOOM_SENSITIVITY
        new_scale = max(MIN_ZOOM, min(MAX_ZOOM, self.scale * zoom_factor))
        if new_scale == self.scale: return
        world_x_before, world_y_before = self._screen_to_world(event.x, event.y)
        self.scale = new_scale
        self.offset_x = event.x - world_x_before * self.scale
        self.offset_y = event.y - world_y_before * self.scale
        self.redraw_canvas()


    # --- Painting & Erasing Logic ---
    def _paint_or_erase_at(self, screen_x, screen_y, is_paint_mode):
        q, r = self._get_hex_at_screen_pos(screen_x, screen_y)
        key = f"{q},{r}"
        if key == self.last_painted_hex_key: return

        current_value = self.map_data.get(key)
        changed = False
        if is_paint_mode:
            if current_value != self.current_brush_id:
                self.map_data[key] = self.current_brush_id
                changed = True
        else: # Erase mode
            if key in self.map_data:
                del self.map_data[key]
                changed = True

        if changed:
            self._draw_single_hex(q, r) # Redraw only the changed hex
        self.last_painted_hex_key = key


    # --- Image Handling ---
    def _get_cached_image(self, image_path, size=None):
        """Loads image, resizes (optional), caches, and returns PhotoImage."""
        if not image_path: return None

        # Resolve potential relative path
        if not os.path.isabs(image_path):
            image_path = os.path.join(self.script_dir, image_path)

        cache_key = f"{image_path}_{size}" if size else image_path

        if cache_key in self.loaded_images:
            return self.loaded_images[cache_key]

        try:
            if not os.path.exists(image_path):
                print(f"Warning: Image file not found: {image_path}")
                return None

            img = Image.open(image_path)
            img.load() # Load image data

            # Handle transparency
            # if img.mode == 'RGBA' or 'transparency' in img.info:
                 # PhotoImage handles basic RGBA transparency
                 # More complex masking might be needed for other modes
                 # img = img.convert("RGBA") # Ensure RGBA?

            # Resize if needed (maintaining aspect ratio)
            if size:
                 # Create a copy before thumbnail to avoid modifying original Image object if cached differently
                 thumb_img = img.copy()
                 thumb_img.thumbnail(size, Image.Resampling.LANCZOS) # Resize inplace to fit within size
                 img_to_convert = thumb_img
            else:
                 img_to_convert = img


            photo_img = ImageTk.PhotoImage(img_to_convert)
            self.loaded_images[cache_key] = photo_img # Cache it
            # print(f"Loaded and cached image: {cache_key}")
            return photo_img
        except Exception as e:
            print(f"❌ Error loading image {image_path}: {e}")
            if cache_key in self.loaded_images: # Clean cache on error
                 del self.loaded_images[k]
            return None


    # --- Drawing ---
    def redraw_canvas(self):
        self.canvas.delete("all")
        # Calculate visible hex range
        world_x_min, world_y_min = self._screen_to_world(0, 0)
        world_x_max, world_y_max = self._screen_to_world(self.canvas.winfo_width(), self.canvas.winfo_height())
        frac_q_min, frac_r_min = pixel_to_fractional_hex(world_x_min, world_y_min)
        frac_q_max, frac_r_max = pixel_to_fractional_hex(world_x_max, world_y_max)
        q_min = math.floor(min(frac_q_min, frac_q_max)) - 2
        q_max = math.ceil(max(frac_q_min, frac_q_max)) + 2
        r_min = math.floor(min(frac_r_min, frac_r_max)) - 2
        r_max = math.ceil(max(frac_r_min, frac_r_max)) + 2

        # Keep track of images drawn in this frame to avoid issues with garbage collection
        self._current_frame_images = []

        # Draw hexes first (as background)
        for r in range(r_min, r_max + 1):
            for q in range(q_min, q_max + 1):
                self._draw_single_hex(q, r)
                
        # Then draw characters on top if enabled
        if self.show_characters.get() and self.characters:
            self._draw_characters()

    def _draw_single_hex(self, q, r):
        key = f"{q},{r}"
        terrain_id = self.map_data.get(key)
        hex_tag = f"hex_{q}_{r}"
        self.canvas.delete(hex_tag) # Clear previous drawing

        center_x_world, center_y_world = hex_to_pixel(q, r)
        center_x_screen, center_y_screen = self._world_to_screen(center_x_world, center_y_world)

        terrain_data = self.terrains.get(str(terrain_id)) if terrain_id is not None else None
        image_path = terrain_data[2] if terrain_data and len(terrain_data) > 2 else None
        photo_image = None

        if image_path:
            # Calculate approx screen size for image loading
            # Use HEX_WIDTH/HEIGHT which are based on HEX_SIZE, apply scale
            hex_screen_width = HEX_WIDTH * self.scale
            hex_screen_height = HEX_HEIGHT * 0.75 * self.scale # Pointy top height factor
            # Load/get image sized roughly to the hex display size
            photo_image = self._get_cached_image(image_path, size=(int(hex_screen_width), int(hex_screen_height)))

        # Draw Image OR Color Polygon
        if photo_image:
             # Draw image centered on the hex
             img_item = self.canvas.create_image(center_x_screen, center_y_screen, image=photo_image, tags=(hex_tag, "hex"))
             # Keep a reference if needed (handled by cache now)
             # self._current_frame_images.append(photo_image)

             # Optionally draw outline over image
             screen_vertices = []
             hex_vertices_world = get_hex_vertices(center_x_world, center_y_world)
             for vx_w, vy_w in hex_vertices_world:
                 vx_s, vy_s = self._world_to_screen(vx_w, vy_w)
                 screen_vertices.extend([vx_s, vy_s])
             self.canvas.create_polygon(
                 screen_vertices, fill="", outline="#333333", # Dark outline over image
                 width=max(1, 1 / self.scale), tags=(hex_tag, "hex_outline")
             )

        else:
            # Fallback to color or empty outline
            screen_vertices = []
            hex_vertices_world = get_hex_vertices(center_x_world, center_y_world)
            for vx_w, vy_w in hex_vertices_world:
                vx_s, vy_s = self._world_to_screen(vx_w, vy_w)
                screen_vertices.extend([vx_s, vy_s])

            fill_color = ""
            outline_color = "#e5e5e5"
            line_width = max(1, 1 / self.scale)

            if terrain_data:
                fill_color = terrain_data[1]
                outline_color = "#6b7280"
            elif terrain_id is not None: # Unknown ID
                 outline_color = "#FF00FF"

            self.canvas.create_polygon(
                screen_vertices, fill=fill_color, outline=outline_color,
                width=line_width, tags=(hex_tag, "hex")
            )

    def _draw_characters(self):
        """Draw all characters on the map"""
        if not self.characters:
            return
            
        for char_id, char_data in self.characters.items():
            # Get character position
            position = char_data.get("position", {})
            q = position.get("q", 0)
            r = position.get("r", 0)
            
            # Get world coordinates
            center_x_world, center_y_world = hex_to_pixel(q, r)
            center_x_screen, center_y_screen = self._world_to_screen(center_x_world, center_y_world)
            
            # Calculate character display size based on hex size
            # Use the full hex width/height instead of a percentage
            hex_screen_width = HEX_WIDTH * self.scale
            hex_screen_height = HEX_HEIGHT * self.scale
            
            # Get character sprite if available
            sprite_path = char_data.get("sprite", "")
            photo_image = None
            
            if sprite_path:
                # Use the complete hex size for the character image
                photo_image = self._get_cached_image(sprite_path, size=(int(hex_screen_width), int(hex_screen_height)))
            
            if photo_image:
                # Draw character sprite
                char_tag = f"char_{char_id}"
                img_item = self.canvas.create_image(
                    center_x_screen, center_y_screen, 
                    image=photo_image, 
                    tags=(char_tag, "character")
                )
                self._current_frame_images.append(photo_image)
                
                # Optional: Add subtle outline to make character boundary visible
                screen_vertices = []
                hex_vertices_world = get_hex_vertices(center_x_world, center_y_world)
                for vx_w, vy_w in hex_vertices_world:
                    vx_s, vy_s = self._world_to_screen(vx_w, vy_w)
                    screen_vertices.extend([vx_s, vy_s])
                    
                self.canvas.create_polygon(
                    screen_vertices, fill="", outline="#ffffff", 
                    width=max(1, 0.5 * self.scale), 
                    tags=(char_tag, "character_outline"),
                    dash=(3,3)  # Creates dotted line outline
                )
            else:
                # Fallback to circle with first letter of name
                char_name = char_data.get("name", "?")
                char_class = char_data.get("class", "")
                char_letter = char_name[0] if char_name else "?"
                
                # Draw circle (use more of the hex area)
                char_size = hex_screen_width * 0.8  # Larger default size
                outline_width = max(1, 1 * self.scale)
                char_tag = f"char_{char_id}"
                
                # Choose color based on character class
                colors = {
                    "Warrior": "#e74c3c",
                    "Mage": "#3498db",
                    "Rogue": "#2ecc71",
                    "Cleric": "#f1c40f",
                    "Ranger": "#9b59b6"
                }
                fill_color = colors.get(char_class, "#95a5a6")  # Default gray
                
                self.canvas.create_oval(
                    center_x_screen - char_size/2, center_y_screen - char_size/2,
                    center_x_screen + char_size/2, center_y_screen + char_size/2,
                    fill=fill_color, outline="black", width=outline_width,
                    tags=(char_tag, "character")
                )
                
                # Add text (first letter of name)
                font_size = max(10, int(char_size/3))
                self.canvas.create_text(
                    center_x_screen, center_y_screen,
                    text=char_letter, fill="white", font=("Arial", font_size, "bold"),
                    tags=(char_tag, "character_text")
                )
                
            # Add tooltip on hover with character info
            self._add_character_tooltip(char_id, center_x_screen, center_y_screen, 
                                        hex_screen_width if photo_image else char_size, 
                                        char_data)
    
    def _add_character_tooltip(self, char_id, x, y, size, char_data):
        """Add tooltip-like behavior for a character"""
        char_tag = f"char_{char_id}"
        
        def show_tooltip(event):
            # Remove any existing tooltips
            self.canvas.delete("tooltip")
            
            # Create tooltip with character info
            char_name = char_data.get("name", "Unknown")
            char_class = char_data.get("class", "")
            stats = char_data.get("stats", {})
            
            # Build tooltip text
            tooltip_text = f"{char_name}\n{char_class}\n"
            if stats:
                tooltip_text += f"HP: {stats.get('hp', 0)}  ATK: {stats.get('attack', 0)}\n"
                tooltip_text += f"DEF: {stats.get('defense', 0)}  SPD: {stats.get('speed', 0)}"
            
            # Calculate tooltip position
            tooltip_x = x
            tooltip_y = y - size - 5  # Above the character
            
            # Create tooltip background
            bg = self.canvas.create_rectangle(
                tooltip_x - 80, tooltip_y - 40,
                tooltip_x + 80, tooltip_y + 5,
                fill="#333333", outline="#ffffff", width=1,
                tags=("tooltip",)
            )
            
            # Create tooltip text
            text = self.canvas.create_text(
                tooltip_x, tooltip_y - 18,
                text=tooltip_text, fill="#ffffff", font=("Arial", 9),
                tags=("tooltip",), justify="center"
            )
        
        def hide_tooltip(event):
            self.canvas.delete("tooltip")
        
        # Bind mouse events to character elements
        for item in self.canvas.find_withtag(char_tag):
            tag_id = f"tooltip_bind_{char_id}_{item}"
            self.canvas.tag_bind(item, "<Enter>", show_tooltip, tag_id)
            self.canvas.tag_bind(item, "<Leave>", hide_tooltip, tag_id)

    # --- Save/Load Logic ---
    def _get_save_path(self, default_filename, title, filetypes):
        """Opens save dialog and returns chosen path or None."""
        filepath = filedialog.asksaveasfilename(
            title=title,
            initialdir=self.script_dir,
            initialfile=default_filename,
            defaultextension=".json",
            filetypes=filetypes
        )
        return filepath # Returns empty string if cancelled

    def _get_load_path(self, title, filetypes):
        """Opens load dialog and returns chosen path or None."""
        filepath = filedialog.askopenfilename(
            title=title,
            initialdir=self.script_dir,
            defaultextension=".json",
            filetypes=filetypes
        )
        return filepath # Returns empty string if cancelled

    def save_terrains(self, filepath=None):
        """Saves terrain definitions to the specified path or default."""
        if not filepath:
             filepath = os.path.join(self.script_dir, DEFAULT_TERRAINS_FILENAME)
        try:
            with open(filepath, 'w') as f:
                json.dump(self.terrains, f, indent=4)
            print(f"Custom terrains saved to {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error saving terrains: {e}")
            messagebox.showerror("Save Error", f"Could not save terrain definitions to\n{filepath}\n\nError: {e}")
            return False

    def load_terrains(self, filepath=None, silent=False):
        """Loads terrain definitions from the specified path or default."""
        if not filepath:
            filepath = os.path.join(self.script_dir, DEFAULT_TERRAINS_FILENAME)
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    loaded_terrains = json.load(f)
                    if isinstance(loaded_terrains, dict):
                        self.terrains = loaded_terrains # Overwrite current
                        print(f"Custom terrains loaded from {filepath}")
                        # Clear image cache as paths might have changed relative to new file location? Or assume paths are relative to script dir.
                        self.loaded_images.clear()
                        return True
                    else:
                        if not silent: messagebox.showwarning("Load Warning", f"Invalid terrain data format in {filepath}, using defaults.")
                        print(f"⚠️ Invalid terrain data format in {filepath}, using defaults.")
                        self.terrains = DEFAULT_TERRAINS.copy()
            else:
                if not silent: print("No custom terrains file found, using defaults.")
                self.terrains = DEFAULT_TERRAINS.copy()
        except Exception as e:
            if not silent: messagebox.showerror("Load Error", f"Could not load terrain definitions from\n{filepath}\n\nError: {e}")
            print(f"❌ Error loading terrains: {e}")
            self.terrains = DEFAULT_TERRAINS.copy() # Fallback
        return False


    def _save_map_as(self):
        """Saves both terrains and map data using file dialogs."""
        # 1. Save Terrains
        terrain_path = self._get_save_path(DEFAULT_TERRAINS_FILENAME, "Save Terrain Definitions As...", [("JSON files", "*.json")])
        if not terrain_path:
             print("Terrain save cancelled.")
             return # User cancelled terrain save

        if not self.save_terrains(terrain_path):
             return # Error occurred during terrain save

        # 2. Save Map Data
        map_path = self._get_save_path(DEFAULT_MAP_FILENAME, "Save Map Data As...", [("JSON files", "*.json")])
        if not map_path:
             print("Map data save cancelled.")
             # Should we revert terrain save? Maybe not.
             return # User cancelled map save

        try:
            with open(map_path, 'w') as f:
                json.dump(self.map_data, f, indent=4)
            print(f"💾 Map saved successfully to {map_path} ({len(self.map_data)} cells).")
            messagebox.showinfo("Save Successful", f"Terrains saved to:\n{terrain_path}\n\nMap saved to:\n{map_path}")
        except Exception as e:
            print(f"❌ Error saving map data: {e}")
            messagebox.showerror("Save Error", f"Could not save map data to\n{map_path}\n\nError: {e}")


    def _load_map_action(self):
        """Loads terrains and map data using file dialogs."""
        # 1. Load Terrains
        terrain_path = self._get_load_path("Load Terrain Definitions", [("JSON files", "*.json")])
        if not terrain_path:
            print("Terrain load cancelled.")
            return # User cancelled

        if not self.load_terrains(terrain_path):
             # Error message already shown by load_terrains
             return

        # 2. Load Map Data
        map_path = self._get_load_path("Load Map Data", [("JSON files", "*.json")])
        if not map_path:
             print("Map data load cancelled.")
             return # User cancelled

        try:
            if os.path.exists(map_path):
                with open(map_path, 'r') as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, dict):
                        self.map_data = loaded_data
                        print(f"📂 Map data loaded successfully from {map_path}.")
                        messagebox.showinfo("Load Successful", f"Terrains loaded from:\n{terrain_path}\n\nMap loaded from:\n{map_path}")
                    else:
                        messagebox.showwarning("Load Warning", f"Invalid map data format in\n{map_path}")
                        self.map_data = {} # Reset map
            else:
                 messagebox.showwarning("Load Warning", f"Map data file not found:\n{map_path}")
                 self.map_data = {} # Ensure map is empty
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load map data from\n{map_path}\n\nError: {e}")
            self.map_data = {} # Reset map

        # 3. Refresh UI and Canvas
        self.last_painted_hex_key = None
        self._update_toolbar_buttons() # Refresh toolbar with loaded terrains
        self._update_terrain_editor_ui() # Update editor based on current brush
        self.redraw_canvas() # Redraw map

    def load_map(self, filepath=None, silent=False):
        """Internal: Loads only map cell data from a given path or default."""
        # This is mostly used for initial load now. User loads use _load_map_action.
        if not filepath:
            filepath = os.path.join(self.script_dir, DEFAULT_MAP_FILENAME)
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, dict):
                        self.map_data = loaded_data
                        if not silent: print(f"📂 Map data loaded successfully from {filepath}.")
                    else:
                        if not silent: print(f"⚠️ Invalid map data format in {filepath}.")
                        self.map_data = {}
            else:
                if not silent: print("No saved map data file found.")
                self.map_data = {}
        except Exception as e:
            if not silent: print(f"❌ Error loading map data: {e}")
            self.map_data = {}
        self.last_painted_hex_key = None

    def clear_map(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the entire map? This cannot be undone."):
            self.map_data = {}
            print("Map cleared.")
            self.last_painted_hex_key = None
            self.redraw_canvas()
            # Optionally reset terrains?
            # if messagebox.askyesno("Reset Terrains?", "Also reset custom terrains to default?"):
            #     terrain_filepath = os.path.join(self.script_dir, DEFAULT_TERRAINS_FILENAME)
            #     if os.path.exists(terrain_filepath):
            #         try: os.remove(terrain_filepath); print("Removed custom terrains file.")
            #         except Exception as e: print(f"Could not remove terrains file: {e}")
            #     self.load_terrains(silent=True)
            #     self._update_toolbar_buttons()
            #     self._update_terrain_editor_ui()

    def _load_characters_action(self):
        """Load character data from a JSON file exported by CharacterForge"""
        filepath = filedialog.askopenfilename(
            title="Load Characters",
            initialdir=self.script_dir,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if not filepath:
            return  # User cancelled
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
                # Check if this is a CharacterForge export format
                if isinstance(data, dict) and "characters" in data:
                    self.characters = data["characters"]
                    print(f"Loaded {len(self.characters)} characters from {filepath}")
                    messagebox.showinfo("Success", f"Loaded {len(self.characters)} characters")
                else:
                    # Try to load direct character dictionary format
                    if isinstance(data, dict):
                        self.characters = data
                        print(f"Loaded {len(self.characters)} characters from {filepath}")
                        messagebox.showinfo("Success", f"Loaded {len(self.characters)} characters")
                    else:
                        messagebox.showerror("Error", "Invalid character data format")
                        return
                    
                # Enable character display and redraw
                self.show_characters.set(True)
                self.redraw_canvas()
                
        except Exception as e:
            print(f"Error loading character data: {e}")
            messagebox.showerror("Error", f"Could not load character data: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    # Set a theme for better looking widgets if available
    try:
        style = ttk.Style(root)
        # Try common theme names
        available_themes = style.theme_names()
        # print("Available themes:", available_themes) # Debug
        if 'clam' in available_themes: style.theme_use('clam')
        elif 'alt' in available_themes: style.theme_use('alt')
        elif 'vista' in available_themes: style.theme_use('vista') # Windows
        elif 'aqua' in available_themes: style.theme_use('aqua')   # macOS
    except Exception as e:
        print(f"Could not set ttk theme: {e}")

    app = HexMapEditorApp(root)
    root.mainloop()
`
