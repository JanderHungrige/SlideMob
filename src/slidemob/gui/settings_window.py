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
    "whisper-1" "text-embedding-3-large",
    "text-embedding-3-small",
]

# DeepSeek models list
DEEPSEEK_MODELS = ["deepseek-chat", "deepseek-reasoner"]

# Add Azure OpenAI models and configuration
AZURE_OPENAI_MODELS = ["gpt-35-turbo", "gpt-4", "gpt-4-32k"]

# Add Azure configuration
AZURE_CONFIG = {
    "api_version": "2024-02-15-preview",
    "temperature": 0.7,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "max_tokens_out": 1000,
}

# Create custom styles for smaller elements
def create_custom_styles(style):
    # Configure smaller font sizes
    style.configure(
        "Small.TRadiobutton",
        font=("TkDefaultFont", 8),
        indicatorsize=2,  # Reduced from 10 to 6
        padding=(1, 0),
    )  # Minimal padding

    style.configure("Small.TLabel", font=("TkDefaultFont", 8))

    style.configure("Small.TLabelframe.Label", font=("TkDefaultFont", 8))

    style.configure("Small.TLabelframe", padding=2)  # Reduced from 3

    style.configure("Small.TEntry", padding=1)

    style.configure("Small.TCombobox", padding=1, font=("TkDefaultFont", 8))

    # Configure layout for tiny radio buttons
    style.layout(
        "Small.TRadiobutton",
        [
            (
                "Radiobutton.padding",
                {
                    "children": [
                        ("Radiobutton.indicator", {"side": "left", "sticky": ""}),
                        (
                            "Radiobutton.focus",
                            {
                                "children": [("Radiobutton.label", {"sticky": "nswe"})],
                                "side": "left",
                                "sticky": "",
                            },
                        ),
                    ],
                    "sticky": "nswe",
                },
            )
        ],
    )


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

        # Load settings before creating widgets
        self.load_settings()

        # Create widgets
        self.create_widgets()

        # Update idletasks to ensure proper initial layout
        self.root.update_idletasks()

    def load_env_variables(self):
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.huggingface_api_key = os.getenv("HUGGINGFACE", "")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.azure_api_key = os.getenv("AZURE_OPENAI_ENDPOINT_KEY", "")

    def clear_field(self, string_var):
        """Clear the field when it gains focus if it contains masked content"""
        if string_var.get().startswith("*"):
            string_var.set("")

    def mask_field(self, string_var, original_value):
        """Mask the field when it loses focus, unless new content was entered"""
        current = string_var.get()
        if not current or current.startswith("*"):
            string_var.set("*" * 30 if original_value else "")
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
        env_path = Path(".env")
        env_path.touch(exist_ok=True)

        # Save API keys if changed
        if not self.openai_key.get().startswith("*"):
            set_key(env_path, "OPENAI_API_KEY", self.openai_key.get())
        if not self.huggingface_key.get().startswith("*"):
            set_key(env_path, "HUGGINGFACE", self.huggingface_key.get())
        if not self.deepseek_key.get().startswith("*"):
            set_key(env_path, "DEEPSEEK_API_KEY", self.deepseek_key.get())
        if not self.azure_key.get().startswith("*"):
            set_key(env_path, "AZURE_OPENAI_ENDPOINT_KEY", self.azure_key.get())
        set_key(env_path, "AZURE_OPENAI_ENDPOINT", self.azure_endpoint.get())

        # Initialize variables
        translation_model = ""
        translation_api_url = ""
        mapping_model = ""
        mapping_api_url = ""
        azure_translation_config = None
        azure_mapping_config = None

        # Get translation settings based on method
        if self.translation_method.get() == "OpenAI":
            translation_model = self.openai_translation_model.get()
        elif self.translation_method.get() == "LMStudio":
            translation_model = self.lmstudio_translation_model.get()
            translation_api_url = self.translation_lmstudio_server.get()
        elif self.translation_method.get() == "HuggingFace":
            translation_api_url = self.translation_huggingface_url.get()
        elif self.translation_method.get() == "DeepSeek":
            translation_model = self.deepseek_translation_model.get()
        elif self.translation_method.get() == "Azure OpenAI":
            translation_model = self.azure_translation_model.get()
            translation_api_url = self.azure_endpoint.get()
            azure_translation_config = {
                "temperature": self.translation_temperature.get(),
                "frequency_penalty": self.translation_frequency_penalty.get(),
                "presence_penalty": self.translation_presence_penalty.get(),
                "max_tokens_out": self.translation_max_tokens.get(),
            }

        # Get mapping settings based on method
        if self.mapping_method.get() == "OpenAI":
            mapping_model = self.openai_mapping_model.get()
        elif self.mapping_method.get() == "LMStudio":
            mapping_model = self.lmstudio_mapping_model.get()
            mapping_api_url = self.mapping_lmstudio_server.get()
        elif self.mapping_method.get() == "HuggingFace":
            mapping_api_url = self.mapping_huggingface_url.get()
        elif self.mapping_method.get() == "DeepSeek":
            mapping_model = self.deepseek_mapping_model.get()
        elif self.mapping_method.get() == "Azure OpenAI":
            mapping_model = self.azure_mapping_model.get()
            mapping_api_url = self.azure_mapping_endpoint.get()
            azure_mapping_config = {
                "temperature": self.mapping_temperature.get(),
                "frequency_penalty": self.mapping_frequency_penalty.get(),
                "presence_penalty": self.mapping_presence_penalty.get(),
                "max_tokens_out": self.mapping_max_tokens.get(),
            }

        # Create config dictionary with all settings
        config = {
            "translation_method": self.translation_method.get(),
            "mapping_method": self.mapping_method.get(),
            "translation_model": translation_model,
            "translation_api_url": translation_api_url,
            "mapping_model": mapping_model,
            "mapping_api_url": mapping_api_url,
            "azure_translation_config": azure_translation_config,
            "azure_mapping_config": azure_mapping_config,
        }

        # Update parent's config
        self.parent.update_config(config)

        # Save all GUI settings
        self.parent.save_gui_config(save_all=True)

        messagebox.showinfo("Success", "Settings saved successfully!")
        self.root.destroy()

    def load_settings(self):
        """Load settings from environment variables and config"""
        # Load API keys from environment
        self.load_env_variables()

        # Load other settings from parent's config
        self.translation_method = tk.StringVar(
            value=self.parent.translation_method.get()
        )
        self.mapping_method = tk.StringVar(value=self.parent.mapping_method.get())

        # Initialize translation model variables for each service
        self.openai_translation_model = tk.StringVar(
            value=self.parent.translation_model
        )
        self.lmstudio_translation_model = tk.StringVar(
            value=self.parent.translation_model
        )
        self.deepseek_translation_model = tk.StringVar(
            value=self.parent.translation_model
        )
        self.azure_translation_model = tk.StringVar(value=self.parent.translation_model)

        # Initialize mapping model variables for each service
        self.openai_mapping_model = tk.StringVar(value=self.parent.mapping_model)
        self.lmstudio_mapping_model = tk.StringVar(value=self.parent.mapping_model)
        self.deepseek_mapping_model = tk.StringVar(value=self.parent.mapping_model)

        # Initialize API URLs for different services
        self.translation_lmstudio_server = tk.StringVar(
            value=self.parent.translation_api_url
        )
        self.mapping_lmstudio_server = tk.StringVar(value=self.parent.mapping_api_url)

        # Load HuggingFace URLs from parent's config
        self.translation_huggingface_url = tk.StringVar(
            value=self.parent.translation_api_url
        )
        self.mapping_huggingface_url = tk.StringVar(value=self.parent.mapping_api_url)
        self.azure_endpoint = tk.StringVar(value=self.parent.translation_api_url)

        # Add this line around line 287, after the other model initializations:
        self.azure_mapping_model = tk.StringVar(value=self.parent.mapping_model)
        self.azure_mapping_endpoint = tk.StringVar(value=self.parent.mapping_api_url)

    def create_widgets(self):
        # Remove the existing container and canvas setup since we're using tabs

        # Create notebook for tabs - attach directly to root
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, pady=5, padx=5)

        # Create frames for each tab
        config_frame = ttk.Frame(notebook)
        keys_frame = ttk.Frame(notebook)

        # Add frames to notebook with padding
        notebook.add(config_frame, text="Config", padding=5)
        notebook.add(keys_frame, text="API Keys", padding=5)

        # Create scrollable frame for each tab
        config_canvas = tk.Canvas(config_frame)
        keys_canvas = tk.Canvas(keys_frame)

        config_scrollbar = ttk.Scrollbar(
            config_frame, orient="vertical", command=config_canvas.yview
        )
        keys_scrollbar = ttk.Scrollbar(
            keys_frame, orient="vertical", command=keys_canvas.yview
        )

        self.config_main_frame = ttk.Frame(config_canvas)
        self.keys_main_frame = ttk.Frame(keys_canvas)

        # Configure scrolling
        def _on_mousewheel(event, canvas):
            if event.num == 5 or event.delta < 0:  # Scroll down
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0:  # Scroll up
                canvas.yview_scroll(-1, "units")

        # Bind mousewheel for both canvases
        for canvas in [config_canvas, keys_canvas]:
            canvas.bind_all("<MouseWheel>", lambda e, c=canvas: _on_mousewheel(e, c))
            canvas.bind_all("<Button-4>", lambda e, c=canvas: _on_mousewheel(e, c))
            canvas.bind_all("<Button-5>", lambda e, c=canvas: _on_mousewheel(e, c))

        # Configure the canvases
        for canvas, frame in [
            (config_canvas, self.config_main_frame),
            (keys_canvas, self.keys_main_frame),
        ]:
            frame.bind(
                "<Configure>",
                lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")),
            )
            canvas.create_window((0, 0), window=frame, anchor="nw")
            canvas.configure(yscrollcommand=config_scrollbar.set)

        # Pack scrollbars and canvases with proper fill and expand
        for frame, canvas, scrollbar in [
            (config_frame, config_canvas, config_scrollbar),
            (keys_frame, keys_canvas, keys_scrollbar),
        ]:
            # Configure frame to expand
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            # Use grid instead of pack for better space management
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")

        # Create the content for each tab
        self.create_keys_tab()
        self.create_config_tab()

        # Save Button at the bottom
        ttk.Button(
            self.root,
            text="Save Settings",
            command=self.save_settings,
            style="Blue.TButton",
        ).pack(pady=(5, 10))

    def create_keys_tab(self):
        # API Keys Section
        api_frame = ttk.LabelFrame(self.keys_main_frame, text="API Keys", padding="10")
        api_frame.pack(fill="x", pady=5)

        # OpenAI API Key
        ttk.Label(api_frame, text="OpenAI API Key:").pack(anchor="w")
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill="x", pady=2)
        self.openai_key = tk.StringVar(value="*" * 30 if self.openai_api_key else "")
        self.openai_entry = ttk.Entry(key_frame, textvariable=self.openai_key, width=50)
        self.openai_entry.pack(side="left", fill="x", expand=True)
        self.openai_show_btn = ttk.Button(
            key_frame,
            text="Show",
            width=8,
            command=lambda: self.toggle_show_key(
                self.openai_key, self.openai_api_key, self.openai_show_btn
            ),
        )
        self.openai_show_btn.pack(side="left", padx=(5, 0))
        self.openai_entry.bind("<FocusIn>", lambda e: self.clear_field(self.openai_key))
        self.openai_entry.bind(
            "<FocusOut>",
            lambda e: self.mask_field(self.openai_key, self.openai_api_key),
        )

        # Azure OpenAI API Key
        ttk.Label(api_frame, text="Azure OpenAI API Key:").pack(anchor="w")
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill="x", pady=2)
        self.azure_key = tk.StringVar(value="*" * 30 if self.azure_api_key else "")
        self.azure_entry = ttk.Entry(key_frame, textvariable=self.azure_key, width=50)
        self.azure_entry.pack(side="left", fill="x", expand=True)
        self.azure_show_btn = ttk.Button(
            key_frame,
            text="Show",
            width=8,
            command=lambda: self.toggle_show_key(
                self.azure_key, self.azure_api_key, self.azure_show_btn
            ),
        )
        self.azure_show_btn.pack(side="left", padx=(5, 0))
        self.azure_entry.bind("<FocusIn>", lambda e: self.clear_field(self.azure_key))
        self.azure_entry.bind(
            "<FocusOut>", lambda e: self.mask_field(self.azure_key, self.azure_api_key)
        )

        # Azure OpenAI Endpoint
        ttk.Label(api_frame, text="Azure OpenAI Endpoint:").pack(anchor="w")
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill="x", pady=2)
        self.azure_endpoint = tk.StringVar(value=os.getenv("AZURE_OPENAI_ENDPOINT", ""))
        ttk.Entry(key_frame, textvariable=self.azure_endpoint, width=50).pack(fill="x")

        # HuggingFace API Key
        ttk.Label(api_frame, text="HuggingFace API Key:").pack(anchor="w")
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill="x", pady=2)
        self.huggingface_key = tk.StringVar(
            value="*" * 30 if self.huggingface_api_key else ""
        )
        self.huggingface_entry = ttk.Entry(
            key_frame, textvariable=self.huggingface_key, width=50
        )
        self.huggingface_entry.pack(side="left", fill="x", expand=True)
        self.huggingface_show_btn = ttk.Button(
            key_frame,
            text="Show",
            width=8,
            command=lambda: self.toggle_show_key(
                self.huggingface_key,
                self.huggingface_api_key,
                self.huggingface_show_btn,
            ),
        )
        self.huggingface_show_btn.pack(side="left", padx=(5, 0))
        self.huggingface_entry.bind(
            "<FocusIn>", lambda e: self.clear_field(self.huggingface_key)
        )
        self.huggingface_entry.bind(
            "<FocusOut>",
            lambda e: self.mask_field(self.huggingface_key, self.huggingface_api_key),
        )

        # DeepSeek API Key
        ttk.Label(api_frame, text="DeepSeek API Key:").pack(anchor="w")
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill="x", pady=2)
        self.deepseek_key = tk.StringVar(
            value="*" * 30 if self.deepseek_api_key else ""
        )
        self.deepseek_entry = ttk.Entry(
            key_frame, textvariable=self.deepseek_key, width=50
        )
        self.deepseek_entry.pack(side="left", fill="x", expand=True)
        self.deepseek_show_btn = ttk.Button(
            key_frame,
            text="Show",
            width=8,
            command=lambda: self.toggle_show_key(
                self.deepseek_key, self.deepseek_api_key, self.deepseek_show_btn
            ),
        )
        self.deepseek_show_btn.pack(side="left", padx=(5, 0))
        self.deepseek_entry.bind(
            "<FocusIn>", lambda e: self.clear_field(self.deepseek_key)
        )
        self.deepseek_entry.bind(
            "<FocusOut>",
            lambda e: self.mask_field(self.deepseek_key, self.deepseek_api_key),
        )

    # Add Azure configuration frame to both translation and mapping settings
    def create_azure_config_frame(self, parent_frame, prefix):
        config_frame = ttk.LabelFrame(
            parent_frame, text="Azure Configuration", padding="5"
        )
        config_frame.pack(fill="x", pady=5)

        # Temperature
        temp_frame = ttk.Frame(config_frame)
        temp_frame.pack(fill="x", pady=2)
        ttk.Label(temp_frame, text="Temperature:", style="Small.TLabel").pack(
            side="left"
        )
        temp_var = tk.DoubleVar(value=AZURE_CONFIG["temperature"])
        setattr(self, f"{prefix}_temperature", temp_var)
        ttk.Entry(temp_frame, textvariable=temp_var, width=10).pack(side="left", padx=5)

        # Frequency Penalty
        freq_frame = ttk.Frame(config_frame)
        freq_frame.pack(fill="x", pady=2)
        ttk.Label(freq_frame, text="Frequency Penalty:", style="Small.TLabel").pack(
            side="left"
        )
        freq_var = tk.DoubleVar(value=AZURE_CONFIG["frequency_penalty"])
        setattr(self, f"{prefix}_frequency_penalty", freq_var)
        ttk.Entry(freq_frame, textvariable=freq_var, width=10).pack(side="left", padx=5)

        # Presence Penalty
        pres_frame = ttk.Frame(config_frame)
        pres_frame.pack(fill="x", pady=2)
        ttk.Label(pres_frame, text="Presence Penalty:", style="Small.TLabel").pack(
            side="left"
        )
        pres_var = tk.DoubleVar(value=AZURE_CONFIG["presence_penalty"])
        setattr(self, f"{prefix}_presence_penalty", pres_var)
        ttk.Entry(pres_frame, textvariable=pres_var, width=10).pack(side="left", padx=5)

        # Max Tokens
        token_frame = ttk.Frame(config_frame)
        token_frame.pack(fill="x", pady=2)
        ttk.Label(token_frame, text="Max Tokens:", style="Small.TLabel").pack(
            side="left"
        )
        token_var = tk.IntVar(value=AZURE_CONFIG["max_tokens_out"])
        setattr(self, f"{prefix}_max_tokens", token_var)
        ttk.Entry(token_frame, textvariable=token_var, width=10).pack(
            side="left", padx=5
        )

        return config_frame

    def create_config_tab(self):
        # Translation Method Section
        translation_frame = ttk.LabelFrame(
            self.config_main_frame, text="Translation Settings", padding="10"
        )
        translation_frame.pack(fill="x", pady=5)

        # Translation Method
        ttk.Label(translation_frame, text="Translation Method:").pack(anchor="w")
        self.translation_method = tk.StringVar(
            value=self.parent.translation_method.get()
        )
        translation_methods = [
            "OpenAI",
            "LMStudio",
            "HuggingFace",
            "DeepSeek",
            "Azure OpenAI",
        ]
        translation_method_menu = ttk.OptionMenu(
            translation_frame,
            self.translation_method,
            self.translation_method.get(),
            *translation_methods,
        )
        translation_method_menu.pack(fill="x", pady=2)

        # Translation Model Selection Frame
        self.translation_model_frame = ttk.Frame(translation_frame)
        self.translation_model_frame.pack(fill="x", pady=2)

        # OpenAI Translation Models
        self.openai_translation_model = tk.StringVar(
            value=self.parent.translation_model
        )
        self.openai_translation_models = ttk.Frame(self.translation_model_frame)
        ttk.Label(self.openai_translation_models, text="OpenAI Model:").pack(
            side="left"
        )
        openai_models = ["gpt-4", "gpt-3.5-turbo"]
        ttk.OptionMenu(
            self.openai_translation_models,
            self.openai_translation_model,
            self.openai_translation_model.get(),
            *openai_models,
        ).pack(side="left", padx=5)

        # LMStudio Translation Settings
        self.lmstudio_translation_model = tk.StringVar(
            value=self.parent.translation_model
        )
        self.translation_lmstudio_server = tk.StringVar(
            value=self.parent.translation_api_url
        )
        self.lmstudio_translation_frame = ttk.Frame(self.translation_model_frame)
        ttk.Label(self.lmstudio_translation_frame, text="Model Name:").pack(side="left")
        ttk.Entry(
            self.lmstudio_translation_frame,
            textvariable=self.lmstudio_translation_model,
        ).pack(side="left", padx=5)
        ttk.Label(self.lmstudio_translation_frame, text="Server URL:").pack(side="left")
        ttk.Entry(
            self.lmstudio_translation_frame,
            textvariable=self.translation_lmstudio_server,
        ).pack(side="left", padx=5)

        # HuggingFace Translation Settings
        self.translation_huggingface_url = tk.StringVar(
            value=self.parent.translation_api_url
        )
        self.huggingface_translation_frame = ttk.Frame(self.translation_model_frame)
        ttk.Label(self.huggingface_translation_frame, text="API URL:").pack(side="left")
        ttk.Entry(
            self.huggingface_translation_frame,
            textvariable=self.translation_huggingface_url,
        ).pack(side="left", padx=5)

        # DeepSeek Translation Models
        self.deepseek_translation_model = tk.StringVar(
            value=self.parent.translation_model
        )
        self.deepseek_translation_frame = ttk.Frame(self.translation_model_frame)
        ttk.Label(self.deepseek_translation_frame, text="DeepSeek Model:").pack(
            side="left"
        )
        deepseek_models = ["deepseek-chat", "deepseek-coder"]
        ttk.OptionMenu(
            self.deepseek_translation_frame,
            self.deepseek_translation_model,
            self.deepseek_translation_model.get(),
            *deepseek_models,
        ).pack(side="left", padx=5)

        # Azure OpenAI Translation Settings
        self.azure_translation_model = tk.StringVar(value=self.parent.translation_model)
        self.azure_translation_endpoint = tk.StringVar(
            value=self.parent.translation_api_url
        )
        self.azure_translation_frame = ttk.Frame(self.translation_model_frame)
        ttk.Label(self.azure_translation_frame, text="Model Name:").pack(side="left")
        ttk.Entry(
            self.azure_translation_frame, textvariable=self.azure_translation_model
        ).pack(side="left", padx=5)

        # Azure Configuration Settings
        self.translation_temperature = tk.DoubleVar(value=0.7)
        self.translation_frequency_penalty = tk.DoubleVar(value=0.0)
        self.translation_presence_penalty = tk.DoubleVar(value=0.0)
        self.translation_max_tokens = tk.IntVar(value=2000)

        azure_config_frame = ttk.Frame(self.azure_translation_frame)
        azure_config_frame.pack(fill="x", pady=2)

        ttk.Label(azure_config_frame, text="Temperature:").pack(side="left")
        ttk.Entry(
            azure_config_frame, textvariable=self.translation_temperature, width=8
        ).pack(side="left", padx=5)
        ttk.Label(azure_config_frame, text="Freq Penalty:").pack(side="left")
        ttk.Entry(
            azure_config_frame, textvariable=self.translation_frequency_penalty, width=8
        ).pack(side="left", padx=5)
        ttk.Label(azure_config_frame, text="Pres Penalty:").pack(side="left")
        ttk.Entry(
            azure_config_frame, textvariable=self.translation_presence_penalty, width=8
        ).pack(side="left", padx=5)
        ttk.Label(azure_config_frame, text="Max Tokens:").pack(side="left")
        ttk.Entry(
            azure_config_frame, textvariable=self.translation_max_tokens, width=8
        ).pack(side="left", padx=5)

        # Show/hide appropriate frames based on selected method
        self.translation_method.trace("w", self.update_translation_frames)
        self.update_translation_frames()

        # Mapping Method Section
        mapping_frame = ttk.LabelFrame(
            self.config_main_frame, text="Mapping Settings", padding="10"
        )
        mapping_frame.pack(fill="x", pady=5)

        # Mapping Method
        ttk.Label(mapping_frame, text="Mapping Method:").pack(anchor="w")
        self.mapping_method = tk.StringVar(value=self.parent.mapping_method.get())
        mapping_methods = [
            "OpenAI",
            "LMStudio",
            "HuggingFace",
            "DeepSeek",
            "Azure OpenAI",
        ]
        mapping_method_menu = ttk.OptionMenu(
            mapping_frame,
            self.mapping_method,
            self.mapping_method.get(),
            *mapping_methods,
        )
        mapping_method_menu.pack(fill="x", pady=2)

        # Mapping Model Selection Frame
        self.mapping_model_frame = ttk.Frame(mapping_frame)
        self.mapping_model_frame.pack(fill="x", pady=2)

        # OpenAI Mapping Models
        self.openai_mapping_models = ttk.Frame(self.mapping_model_frame)
        ttk.Label(self.openai_mapping_models, text="OpenAI Model:").pack(side="left")
        ttk.OptionMenu(
            self.openai_mapping_models,
            self.openai_mapping_model,
            self.openai_mapping_model.get(),
            *OPENAI_MODELS,
        ).pack(side="left", padx=5)

        # LMStudio Mapping Settings
        self.lmstudio_mapping_frame = ttk.Frame(self.mapping_model_frame)
        ttk.Label(self.lmstudio_mapping_frame, text="Model Name:").pack(side="left")
        ttk.Entry(
            self.lmstudio_mapping_frame, textvariable=self.lmstudio_mapping_model
        ).pack(side="left", padx=5)
        ttk.Label(self.lmstudio_mapping_frame, text="Server URL:").pack(side="left")
        ttk.Entry(
            self.lmstudio_mapping_frame, textvariable=self.mapping_lmstudio_server
        ).pack(side="left", padx=5)

        # HuggingFace Mapping Settings
        self.huggingface_mapping_frame = ttk.Frame(self.mapping_model_frame)
        ttk.Label(self.huggingface_mapping_frame, text="API URL:").pack(side="left")
        ttk.Entry(
            self.huggingface_mapping_frame, textvariable=self.mapping_huggingface_url
        ).pack(side="left", padx=5)

        # DeepSeek Mapping Models
        self.deepseek_mapping_frame = ttk.Frame(self.mapping_model_frame)
        ttk.Label(self.deepseek_mapping_frame, text="DeepSeek Model:").pack(side="left")
        ttk.OptionMenu(
            self.deepseek_mapping_frame,
            self.deepseek_mapping_model,
            self.deepseek_mapping_model.get(),
            *DEEPSEEK_MODELS,
        ).pack(side="left", padx=5)

        # Azure OpenAI Mapping Settings
        self.azure_mapping_frame = ttk.Frame(self.mapping_model_frame)
        ttk.Label(self.azure_mapping_frame, text="Model Name:").pack(side="left")
        ttk.Entry(self.azure_mapping_frame, textvariable=self.azure_mapping_model).pack(
            side="left", padx=5
        )

        # Add Azure configuration for mapping
        self.azure_mapping_config_frame = self.create_azure_config_frame(
            mapping_frame, "mapping"
        )

        # Add trace to update visible frames based on selected method
        self.mapping_method.trace("w", self.update_mapping_frames)
        self.update_mapping_frames()

    def update_translation_frames(self, *args):
        # Hide all frames first
        for frame in [
            self.openai_translation_models,
            self.lmstudio_translation_frame,
            self.huggingface_translation_frame,
            self.deepseek_translation_frame,
            self.azure_translation_frame,
        ]:
            frame.pack_forget()

        # Show the appropriate frame based on selected method
        method = self.translation_method.get()
        if method == "OpenAI":
            self.openai_translation_models.pack(fill="x")
        elif method == "LMStudio":
            self.lmstudio_translation_frame.pack(fill="x")
        elif method == "HuggingFace":
            self.huggingface_translation_frame.pack(fill="x")
        elif method == "DeepSeek":
            self.deepseek_translation_frame.pack(fill="x")
        elif method == "Azure OpenAI":
            self.azure_translation_frame.pack(fill="x")

    def update_mapping_frames(self, *args):
        # Hide all frames first
        for frame in [
            self.openai_mapping_models,
            self.lmstudio_mapping_frame,
            self.huggingface_mapping_frame,
            self.deepseek_mapping_frame,
            self.azure_mapping_frame,
            self.azure_mapping_config_frame,
        ]:
            frame.pack_forget()

        # Show the appropriate frame based on selected method
        method = self.mapping_method.get()
        if method == "OpenAI":
            self.openai_mapping_models.pack(fill="x")
        elif method == "LMStudio":
            self.lmstudio_mapping_frame.pack(fill="x")
        elif method == "HuggingFace":
            self.huggingface_mapping_frame.pack(fill="x")
        elif method == "DeepSeek":
            self.deepseek_mapping_frame.pack(fill="x")
        elif method == "Azure OpenAI":
            self.azure_mapping_frame.pack(fill="x")
            self.azure_mapping_config_frame.pack(fill="x")
