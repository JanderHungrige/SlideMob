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
        self.parent = parent
        self.window = tk.Toplevel(root)
        self.window.title("Settings")
        self.window.geometry("600x400")  # Set a fixed size for the window
        
        # Load current settings
        self.load_env_variables()
        
        # Create and configure styles
        style = ttk.Style(self.window)
        create_custom_styles(style)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        
        # Create main frame that will be scrolled
        main_frame = ttk.Frame(canvas, padding="10")
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Create window in canvas for main frame
        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw", width=canvas.winfo_width())
        
        # Update canvas scroll region when main frame size changes
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Update canvas window size when canvas size changes
        def configure_window_size(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        # Bind events
        main_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_window_size)
        
        # Enable mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
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
        translation_frame = ttk.LabelFrame(main_frame, text="Translation Settings", 
                                         padding="5", style='Small.TLabelframe')
        translation_frame.pack(fill="x", pady=5)
        
        # Translation Method
        ttk.Label(translation_frame, text="Translation Method:").pack(anchor="w")
        self.translation_method = tk.StringVar(value=parent.translation_method.get())
        for method in ["OpenAI", "Google", "HuggingFace", "LMStudio"]:
            method_frame = ttk.Frame(translation_frame)
            method_frame.pack(anchor="w", fill="x", pady=1)  # Reduced padding
            
            ttk.Radiobutton(method_frame, text=method, variable=self.translation_method, 
                           value=method, style='Small.TRadiobutton').pack(side="left")
        
        # OpenAI Model Selection Frame
        self.openai_model_frame = ttk.Frame(translation_frame)
        self.openai_model_frame.pack(fill="x", pady=5)
        ttk.Label(self.openai_model_frame, text="Model:", style='Small.TLabel').pack(side="left")
        self.openai_model = tk.StringVar(value=parent.get_config_value("openai_model", "gpt-4"))
        self.openai_model_dropdown = ttk.Combobox(
            self.openai_model_frame, 
            textvariable=self.openai_model,
            values=OPENAI_MODELS,
            state="readonly",
            width=25,  # Slightly smaller width
            style='Small.TCombobox'
        )
        self.openai_model_dropdown.pack(side="left", padx=5)
        
        # Update visibility based on translation method
        def update_model_visibility(*args):
            if self.translation_method.get() == "OpenAI":
                self.openai_model_frame.pack(fill="x", pady=5)
            else:
                self.openai_model_frame.pack_forget()
        
        self.translation_method.trace_add('write', update_model_visibility)
        # Initial visibility check
        update_model_visibility()
        
        # Mapping Method Section
        mapping_frame = ttk.LabelFrame(main_frame, text="Mapping Settings", padding="5", style='Small.TLabelframe')
        mapping_frame.pack(fill="x", pady=5)
        
        # Mapping Method - Initialize with parent's value
        ttk.Label(mapping_frame, text="Mapping Method:").pack(anchor="w")
        self.mapping_method = tk.StringVar(value=parent.mapping_method.get())  # Get from parent
        for method in ["OpenAI", "HuggingFace", "LMStudio"]:
            method_frame = ttk.Frame(mapping_frame)
            method_frame.pack(anchor="w", fill="x", pady=1)
            
            ttk.Radiobutton(method_frame, text=method, variable=self.mapping_method, 
                           value=method, style='Small.TRadiobutton').pack(side="left")
        
        # Mapping Model Selection Frame
        self.mapping_model_frame = ttk.Frame(mapping_frame)
        self.mapping_model_frame.pack(fill="x", pady=5)
        ttk.Label(self.mapping_model_frame, text="Model:", style='Small.TLabel').pack(side="left")
        self.mapping_model = tk.StringVar(value=parent.get_config_value("mapping_model", "gpt-4"))
        self.mapping_model_dropdown = ttk.Combobox(
            self.mapping_model_frame, 
            textvariable=self.mapping_model,
            values=OPENAI_MODELS,
            state="readonly",
            width=25,
            style='Small.TCombobox'
        )
        self.mapping_model_dropdown.pack(side="left", padx=5)
        
        # Translation Method - Initialize with parent's value
        self.translation_method = tk.StringVar(value=parent.translation_method.get())  # Get from parent
        
        # LMStudio Settings Section
        lmstudio_frame = ttk.LabelFrame(main_frame, text="Settings for LMStudio", padding="10")
        lmstudio_frame.pack(fill="x", pady=5)
        
        # Local Server Address
        ttk.Label(lmstudio_frame, text="Local Server Address:").pack(anchor="w")
        self.lmstudio_server = tk.StringVar(value=parent.get_config_value("lmstudio_server", "http://localhost:1234"))
        server_entry = ttk.Entry(lmstudio_frame, textvariable=self.lmstudio_server, width=50)
        server_entry.pack(fill="x", pady=2)
        
        # Model API Identifier
        ttk.Label(lmstudio_frame, text="Model API Identifier:").pack(anchor="w")
        self.lmstudio_model = tk.StringVar(value=parent.get_config_value("lmstudio_model_api", ""))  # Changed key name
        model_entry = ttk.Entry(lmstudio_frame, textvariable=self.lmstudio_model, width=50)
        model_entry.pack(fill="x", pady=2)
        
        # Update visibility based on mapping method
        def update_visibility(*args):
            if self.mapping_method.get() == "OpenAI":
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
        self.huggingface_frame = ttk.LabelFrame(main_frame, text="Settings for HuggingFace", 
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
        ttk.Button(main_frame, text="Save Settings", 
                  command=self.save_settings, 
                  style='Blue.TButton').pack(pady=(5, 10))

        def on_closing():
            canvas.unbind_all("<MouseWheel>")  # Remove mousewheel binding
            self.window.destroy()
        
        self.window.protocol("WM_DELETE_WINDOW", on_closing)

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
        
        # Save LMStudio settings to config
        config = {
            "lmstudio_server": self.lmstudio_server.get(),
            "lmstudio_model": self.lmstudio_model.get(),
            "translation_method": self.translation_method.get(),
            "mapping_method": self.mapping_method.get(),
            "openai_model": self.openai_model.get(),
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
        self.window.destroy()
        if not self.openai_key.get().startswith('*'):
            set_key(env_path, "OPENAI_API_KEY", self.openai_key.get())
        if not self.huggingface_key.get().startswith('*'):
            set_key(env_path, "HUGGINGFACE", self.huggingface_key.get())
        
        # Update parent's translation and mapping methods
        self.parent.translation_method.set(self.translation_method.get())
        self.parent.mapping_method.set(self.mapping_method.get())
        
        # Save all GUI settings immediately using parent's save method
        self.parent.save_gui_config()
        
        #messagebox.showinfo("Success", "Settings saved successfully!")
        self.window.destroy()