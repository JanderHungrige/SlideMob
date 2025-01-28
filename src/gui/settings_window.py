import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from dotenv import load_dotenv, set_key
from pathlib import Path

# OpenAI models list
OPENAI_MODELS = [
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "gpt-4",
    "gpt-4-0613",
    "gpt-4o",
    "gpt-4o-mini",
    "o1-preview",
    "o1",
    "o1-mini",
    "o3",
    "o3-mini"
]

# DeepSeek models list
DEEPSEEK_MODELS = [
    "ds_V3",
    "ds_R1"
]

# Create custom styles for smaller elements
def create_custom_styles(style):
    # Configure smaller font sizes
    style.configure('Small.TRadiobutton', 
                   font=('TkDefaultFont', 8),
                   indicatorsize=2,  # Reduced from 10 to 6
                   padding=(1, 0))   # Minimal padding
    
    style.configure('Small.TLabel', 
                   font=('TkDefaultFont', 8))
    
    style.configure('Small.TLabelframe.Label', 
                   font=('TkDefaultFont', 8))
    
    style.configure('Small.TLabelframe', 
                   padding=2)  # Reduced from 3
    
    style.configure('Small.TEntry', 
                   padding=1)
    
    style.configure('Small.TCombobox', 
                   padding=1,
                   font=('TkDefaultFont', 8))
    
    # Configure layout for tiny radio buttons
    style.layout('Small.TRadiobutton', [
        ('Radiobutton.padding', {'children':
            [('Radiobutton.indicator', {'side': 'left', 'sticky': ''}),
             ('Radiobutton.focus', {'children':
                 [('Radiobutton.label', {'sticky': 'nswe'})],
                 'side': 'left', 'sticky': ''})],
            'sticky': 'nswe'})])

class SettingsWindow:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.root.title("Settings")
        
        # Set window size and position
        window_width = 600
        window_height = 800
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position for center of screen
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        
        # Set window size and position
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        
        # Optional: Set minimum window size
        self.root.minsize(500, 600)
        
        # Create main container frame
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)
        
        # Create canvas with scrollbar
        self.canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        # Create main frame that will contain all widgets
        self.main_frame = ttk.Frame(self.canvas)
        
        # Configure scrolling for different platforms
        def _on_mousewheel(event):
            if event.num == 5 or event.delta < 0:  # Scroll down
                self.canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0:  # Scroll up
                self.canvas.yview_scroll(-1, "units")
        
        # Bind for Windows and MacOS
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # Bind for Linux
        self.canvas.bind_all("<Button-4>", _on_mousewheel)
        self.canvas.bind_all("<Button-5>", _on_mousewheel)
        
        # Configure the canvas
        self.main_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas for the frame
        self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the scrollbar first, then the canvas
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Load settings before creating widgets
        self.load_settings()
        
        # Create widgets in main_frame
        self.create_widgets()
        
        # Update idletasks to ensure proper initial layout
        self.root.update_idletasks()

    def load_env_variables(self):
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.huggingface_api_key = os.getenv("HUGGINGFACE", "")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")

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
            elif string_var == self.huggingface_key:
                self.huggingface_api_key = current
            elif string_var == self.deepseek_key:
                self.deepseek_api_key = current

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
        # Create .env file if it doesn't exist
        env_path = Path('.env')
        env_path.touch(exist_ok=True)
        
        # Only save if the user has entered a new value (not masked)
        if not self.openai_key.get().startswith('*'):
            set_key(env_path, "OPENAI_API_KEY", self.openai_key.get())
        if not self.huggingface_key.get().startswith('*'):
            set_key(env_path, "HUGGINGFACE", self.huggingface_key.get())
        if not self.deepseek_key.get().startswith('*'):
            set_key(env_path, "DEEPSEEK_API_KEY", self.deepseek_key.get())
        
        # Save settings to config
        config = {
            "lmstudio_server": self.lmstudio_server.get(),
            "translation_method": self.translation_method.get(),
            "mapping_method": self.mapping_method.get(),
            "translation_model": self.translation_model.get(),
            "mapping_model": self.mapping_model.get(),
            "huggingface_url": self.huggingface_url.get()
        }
        
        # Update parent's config
        self.parent.update_config(config)
        
        # Update parent's translation and mapping methods
        self.parent.translation_method.set(self.translation_method.get())
        self.parent.mapping_method.set(self.mapping_method.get())
        
        # Save all GUI settings immediately using parent's save method
        self.parent.save_gui_config()
        
        messagebox.showinfo("Success", "Settings saved successfully!")
        self.root.destroy()

    def load_settings(self):
        """Load settings from environment variables and config"""
        # Load API keys from environment
        self.load_env_variables()
        
        # Load other settings from parent's config
        self.translation_method = tk.StringVar(value=self.parent.translation_method.get())
        self.mapping_method = tk.StringVar(value=self.parent.mapping_method.get())
        self.translation_model = tk.StringVar(value=self.parent.get_config_value("translation_model", "gpt-4"))
        self.mapping_model = tk.StringVar(value=self.parent.get_config_value("mapping_model", "gpt-4"))
        self.lmstudio_server = tk.StringVar(value=self.parent.get_config_value("lmstudio_server", "http://localhost:1234"))
        self.huggingface_url = tk.StringVar(value=self.parent.get_config_value(
            "huggingface_url", 
            "https://api-inference.huggingface.co/models/meta-llama/Llama-2-13b-chat-hf"
        ))

    def create_widgets(self):
        # API Keys Section
        api_frame = ttk.LabelFrame(self.main_frame, text="API Keys", padding="10")
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
        
        # DeepSeek API Key with show button
        ttk.Label(api_frame, text="DeepSeek API Key:").pack(anchor="w")
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill="x", pady=2)
        self.deepseek_key = tk.StringVar(value="*" * 30 if self.deepseek_api_key else "")
        self.deepseek_entry = ttk.Entry(key_frame, textvariable=self.deepseek_key, width=50)
        self.deepseek_entry.pack(side="left", fill="x", expand=True)
        self.deepseek_show_btn = ttk.Button(key_frame, text="Show", width=8,
                                command=lambda: self.toggle_show_key(self.deepseek_key, self.deepseek_api_key, self.deepseek_show_btn))
        self.deepseek_show_btn.pack(side="left", padx=(5, 0))
        self.deepseek_entry.bind('<FocusIn>', lambda e: self.clear_field(self.deepseek_key))
        self.deepseek_entry.bind('<FocusOut>', lambda e: self.mask_field(self.deepseek_key, self.deepseek_api_key))
        
        # Translation Method Section
        translation_frame = ttk.LabelFrame(self.main_frame, text="Translation Settings", padding="5")
        translation_frame.pack(fill="x", pady=5)
        
        ttk.Label(translation_frame, text="Translation Method:").pack(anchor="w")
        for method in ["OpenAI", "Google", "HuggingFace", "LMStudio", "DeepSeek"]:
            ttk.Radiobutton(translation_frame, text=method, variable=self.translation_method, 
                           value=method).pack(anchor="w")
        
        # Method-specific Translation Settings
        self.translation_settings_frame = ttk.LabelFrame(self.main_frame, text="Method-Specific Translation Settings", 
                                               padding="5", style='Small.TLabelframe')
        self.translation_settings_frame.pack(fill="x", pady=5)
        
        # OpenAI Translation Settings
        self.openai_translation_frame = ttk.Frame(self.translation_settings_frame)
        ttk.Label(self.openai_translation_frame, text="Model:", style='Small.TLabel').pack(side="left")
        self.translation_model = tk.StringVar(value=self.parent.get_config_value("translation_model", "gpt-4"))
        self.translation_model_dropdown = ttk.Combobox(
            self.openai_translation_frame, 
            textvariable=self.translation_model,
            values=OPENAI_MODELS,
            state="readonly",
            width=25,
            style='Small.TCombobox'
        )
        self.translation_model_dropdown.pack(side="left", padx=5)
        
        # Google Translation Settings
        self.google_translation_frame = ttk.Frame(self.translation_settings_frame)
        ttk.Label(self.google_translation_frame, text="No additional settings required", 
                  style='Small.TLabel').pack(pady=5)
        
        # HuggingFace Translation Settings
        self.huggingface_translation_frame = ttk.Frame(self.translation_settings_frame)
        ttk.Label(self.huggingface_translation_frame, text="API URL:", style='Small.TLabel').pack(anchor="w")
        self.translation_huggingface_url = tk.StringVar(value=self.parent.get_config_value(
            "translation_huggingface_url", 
            "https://api-inference.huggingface.co/models/meta-llama/Llama-2-13b-chat-hf"
        ))
        ttk.Entry(self.huggingface_translation_frame, textvariable=self.translation_huggingface_url, 
                  width=50).pack(fill="x", pady=2)
        
        # LMStudio Translation Settings
        self.lmstudio_translation_frame = ttk.Frame(self.translation_settings_frame)
        ttk.Label(self.lmstudio_translation_frame, text="Server URL:", style='Small.TLabel').pack(anchor="w")
        self.translation_lmstudio_server = tk.StringVar(value=self.parent.get_config_value("translation_lmstudio_server", "http://localhost:1234"))
        ttk.Entry(self.lmstudio_translation_frame, textvariable=self.translation_lmstudio_server, width=50).pack(fill="x", pady=2)
        ttk.Label(self.lmstudio_translation_frame, text="Model:", style='Small.TLabel').pack(anchor="w")
        self.translation_model = tk.StringVar(value=self.parent.get_config_value("translation_model", "llama-3.2-3b-instruct"))
        ttk.Entry(self.lmstudio_translation_frame, textvariable=self.translation_model, width=50).pack(fill="x", pady=2)
        
        # DeepSeek Translation Settings
        self.deepseek_translation_frame = ttk.Frame(self.translation_settings_frame)
        ttk.Label(self.deepseek_translation_frame, text="Model:", style='Small.TLabel').pack(side="left")
        self.translation_model = tk.StringVar(value=self.parent.get_config_value("translation_model", "ds_V3"))
        self.translation_model_dropdown = ttk.Combobox(
            self.deepseek_translation_frame, 
            textvariable=self.translation_model,
            values=DEEPSEEK_MODELS,
            state="readonly",
            width=25,
            style='Small.TCombobox'
        )
        self.translation_model_dropdown.pack(side="left", padx=5)
        
        # Update visibility based on translation method
        def update_translation_settings_visibility(*args):
            # Hide all frames
            for frame in [self.openai_translation_frame, self.google_translation_frame, 
                         self.huggingface_translation_frame, self.lmstudio_translation_frame,
                         self.deepseek_translation_frame]:
                frame.pack_forget()
            
            # Show the appropriate frame based on selected method
            method = self.translation_method.get()
            if method == "OpenAI":
                self.openai_translation_frame.pack(fill="x", pady=5)
            elif method == "Google":
                self.google_translation_frame.pack(fill="x", pady=5)
            elif method == "HuggingFace":
                self.huggingface_translation_frame.pack(fill="x", pady=5)
            elif method == "LMStudio":
                self.lmstudio_translation_frame.pack(fill="x", pady=5)
            elif method == "DeepSeek":
                self.deepseek_translation_frame.pack(fill="x", pady=5)
        
        # Bind the update function to translation method changes
        self.translation_method.trace_add('write', update_translation_settings_visibility)
        # Initial visibility check
        update_translation_settings_visibility()
        
        # Mapping Method Section
        mapping_frame = ttk.LabelFrame(self.main_frame, text="Mapping Settings", padding="5", style='Small.TLabelframe')
        mapping_frame.pack(fill="x", pady=5)
        
        # Mapping Method - Initialize with parent's value
        ttk.Label(mapping_frame, text="Mapping Method:").pack(anchor="w")
        self.mapping_method = tk.StringVar(value=self.parent.mapping_method.get())  # Get from parent
        for method in ["OpenAI", "HuggingFace", "LMStudio", "DeepSeek"]:
            method_frame = ttk.Frame(mapping_frame)
            method_frame.pack(anchor="w", fill="x", pady=1)
            
            ttk.Radiobutton(method_frame, text=method, variable=self.mapping_method, 
                           value=method, style='Small.TRadiobutton').pack(side="left")
        
        # Mapping Model Selection Frame
        self.mapping_model_frame = ttk.Frame(mapping_frame)
        self.mapping_model_frame.pack(fill="x", pady=5)
        ttk.Label(self.mapping_model_frame, text="Model:", style='Small.TLabel').pack(side="left")
        self.mapping_model = tk.StringVar(value=self.parent.get_config_value("mapping_model", "gpt-4"))
        self.mapping_model_dropdown = ttk.Combobox(
            self.mapping_model_frame, 
            textvariable=self.mapping_model,
            values=OPENAI_MODELS,
            state="readonly",
            width=25,
            style='Small.TCombobox'
        )
        self.mapping_model_dropdown.pack(side="left", padx=5)
        
        # LMStudio Settings Section
        lmstudio_frame = ttk.LabelFrame(self.main_frame, text="Settings for LMStudio", padding="10")
        lmstudio_frame.pack(fill="x", pady=5)
        
        # Local Server Address
        ttk.Label(lmstudio_frame, text="Local Server Address:").pack(anchor="w")
        self.lmstudio_server = tk.StringVar(value=self.parent.get_config_value("lmstudio_server", "http://localhost:1234"))
        server_entry = ttk.Entry(lmstudio_frame, textvariable=self.lmstudio_server, width=50)
        server_entry.pack(fill="x", pady=2)
        
        # Model API Identifier
        ttk.Label(lmstudio_frame, text="Model API Identifier:").pack(anchor="w")
        self.mapping_model = tk.StringVar(value=self.parent.get_config_value("mapping_model", "llama-3.2-3b-instruct"))  # Changed key name
        model_entry = ttk.Entry(lmstudio_frame, textvariable=self.mapping_model, width=50)
        model_entry.pack(fill="x", pady=2)
        
        # Update visibility based on mapping method
        def update_visibility(*args):
            if self.mapping_method.get() == "OpenAI":
                self.mapping_model_dropdown['values'] = OPENAI_MODELS
                self.mapping_model_frame.pack(fill="x", pady=5)
                lmstudio_frame.pack_forget()
            elif self.mapping_method.get() == "DeepSeek":
                self.mapping_model_dropdown['values'] = DEEPSEEK_MODELS
                self.mapping_model_frame.pack(fill="x", pady=5)
                lmstudio_frame.pack_forget()
            elif self.mapping_method.get() == "LMStudio":
                self.mapping_model_frame.pack_forget()
                lmstudio_frame.pack(fill="x", pady=5)
            else:
                self.mapping_model_frame.pack_forget()
                lmstudio_frame.pack_forget()
        
        self.mapping_method.trace_add('write', update_visibility)
        # Initial visibility check
        update_visibility()
        
        # HuggingFace Settings Section
        self.huggingface_frame = ttk.LabelFrame(self.main_frame, text="Settings for HuggingFace", 
                                               padding="5", style='Small.TLabelframe')
        self.huggingface_frame.pack(fill="x", pady=5)
        
        # HuggingFace API URL
        ttk.Label(self.huggingface_frame, text="API URL:", 
                  style='Small.TLabel').pack(anchor="w")
        self.huggingface_url = tk.StringVar(value=self.parent.get_config_value(
            "huggingface_url", 
            "https://api-inference.huggingface.co/models/meta-llama/Llama-2-13b-chat-hf"
        ))
        ttk.Entry(self.huggingface_frame, textvariable=self.huggingface_url, 
                  width=50).pack(fill="x", pady=2)
        
        # Update visibility based on translation method
        def update_huggingface_visibility(*args):
            if self.translation_method.get() == "HuggingFace" or self.mapping_method.get() == "HuggingFace":
                self.huggingface_frame.pack(fill="x", pady=5)
            else:
                self.huggingface_frame.pack_forget()
        
        self.translation_method.trace_add('write', update_huggingface_visibility)
        self.mapping_method.trace_add('write', update_huggingface_visibility)
        # Initial visibility check
        update_huggingface_visibility()
        
        # Save Button - now placed after HuggingFace frame
        ttk.Button(self.main_frame, text="Save Settings", 
                  command=self.save_settings, 
                  style='Blue.TButton').pack(pady=(5, 10))

        def on_closing():
            self.canvas.unbind_all("<MouseWheel>")  # Remove mousewheel binding
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)