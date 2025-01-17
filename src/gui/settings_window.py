import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from dotenv import load_dotenv, set_key
from pathlib import Path

class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Settings")
        self.window.geometry("600x700")
        
        # Load current settings
        self.load_env_variables()
        
        # Create and configure styles
        style = ttk.Style(self.window)
        
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # API Keys Section
        api_frame = ttk.LabelFrame(main_frame, text="API Keys", padding="10")
        api_frame.pack(fill="x", pady=5)
        
        # OpenAI API Key with show button
        ttk.Label(api_frame, text="OpenAI API Key:").pack(anchor="w")
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill="x", pady=2)
        self.openai_key = tk.StringVar(value="*" * 30 if self.openai_api_key else "")
        self.openai_entry = ttk.Entry(key_frame, textvariable=self.openai_key, width=50)
        self.openai_entry.pack(side="left", fill="x", expand=True)
        self.openai_show_btn = ttk.Button(key_frame, text="Show", width=8, 
                                        command=lambda: self.toggle_show_key(self.openai_key, self.openai_api_key, self.openai_show_btn))
        self.openai_show_btn.pack(side="left", padx=(5, 0))
        self.openai_entry.bind('<FocusIn>', lambda e: self.clear_field(self.openai_key))
        self.openai_entry.bind('<FocusOut>', lambda e: self.mask_field(self.openai_key, self.openai_api_key))
        
        # HuggingFace API Key with show button
        ttk.Label(api_frame, text="HuggingFace API Key:").pack(anchor="w")
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill="x", pady=2)
        self.huggingface_key = tk.StringVar(value="*" * 30 if self.huggingface_api_key else "")
        self.huggingface_entry = ttk.Entry(key_frame, textvariable=self.huggingface_key, width=50)
        self.huggingface_entry.pack(side="left", fill="x", expand=True)
        self.huggingface_show_btn = ttk.Button(key_frame, text="Show", width=8,
                                             command=lambda: self.toggle_show_key(self.huggingface_key, self.huggingface_api_key, self.huggingface_show_btn))
        self.huggingface_show_btn.pack(side="left", padx=(5, 0))
        self.huggingface_entry.bind('<FocusIn>', lambda e: self.clear_field(self.huggingface_key))
        self.huggingface_entry.bind('<FocusOut>', lambda e: self.mask_field(self.huggingface_key, self.huggingface_api_key))
        
        # Translation Method Section
        translation_frame = ttk.LabelFrame(main_frame, text="Translation Settings", padding="10")
        translation_frame.pack(fill="x", pady=5)
        
        # Translation Method
        ttk.Label(translation_frame, text="Translation Method:").pack(anchor="w")
        self.translation_method = tk.StringVar(value=parent.translation_method.get())
        ttk.Radiobutton(translation_frame, text="OpenAI", variable=self.translation_method, 
                       value="OpenAI").pack(anchor="w")
        ttk.Radiobutton(translation_frame, text="Google", variable=self.translation_method, 
                       value="Google").pack(anchor="w")
        ttk.Radiobutton(translation_frame, text="HuggingFace", variable=self.translation_method, 
                       value="HuggingFace").pack(anchor="w")
        
        # Mapping Method Section
        mapping_frame = ttk.LabelFrame(main_frame, text="Mapping Settings", padding="10")
        mapping_frame.pack(fill="x", pady=5)
        
        # Mapping Method
        ttk.Label(mapping_frame, text="Mapping Method:").pack(anchor="w")
        self.mapping_method = tk.StringVar(value="OpenAI")
        ttk.Radiobutton(mapping_frame, text="OpenAI", variable=self.mapping_method, 
                       value="OpenAI").pack(anchor="w")
        ttk.Radiobutton(mapping_frame, text="HuggingFace", variable=self.mapping_method, 
                       value="HuggingFace").pack(anchor="w")
        
        # Save Button
        ttk.Button(main_frame, text="Save Settings", 
                  command=self.save_settings, style='Blue.TButton').pack(pady=20)

    def load_env_variables(self):
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.huggingface_api_key = os.getenv("HUGGINGFACE", "")

    def clear_field(self, string_var):
        """Clear the field when it gains focus if it contains masked content"""
        if string_var.get().startswith('*'):
            string_var.set('')

    def mask_field(self, string_var, original_value):
        """Mask the field when it loses focus, unless new content was entered"""
        current = string_var.get()
        if not current or current.startswith('*'):
            string_var.set('*' * 30 if original_value else '')
        else:
            # Update the stored original value
            if string_var == self.openai_key:
                self.openai_api_key = current
            else:
                self.huggingface_api_key = current

    def toggle_show_key(self, string_var, api_key, button):
        """Toggle between showing the actual API key and masked version"""
        if button["text"] == "Show":
            if api_key:  # Only show if there's an actual key
                string_var.set(api_key)
            button["text"] = "Hide"
        else:
            string_var.set("*" * 30 if api_key else "")
            button["text"] = "Show"

    def save_settings(self):
        # Update .env file with actual values, not masked ones
        env_path = Path('.env')
        env_path.touch(exist_ok=True)
        
        # Only save if the user has entered a new value (not masked)
        if not self.openai_key.get().startswith('*'):
            set_key(env_path, "OPENAI_API_KEY", self.openai_key.get())
        if not self.huggingface_key.get().startswith('*'):
            set_key(env_path, "HUGGINGFACE", self.huggingface_key.get())
        
        # Update parent's translation and mapping methods
        self.parent.translation_method.set(self.translation_method.get())
        self.parent.mapping_method.set(self.mapping_method.get())
        
        # Save all GUI settings immediately using parent's save method
        self.parent.save_gui_config()
        
        messagebox.showinfo("Success", "Settings saved successfully!")
        self.window.destroy()