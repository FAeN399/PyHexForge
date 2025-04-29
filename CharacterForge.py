import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from PIL import Image, ImageTk

class CharacterForge:
    def __init__(self, root):
        self.root = root
        self.root.title("Character Forge")
        self.root.geometry("800x600")
        
        # Initialize character data
        self.characters = {}
        self.current_character_id = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.character_file = os.path.join(self.script_dir, "characters.json")
        
        # Load previously created characters if they exist
        self.load_characters()
        
        # Create the UI
        self._create_ui()
        
    def _create_ui(self):
        # Main frame with two sections
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Character list
        left_panel = ttk.LabelFrame(main_frame, text="Character List")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Character listbox
        self.character_listbox = tk.Listbox(left_panel, width=30)
        self.character_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.character_listbox.bind("<<ListboxSelect>>", self._on_character_selected)
        
        # Buttons for character management
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="New Character", command=self._new_character).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Character", command=self._delete_character).pack(side=tk.LEFT, padx=5)
        
        # Right panel - Character details
        right_panel = ttk.LabelFrame(main_frame, text="Character Details")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Character details form
        details_frame = ttk.Frame(right_panel)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Character name
        ttk.Label(details_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Character class
        ttk.Label(details_frame, text="Class:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.class_var = tk.StringVar()
        class_combo = ttk.Combobox(details_frame, textvariable=self.class_var, width=27)
        class_combo['values'] = ('Warrior', 'Mage', 'Rogue', 'Cleric', 'Ranger')
        class_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(details_frame, text="Stats")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # HP
        ttk.Label(stats_frame, text="HP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.hp_var = tk.IntVar(value=100)
        ttk.Spinbox(stats_frame, from_=1, to=999, textvariable=self.hp_var, width=5).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Attack
        ttk.Label(stats_frame, text="Attack:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20,0))
        self.attack_var = tk.IntVar(value=10)
        ttk.Spinbox(stats_frame, from_=1, to=99, textvariable=self.attack_var, width=5).grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # Defense
        ttk.Label(stats_frame, text="Defense:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.defense_var = tk.IntVar(value=8)
        ttk.Spinbox(stats_frame, from_=1, to=99, textvariable=self.defense_var, width=5).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Speed
        ttk.Label(stats_frame, text="Speed:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20,0))
        self.speed_var = tk.IntVar(value=6)
        ttk.Spinbox(stats_frame, from_=1, to=99, textvariable=self.speed_var, width=5).grid(row=1, column=3, sticky=tk.W, pady=5)
        
        # Position on hex map
        position_frame = ttk.LabelFrame(details_frame, text="Position on Map")
        position_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # Q coordinate
        ttk.Label(position_frame, text="Q:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.q_var = tk.IntVar(value=0)
        ttk.Spinbox(position_frame, from_=-99, to=99, textvariable=self.q_var, width=5).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # R coordinate
        ttk.Label(position_frame, text="R:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20,0))
        self.r_var = tk.IntVar(value=0)
        ttk.Spinbox(position_frame, from_=-99, to=99, textvariable=self.r_var, width=5).grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # Sprite/Avatar selection
        ttk.Label(details_frame, text="Sprite:").grid(row=4, column=0, sticky=tk.NW, pady=5)
        
        sprite_frame = ttk.Frame(details_frame)
        sprite_frame.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        self.sprite_path_var = tk.StringVar()
        ttk.Label(sprite_frame, textvariable=self.sprite_path_var, wraplength=250).pack(anchor=tk.W)
        
        sprite_btn_frame = ttk.Frame(sprite_frame)
        sprite_btn_frame.pack(anchor=tk.W, pady=(5,0))
        
        ttk.Button(sprite_btn_frame, text="Browse...", command=self._browse_sprite).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(sprite_btn_frame, text="Clear", command=self._clear_sprite).pack(side=tk.LEFT)
        
        # Preview area
        preview_frame = ttk.LabelFrame(details_frame, text="Preview")
        preview_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(pady=10)
        
        # Save buttons
        btn_frame2 = ttk.Frame(right_panel)
        btn_frame2.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame2, text="Save Character", command=self._save_character).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Export to PyHexForge", command=self._export_to_hexforge).pack(side=tk.LEFT, padx=5)
        
        # Disable the form initially until character is selected/created
        self._disable_form()
        
        # Populate the character list
        self._update_character_list()
    
    def load_characters(self):
        """Load characters from JSON file"""
        if os.path.exists(self.character_file):
            try:
                with open(self.character_file, 'r') as f:
                    self.characters = json.load(f)
                print(f"Loaded {len(self.characters)} characters")
            except Exception as e:
                print(f"Error loading characters: {e}")
                self.characters = {}
    
    def save_characters(self):
        """Save characters to JSON file"""
        try:
            with open(self.character_file, 'w') as f:
                json.dump(self.characters, f, indent=4)
            print(f"Saved {len(self.characters)} characters")
            return True
        except Exception as e:
            print(f"Error saving characters: {e}")
            messagebox.showerror("Error", f"Could not save characters: {e}")
            return False
    
    def _update_character_list(self):
        """Update the character listbox with current characters"""
        self.character_listbox.delete(0, tk.END)
        for char_id, char_data in self.characters.items():
            self.character_listbox.insert(tk.END, char_data.get('name', 'Unnamed'))
    
    def _on_character_selected(self, event):
        """Handle character selection from listbox"""
        selection = self.character_listbox.curselection()
        if not selection:
            return
        
        # Get the character ID from the selected index
        selected_index = selection[0]
        if selected_index < 0 or selected_index >= len(self.characters):
            return
        
        char_id = list(self.characters.keys())[selected_index]
        self.current_character_id = char_id
        
        # Load character data into form
        self._load_character_to_form(self.characters[char_id])
    
    def _load_character_to_form(self, char_data):
        """Load character data into the form fields"""
        self.name_var.set(char_data.get('name', ''))
        self.class_var.set(char_data.get('class', ''))
        
        # Stats
        stats = char_data.get('stats', {})
        self.hp_var.set(stats.get('hp', 100))
        self.attack_var.set(stats.get('attack', 10))
        self.defense_var.set(stats.get('defense', 8))
        self.speed_var.set(stats.get('speed', 6))
        
        # Position
        position = char_data.get('position', {})
        self.q_var.set(position.get('q', 0))
        self.r_var.set(position.get('r', 0))
        
        # Sprite
        sprite_path = char_data.get('sprite', '')
        self.sprite_path_var.set(sprite_path)
        self._update_preview()
        
        # Enable the form
        self._enable_form()
    
    def _new_character(self):
        """Create a new character"""
        # Generate a unique ID
        new_id = f"char_{len(self.characters) + 1:03d}"
        
        # Create default character data
        new_char = {
            'name': f"New Character {len(self.characters) + 1}",
            'class': 'Warrior',
            'stats': {
                'hp': 100,
                'attack': 10,
                'defense': 8,
                'speed': 6
            },
            'position': {
                'q': 0,
                'r': 0
            },
            'sprite': ''
        }
        
        # Add to characters dictionary
        self.characters[new_id] = new_char
        self.current_character_id = new_id
        
        # Update listbox and select the new character
        self._update_character_list()
        new_index = list(self.characters.keys()).index(new_id)
        self.character_listbox.selection_set(new_index)
        
        # Load character data into form
        self._load_character_to_form(new_char)
        
        # Save characters
        self.save_characters()
    
    def _delete_character(self):
        """Delete the selected character"""
        if not self.current_character_id:
            messagebox.showwarning("Warning", "Please select a character to delete.")
            return
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete {self.name_var.get()}?"):
            # Remove from dictionary
            del self.characters[self.current_character_id]
            self.current_character_id = None
            
            # Update listbox
            self._update_character_list()
            
            # Clear form
            self._disable_form()
            self._clear_form()
            
            # Save characters
            self.save_characters()
    
    def _save_character(self):
        """Save the current character data"""
        if not self.current_character_id:
            messagebox.showwarning("Warning", "No character selected.")
            return
        
        # Validate input
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a character name.")
            return
        
        # Create character data structure
        char_data = {
            'name': name,
            'class': self.class_var.get(),
            'stats': {
                'hp': self.hp_var.get(),
                'attack': self.attack_var.get(),
                'defense': self.defense_var.get(),
                'speed': self.speed_var.get()
            },
            'position': {
                'q': self.q_var.get(),
                'r': self.r_var.get()
            },
            'sprite': self.sprite_path_var.get()
        }
        
        # Update in dictionary
        self.characters[self.current_character_id] = char_data
        
        # Update listbox to reflect name change
        self._update_character_list()
        
        # Select the current character in the listbox
        current_index = list(self.characters.keys()).index(self.current_character_id)
        self.character_listbox.selection_clear(0, tk.END)
        self.character_listbox.selection_set(current_index)
        
        # Save characters
        if self.save_characters():
            messagebox.showinfo("Success", f"{name} has been saved.")
    
    def _export_to_hexforge(self):
        """Export character data in a format compatible with PyHexForge"""
        if not self.characters:
            messagebox.showwarning("Warning", "No characters to export.")
            return
        
        # Create the export structure
        export_data = {
            "characters": self.characters
        }
        
        # Get export path
        export_path = filedialog.asksaveasfilename(
            title="Export Characters to PyHexForge",
            initialdir=self.script_dir,
            initialfile="pyhexforge_characters.json",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if not export_path:
            return  # User cancelled
        
        # Save export file
        try:
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=4)
            messagebox.showinfo("Success", f"Characters exported successfully to {export_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not export characters: {e}")
    
    def _browse_sprite(self):
        """Browse for a character sprite image"""
        filepath = filedialog.askopenfilename(
            title="Select Character Sprite",
            initialdir=self.script_dir,
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            # Make path relative to script dir if possible
            try:
                rel_path = os.path.relpath(filepath, self.script_dir)
                self.sprite_path_var.set(rel_path)
            except ValueError:
                self.sprite_path_var.set(filepath)  # Use absolute path
            
            self._update_preview()
    
    def _clear_sprite(self):
        """Clear the sprite selection"""
        self.sprite_path_var.set("")
        self._update_preview()
    
    def _update_preview(self):
        """Update the character preview image"""
        sprite_path = self.sprite_path_var.get()
        if sprite_path:
            try:
                # Make absolute path if needed
                if not os.path.isabs(sprite_path):
                    sprite_path = os.path.join(self.script_dir, sprite_path)
                
                if os.path.exists(sprite_path):
                    # Load and resize the image
                    img = Image.open(sprite_path)
                    img.thumbnail((100, 100))  # Resize to fit in preview area
                    
                    # Create PhotoImage and keep reference
                    self.preview_image = ImageTk.PhotoImage(img)
                    self.preview_label.config(image=self.preview_image)
                else:
                    self.preview_label.config(image="", text="Image not found")
            except Exception as e:
                print(f"Error loading image: {e}")
                self.preview_label.config(image="", text=f"Error: {e}")
        else:
            self.preview_label.config(image="", text="No sprite selected")
    
    def _clear_form(self):
        """Clear all form fields"""
        self.name_var.set("")
        self.class_var.set("")
        self.hp_var.set(100)
        self.attack_var.set(10)
        self.defense_var.set(8)
        self.speed_var.set(6)
        self.q_var.set(0)
        self.r_var.set(0)
        self.sprite_path_var.set("")
        self.preview_label.config(image="", text="")
    
    def _disable_form(self):
        """Disable all form fields"""
        # Get the right panel that contains the form
        for main_frame in self.root.winfo_children():
            if isinstance(main_frame, ttk.Frame):
                # Find the right panel in the main frame
                for panel in main_frame.winfo_children():
                    if isinstance(panel, ttk.LabelFrame) and panel.cget("text") == "Character Details":
                        # Disable all widgets in the right panel 
                        self._set_widget_state(panel, tk.DISABLED)
                        return
    
    def _enable_form(self):
        """Enable all form fields"""
        # Get the right panel that contains the form
        for main_frame in self.root.winfo_children():
            if isinstance(main_frame, ttk.Frame):
                # Find the right panel in the main frame
                for panel in main_frame.winfo_children():
                    if isinstance(panel, ttk.LabelFrame) and panel.cget("text") == "Character Details":
                        # Enable all widgets in the right panel
                        self._set_widget_state(panel, tk.NORMAL)
                        return
    
    def _set_widget_state(self, widget, state):
        """Set state of a widget and its children recursively"""
        try:
            widget.configure(state=state)
        except tk.TclError:
            # Not all widgets have state
            pass
        
        # Process children
        for child in widget.winfo_children():
            self._set_widget_state(child, state)


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = CharacterForge(root)
    root.mainloop()