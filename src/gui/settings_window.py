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
    "o3-mini",
    "whisper-1"
    "text-embedding-3-large",
    "text-embedding-3-small"
]

# DeepSeek models list
DEEPSEEK_MODELS = [
    "deepseek-chat",
    "deepseek-reasoner"
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
        
        # Determine which translation model and API URL to use based on method
        translation_model = ""
        translation_api_url = ""
        if self.translation_method.get() == "OpenAI":
            translation_model = self.openai_translation_model_dropdown.get()
        elif self.translation_method.get() == "LMStudio":
            translation_model = self.lmstudio_translation_model.get()
            translation_api_url = self.translation_lmstudio_server.get()
        elif self.translation_method.get() == "HuggingFace":
            translation_api_url = self.translation_huggingface_url.get()
        elif self.translation_method.get() == "DeepSeek":
            translation_model = self.deepseek_translation_model_dropdown.get()

        # Determine which mapping model and API URL to use based on method
        mapping_model = ""
        mapping_api_url = ""
        if self.mapping_method.get() == "OpenAI":
            mapping_model = self.openai_mapping_model_dropdown.get()
        elif self.mapping_method.get() == "LMStudio":
            mapping_model = self.lmstudio_mapping_model.get()
            mapping_api_url = self.mapping_lmstudio_server.get()
        elif self.mapping_method.get() == "HuggingFace":
            mapping_api_url = self.mapping_huggingface_url.get()
        elif self.mapping_method.get() == "DeepSeek":
            mapping_model = self.deepseek_mapping_model_dropdown.get()
        
        # Save settings to config
        config = {
            "translation_method": self.translation_method.get(),
            "mapping_method": self.mapping_method.get(),
            "translation_model": translation_model,
            "translation_api_url": translation_api_url,
            "mapping_model": mapping_model,
            "mapping_api_url": mapping_api_url
        }
        
        # Update parent's config
        self.parent.update_config(config)
        
        # Update parent's translation and mapping methods
        #self.parent.translation_method.set(self.translation_method.get())
        #self.parent.mapping_method.set(self.mapping_method.get())
        
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
        
        # Initialize translation model variables for each service
        self.openai_translation_model = tk.StringVar(value=self.parent.get_config_value("translation_model", "gpt-4"))
        self.lmstudio_translation_model = tk.StringVar(value=self.parent.get_config_value("translation_model", "llama-3.2-3b-instruct"))
        self.deepseek_translation_model = tk.StringVar(value=self.parent.get_config_value("translation_model", "ds_V3"))
        
        # Initialize mapping model variables for each service
        self.openai_mapping_model = tk.StringVar(value=self.parent.get_config_value("mapping_model", "gpt-4"))
        self.lmstudio_mapping_model = tk.StringVar(value=self.parent.get_config_value("mapping_model", "llama-3.2-3b-instruct"))
        self.deepseek_mapping_model = tk.StringVar(value=self.parent.get_config_value("mapping_model", "ds_V3"))
        
        # Initialize API URLs for different services
        self.translation_lmstudio_server = tk.StringVar(value=self.parent.get_config_value("translation_api_url", "http://localhost:1234"))
        self.mapping_lmstudio_server = tk.StringVar(value=self.parent.get_config_value("mapping_api_url", "http://localhost:1234"))
        
        self.translation_huggingface_url = tk.StringVar(value=self.parent.get_config_value(
            "translation_api_url", 
            "https://api-inference.huggingface.co/models/meta-llama/Llama-2-13b-chat-hf"
        ))
        self.mapping_huggingface_url = tk.StringVar(value=self.parent.get_config_value(
            "mapping_api_url", 
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
        
        ''' TRANSLATION SETTINGS '''
        # Method-specific Translation Settings
        self.translation_settings_frame = ttk.LabelFrame(self.main_frame, text="Method-Specific Translation Settings", 
                                               padding="5", style='Small.TLabelframe')
        self.translation_settings_frame.pack(fill="x", pady=5)
        
        # OpenAI Translation Settings
        self.openai_translation_frame = ttk.Frame(self.translation_settings_frame)
        ttk.Label(self.openai_translation_frame, text="Model:", style='Small.TLabel').pack(side="left")
        self.openai_translation_model_dropdown = ttk.Combobox(
            self.openai_translation_frame, 
            textvariable=self.openai_translation_model,
            values=OPENAI_MODELS,
            state="readonly",
            width=25,
            style='Small.TCombobox'
        )
        self.openai_translation_model_dropdown.pack(side="left", padx=5)
        self.openai_translation_frame.pack(fill="x", pady=5)
        
        # Google Translation Settings
        self.google_translation_frame = ttk.Frame(self.translation_settings_frame)
        ttk.Label(self.google_translation_frame, text="No additional settings required", 
                  style='Small.TLabel').pack(pady=5)
        
        # HuggingFace Translation Settings
        self.huggingface_translation_frame = ttk.Frame(self.translation_settings_frame)
        ttk.Label(self.huggingface_translation_frame, text="API URL:", style='Small.TLabel').pack(anchor="w")
        ttk.Entry(self.huggingface_translation_frame, textvariable=self.translation_huggingface_url, 
                  width=50).pack(fill="x", pady=2)
        
        # LMStudio Translation Settings
        self.lmstudio_translation_frame = ttk.Frame(self.translation_settings_frame)
        ttk.Label(self.lmstudio_translation_frame, text="Server URL:", style='Small.TLabel').pack(anchor="w")
        ttk.Entry(self.lmstudio_translation_frame, textvariable=self.translation_lmstudio_server, width=50).pack(fill="x", pady=2)
        ttk.Label(self.lmstudio_translation_frame, text="Model:", style='Small.TLabel').pack(anchor="w")
        ttk.Entry(self.lmstudio_translation_frame, textvariable=self.lmstudio_translation_model, width=50).pack(fill="x", pady=2)

        
        # DeepSeek Translation Settings
        self.deepseek_translation_frame = ttk.Frame(self.translation_settings_frame)
        ttk.Label(self.deepseek_translation_frame, text="Model:", style='Small.TLabel').pack(side="left")
        self.deepseek_translation_model_dropdown = ttk.Combobox(
            self.deepseek_translation_frame, 
            textvariable=self.deepseek_translation_model,
            values=DEEPSEEK_MODELS,
            state="readonly",
            width=25,
            style='Small.TCombobox'
        )
        self.deepseek_translation_model_dropdown.pack(side="left", padx=5)
        self.deepseek_translation_frame.pack(fill="x", pady=5)

        

        # Update visibility based on translation method
        def update_translation_settings_visibility(*args):
            # Hide all frames
            for frame in [self.openai_translation_frame, self.google_translation_frame, 
                         self.huggingface_translation_frame, self.lmstudio_translation_frame,
                         self.deepseek_translation_frame]:
                frame.pack_forget()
            
            # Show the appropriate frame based on selected method
            translation_method = self.translation_method.get()
            if translation_method == "OpenAI":
                self.openai_translation_frame.pack(fill="x", pady=5)
            elif translation_method == "Google":
                self.google_translation_frame.pack(fill="x", pady=5)
            elif translation_method == "HuggingFace":
                self.huggingface_translation_frame.pack(fill="x", pady=5)
            elif translation_method == "LMStudio":
                self.lmstudio_translation_frame.pack(fill="x", pady=5)
            elif translation_method == "DeepSeek":
                self.deepseek_translation_frame.pack(fill="x", pady=5)
        
        # Bind the update function to translation method changes
        self.translation_method.trace_add('write', update_translation_settings_visibility)
        # Initial visibility check
        update_translation_settings_visibility()
        
        ''' MAPPING SETTINGS '''
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
        
      
             # Create mapping model frame
        self.mapping_model_settings_frame = ttk.LabelFrame(self.main_frame, text="Method-Specific Mapping Settings", 
                                                padding="5", style='Small.TLabelframe')
        self.mapping_model_settings_frame.pack(fill="x", pady=5)
        
        # LMStudio Settings Section
        self.lmstudio_frame = ttk.LabelFrame(self.mapping_model_settings_frame, text="Settings for LMStudio", padding="10")
        self.lmstudio_frame.pack(fill="x", pady=5)
        
        # Local Server Address
        ttk.Label(self.lmstudio_frame, text="Local Server Address:").pack(anchor="w")
        self.lmstudio_server = tk.StringVar(value=self.parent.get_config_value("lmstudio_server", "http://localhost:1234"))
        server_entry = ttk.Entry(self.lmstudio_frame, textvariable=self.lmstudio_server, width=50)
        server_entry.pack(fill="x", pady=2)
        
        # Model API Identifier
        ttk.Label(self.lmstudio_frame, text="Model API Identifier:").pack(anchor="w")
        self.lmstudio_mapping_model = tk.StringVar(value=self.parent.get_config_value("mapping_model", "llama-3.2-3b-instruct"))  # Changed key name
        model_entry = ttk.Entry(self.lmstudio_frame, textvariable=self.lmstudio_mapping_model, width=50)
        model_entry.pack(fill="x", pady=2)

        
        # DeepSeek Mapping Settings
        self.deepseek_mapping_frame = ttk.Frame(self.mapping_model_settings_frame)
        ttk.Label(self.deepseek_mapping_frame, text="Model:", style='Small.TLabel').pack(side="left")
        self.deepseek_mapping_model_dropdown = ttk.Combobox(
            self.deepseek_mapping_frame, 
            textvariable=self.deepseek_mapping_model,
            values=DEEPSEEK_MODELS,
            state="readonly",
            width=25,
            style='Small.TCombobox'
        )
        self.deepseek_mapping_model_dropdown.pack(side="left", padx=5)
        self.deepseek_mapping_frame.pack(fill="x", pady=5)
        
        # OpenAI Mapping Settings
        self.openai_mapping_frame = ttk.Frame(self.mapping_model_settings_frame)
        ttk.Label(self.openai_mapping_frame, text="Model:", style='Small.TLabel').pack(side="left")
        self.openai_mapping_model_dropdown = ttk.Combobox(
            self.openai_mapping_frame, 
            textvariable=self.openai_mapping_model,
            values=OPENAI_MODELS,
            state="readonly",
            width=25,
            style='Small.TCombobox'
        )
        self.openai_mapping_model_dropdown.pack(side="left", padx=5)
        self.openai_mapping_frame.pack(fill="x", pady=5)
        

        # HuggingFace Settings Section
        self.huggingface_frame = ttk.LabelFrame(self.mapping_model_settings_frame, text="Settings for HuggingFace", 
                                               padding="5", style='Small.TLabelframe')
        self.huggingface_frame.pack(fill="x", pady=5)
        
        # HuggingFace API URL
        ttk.Label(self.huggingface_frame, text="API URL:", 
                  style='Small.TLabel').pack(anchor="w")
        ttk.Entry(self.huggingface_frame, textvariable=self.mapping_huggingface_url, 
                  width=50).pack(fill="x", pady=2)


        # Update visibility based on mapping method
        def update_mapping_settings_visibility(*args):
            # Hide all frames first
            self.openai_mapping_frame.pack_forget()
            self.lmstudio_frame.pack_forget()
            self.huggingface_frame.pack_forget()
            self.deepseek_mapping_frame.pack_forget()

            mapping_method = self.mapping_method.get()
            if mapping_method == "OpenAI":
                self.openai_mapping_frame.pack(fill="x", pady=5)
            elif mapping_method == "DeepSeek":
                self.deepseek_mapping_frame.pack(fill="x", pady=5)
            elif mapping_method == "LMStudio":
                self.lmstudio_frame.pack(fill="x", pady=5)
            elif mapping_method == "HuggingFace":
                self.huggingface_frame.pack(fill="x", pady=5)

        self.mapping_method.trace_add('write', update_mapping_settings_visibility)
        # Initial visibility check
        update_mapping_settings_visibility()    
        

               
        # Save Button
        ttk.Button(self.main_frame, text="Save Settings", 
                  command=self.save_settings, 
                  style='Blue.TButton').pack(pady=(5, 10))

        def on_closing():
            self.canvas.unbind_all("<MouseWheel>")  # Remove mousewheel binding
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)