"""Modern SlideMob GUI with CustomTkinter."""
import json
import logging
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import traceback

import customtkinter as ctk

from ..core_functions.base_class import PowerpointPipeline
from ..pipelines.polisher_pipeline import PowerPointPolisher
from ..pipelines.run_merger_pipeline import PowerPointRunMerger
from ..pipelines.translator_pipeline import PowerPointTranslator
from ..utils.config import create_config
from ..utils.errorhandler import setup_error_logging
from ..utils.path_manager import PathManager, get_resource_path, get_user_config_path, get_user_env_path
from .settings_window import SettingsWindow
from .tooltips import Tooltip, TOOLTIP_TEXTS

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SlideMobGUI(PowerpointPipeline):
    """Modern GUI for SlideMob PowerPoint Processor."""
    
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.root.title("SlideMob")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Initialize model defaults
        self.translation_model = "gpt-4"
        self.mapping_model = "gpt-4"
        self.translation_api_url = "http://localhost:1234"
        self.mapping_api_url = "http://localhost:1234"
        
        # Initialize tk variables
        self.gui_pptx_path = tk.StringVar(self.root)
        self.gui_output_path = tk.StringVar(self.root)
        self.gui_target_language = tk.StringVar(self.root, value="English")
        self.gui_style_instructions = tk.StringVar(self.root)
        self.translation_method = tk.StringVar(self.root, value="OpenAI")
        self.mapping_method = tk.StringVar(self.root, value="OpenAI")
        
        # Checkbox variables
        self.extract_var = tk.BooleanVar(value=True)
        self.polish_var = tk.BooleanVar(value=False)
        self.translate_var = tk.BooleanVar(value=True)
        self.update_language = tk.BooleanVar(value=False)
        self.reduce_slides = tk.BooleanVar(value=False)
        self.merge_runs_var = tk.BooleanVar(value=False)
        self.overwrite_file = tk.BooleanVar(value=False)
        self.translation_strategy = tk.StringVar(self.root, value="classic")
        
        # Status variable
        self.status_var = tk.StringVar(value="Ready")
        
        # Load config
        self.load_gui_config()
        
        # Load language options
        config_languages_path = get_resource_path("slidemob/config_languages.json")
        with open(config_languages_path) as f:
            language_config = json.load(f)
        self.language_options = [
            lang["language"].split(" (")[0] for lang in language_config["languages"]
        ]
        
        # Initialize state
        self.processing = False
        self.stop_requested = False
        
        # Setup error logging
        setup_error_logging()
        
        # Variable traces
        self.gui_pptx_path.trace_add("write", self._update_pptx_path)
        self.gui_output_path.trace_add("write", self._update_output_path)
        
        # Load logo images
        self._load_images()
        
        # Create the UI
        self._create_ui()
    
    def _load_images(self):
        """Load SlideMob logo images."""
        try:
            from PIL import Image, ImageTk
            
            # Load app logo
            logo_path = get_resource_path("slidemob/images/doppelfahreimerSmall.png")
            logo_image = Image.open(logo_path)
            logo_image = logo_image.resize((60, 60), Image.Resampling.LANCZOS)
            self.app_logo = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(60, 60))
            
            # Load company logo for corner
            company_path = get_resource_path("slidemob/gui/assets/eraneos_bg Small.png")
            company_image = Image.open(company_path)
            company_image = company_image.resize((80, 40), Image.Resampling.LANCZOS)
            self.company_logo = ctk.CTkImage(light_image=company_image, dark_image=company_image, size=(80, 40))
        except Exception as e:
            print(f"Warning: Could not load images: {e}")
            self.app_logo = None
            self.company_logo = None
    
    def _update_pptx_path(self, *args):
        self.pptx_path = self.gui_pptx_path.get()
    
    def _update_output_path(self, *args):
        self.output_path = self.gui_output_path.get()
    
    def _create_ui(self):
        """Build the modern UI with left-side tabs."""
        # Main container
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left sidebar for navigation
        self.sidebar = ctk.CTkFrame(self.main_container, width=180, corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)
        
        # App title in sidebar
        self.title_label = ctk.CTkLabel(
            self.sidebar, 
            text="SlideMob", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(20, 30))
        
        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("home", "Home"),
            ("processing", "Processing"),
            ("translation", "Translation"),
            ("config", "Configuration"),
            ("api_keys", "API Keys"),
        ]
        
        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=ctk.CTkFont(size=14),
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray70", "gray90"),
                hover_color=("gray25", "gray25"),
                anchor="w",
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.nav_buttons[key] = btn
        
        # Settings button at bottom of sidebar
        self.settings_btn = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=8,
            fg_color="transparent",
            text_color=("gray70", "gray90"),
            hover_color=("gray25", "gray25"),
            anchor="w",
            command=self.open_settings
        )
        self.settings_btn.pack(side="bottom", fill="x", padx=10, pady=(5, 10))
        Tooltip(self.settings_btn, TOOLTIP_TEXTS["settings"])
        
        # Logo at bottom of sidebar
        if self.app_logo:
            logo_label = ctk.CTkLabel(self.sidebar, image=self.app_logo, text="")
            logo_label.pack(side="bottom", pady=(0, 15))
        
        # Content area
        self.content_area = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.content_area.pack(side="right", fill="both", expand=True)
        
        # Create tab frames
        self.tab_frames = {}
        self._create_home_tab()
        self._create_processing_tab()
        self._create_translation_tab()
        self._create_config_tab()
        self._create_api_keys_tab()
        
        # Show home tab by default
        self._switch_tab("home")
        
        # Status bar at bottom
        self.status_bar = ctk.CTkLabel(
            self.root,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        self.status_bar.pack(side="bottom", pady=5)
    
    def _switch_tab(self, tab_key: str):
        """Switch to the specified tab."""
        # Hide all tabs
        for frame in self.tab_frames.values():
            frame.pack_forget()
        
        # Update button colors
        for key, btn in self.nav_buttons.items():
            if key == tab_key:
                btn.configure(fg_color=("gray25", "gray25"))
            else:
                btn.configure(fg_color="transparent")
        
        # Show selected tab
        if tab_key in self.tab_frames:
            self.tab_frames[tab_key].pack(fill="both", expand=True, padx=20, pady=20)
    
    def _create_home_tab(self):
        """Create the Home tab with file selection and main actions."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.tab_frames["home"] = frame
        
        # Title
        ctk.CTkLabel(
            frame,
            text="PowerPoint Processing",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w", pady=(0, 20))
        
        # File Selection Section
        file_section = ctk.CTkFrame(frame, corner_radius=8)
        file_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            file_section,
            text="Input File",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        file_row = ctk.CTkFrame(file_section, fg_color="transparent")
        file_row.pack(fill="x", padx=15, pady=(0, 15))
        
        self.pptx_entry = ctk.CTkEntry(
            file_row,
            textvariable=self.gui_pptx_path,
            placeholder_text="Select PowerPoint file...",
            height=40
        )
        self.pptx_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        Tooltip(self.pptx_entry, TOOLTIP_TEXTS["pptx_file"])
        
        browse_btn = ctk.CTkButton(
            file_row,
            text="Browse",
            width=100,
            height=40,
            command=self.browse_pptx
        )
        browse_btn.pack(side="right")
        
        # Output Section
        output_section = ctk.CTkFrame(frame, corner_radius=8)
        output_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            output_section,
            text="Output Folder",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        output_row = ctk.CTkFrame(output_section, fg_color="transparent")
        output_row.pack(fill="x", padx=15, pady=(0, 15))
        
        self.output_entry = ctk.CTkEntry(
            output_row,
            textvariable=self.gui_output_path,
            placeholder_text="Select output folder...",
            height=40
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        Tooltip(self.output_entry, TOOLTIP_TEXTS["output_folder"])
        
        output_browse_btn = ctk.CTkButton(
            output_row,
            text="Browse",
            width=100,
            height=40,
            command=self.browse_output
        )
        output_browse_btn.pack(side="right")
        
        # Action Buttons
        action_frame = ctk.CTkFrame(frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=(20, 0))
        
        self.process_btn = ctk.CTkButton(
            action_frame,
            text="Process Presentation",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=10,
            command=self.process_presentation
        )
        self.process_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))
        Tooltip(self.process_btn, TOOLTIP_TEXTS["process"])
        
        self.stop_btn = ctk.CTkButton(
            action_frame,
            text="Stop",
            font=ctk.CTkFont(size=16),
            height=50,
            corner_radius=10,
            fg_color=("#dc3545", "#dc3545"),
            hover_color=("#c82333", "#c82333"),
            state="disabled",
            command=self.stop_processing
        )
        self.stop_btn.pack(side="right")
        Tooltip(self.stop_btn, TOOLTIP_TEXTS["stop"])
    
    def _create_processing_tab(self):
        """Create the Processing tab with all processing options."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.tab_frames["processing"] = frame
        
        # Title
        ctk.CTkLabel(
            frame,
            text="Processing Options",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w", pady=(0, 20))
        
        # Options container
        options_frame = ctk.CTkFrame(frame, corner_radius=8)
        options_frame.pack(fill="x")
        
        # Create checkboxes with tooltips
        options = [
            ("extract_var", "Extract PPTX", "extract"),
            ("merge_runs_var", "Pre-Merge Runs", "pre_merge"),
            ("polish_var", "Polish Content", "polish"),
            ("translate_var", "Translate Content", "translate"),
            ("update_language", "Update PPTX Language", "update_language"),
            ("reduce_slides", "Reduce Slides", "reduce_slides"),
            ("overwrite_file", "Overwrite Original File", "overwrite"),
        ]
        
        for var_name, label, tooltip_key in options:
            row = ctk.CTkFrame(options_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=8)
            
            cb = ctk.CTkCheckBox(
                row,
                text=label,
                variable=getattr(self, var_name),
                font=ctk.CTkFont(size=14),
                corner_radius=5
            )
            cb.pack(side="left")
            Tooltip(cb, TOOLTIP_TEXTS[tooltip_key])
        
        # Add some padding at bottom
        ctk.CTkFrame(options_frame, fg_color="transparent", height=15).pack()
    
    def _create_translation_tab(self):
        """Create the Translation tab with language settings."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.tab_frames["translation"] = frame
        
        # Title
        ctk.CTkLabel(
            frame,
            text="Translation Settings",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w", pady=(0, 20))
        
        # Language Section
        lang_section = ctk.CTkFrame(frame, corner_radius=8)
        lang_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            lang_section,
            text="Target Language",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        lang_dropdown = ctk.CTkComboBox(
            lang_section,
            values=self.language_options,
            variable=self.gui_target_language,
            width=300,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        lang_dropdown.pack(anchor="w", padx=15, pady=(0, 15))
        Tooltip(lang_dropdown, TOOLTIP_TEXTS["target_language"])
        
        # Strategy Section
        strategy_section = ctk.CTkFrame(frame, corner_radius=8)
        strategy_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            strategy_section,
            text="Translation Strategy",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        strategy_dropdown = ctk.CTkComboBox(
            strategy_section,
            values=["classic", "marker-based"],
            variable=self.translation_strategy,
            width=300,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        strategy_dropdown.pack(anchor="w", padx=15, pady=(0, 15))
        Tooltip(strategy_dropdown, TOOLTIP_TEXTS["translation_strategy"])
        
        # Style Instructions Section
        style_section = ctk.CTkFrame(frame, corner_radius=8)
        style_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            style_section,
            text="Style Instructions (Optional)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        style_entry = ctk.CTkEntry(
            style_section,
            textvariable=self.gui_style_instructions,
            placeholder_text="E.g., 'Use formal language' or 'Keep technical terms'",
            height=40
        )
        style_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Method Info (read-only display)
        info_section = ctk.CTkFrame(frame, corner_radius=8)
        info_section.pack(fill="x")
        
        ctk.CTkLabel(
            info_section,
            text="Current Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        info_text = f"Translation: {self.translation_method.get()} | Mapping: {self.mapping_method.get()}"
        self.config_info_label = ctk.CTkLabel(
            info_section,
            text=info_text,
            font=ctk.CTkFont(size=13),
            text_color="gray60"
        )
        self.config_info_label.pack(anchor="w", padx=15, pady=(0, 15))
    
    def _create_config_tab(self):
        """Create the Configuration tab with model settings."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.tab_frames["config"] = frame
        
        # Title
        ctk.CTkLabel(
            frame,
            text="Configuration",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w", pady=(0, 20))
        
        # Translation Method Section
        trans_section = ctk.CTkFrame(frame, corner_radius=8)
        trans_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            trans_section,
            text="Translation Method",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        trans_methods = ["OpenAI", "DeepSeek", "Azure OpenAI", "HuggingFace", "LMStudio"]
        trans_dropdown = ctk.CTkComboBox(
            trans_section,
            values=trans_methods,
            variable=self.translation_method,
            width=300,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        trans_dropdown.pack(anchor="w", padx=15, pady=(0, 15))
        Tooltip(trans_dropdown, TOOLTIP_TEXTS["translation_method"])
        
        # Mapping Method Section
        map_section = ctk.CTkFrame(frame, corner_radius=8)
        map_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            map_section,
            text="Mapping Method",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        map_dropdown = ctk.CTkComboBox(
            map_section,
            values=trans_methods,
            variable=self.mapping_method,
            width=300,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        map_dropdown.pack(anchor="w", padx=15, pady=(0, 15))
        Tooltip(map_dropdown, TOOLTIP_TEXTS["mapping_method"])
        
        # Model Names Section
        model_section = ctk.CTkFrame(frame, corner_radius=8)
        model_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            model_section,
            text="Model Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        # Translation Model
        ctk.CTkLabel(model_section, text="Translation Model:", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=15, pady=(5, 0))
        self.trans_model_entry = ctk.CTkEntry(model_section, height=35)
        self.trans_model_entry.insert(0, self.translation_model)
        self.trans_model_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        # Mapping Model
        ctk.CTkLabel(model_section, text="Mapping Model:", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=15, pady=(5, 0))
        self.map_model_entry = ctk.CTkEntry(model_section, height=35)
        self.map_model_entry.insert(0, self.mapping_model)
        self.map_model_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Save button
        save_btn = ctk.CTkButton(
            frame,
            text="Save Configuration",
            height=40,
            command=self._save_config_settings
        )
        save_btn.pack(anchor="w", pady=(10, 0))
    
    def _create_api_keys_tab(self):
        """Create the API Keys tab."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.tab_frames["api_keys"] = frame
        
        # Title
        ctk.CTkLabel(
            frame,
            text="API Keys",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w", pady=(0, 20))
        
        # Note
        ctk.CTkLabel(
            frame,
            text="API keys are stored securely in your home directory (~/.slidemob/.env)",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        ).pack(anchor="w", pady=(0, 15))
        
        # API Keys Section
        keys_section = ctk.CTkFrame(frame, corner_radius=8)
        keys_section.pack(fill="x", pady=(0, 15))
        
        api_keys = [
            ("OpenAI API Key", "OPENAI_API_KEY"),
            ("DeepSeek API Key", "DEEPSEEK_API_KEY"),
            ("HuggingFace Token", "HUGGINGFACE"),
            ("Azure Endpoint Key", "AZURE_OPENAI_ENDPOINT_KEY"),
            ("Azure Endpoint URL", "AZURE_OPENAI_ENDPOINT"),
        ]
        
        self.api_key_entries = {}
        
        for label, env_var in api_keys:
            ctk.CTkLabel(
                keys_section,
                text=label,
                font=ctk.CTkFont(size=13)
            ).pack(anchor="w", padx=15, pady=(10, 0))
            
            entry = ctk.CTkEntry(keys_section, height=35, show="*")
            # Load existing value if present
            existing = os.getenv(env_var, "")
            if existing:
                entry.insert(0, existing)
            entry.pack(fill="x", padx=15, pady=(0, 5))
            self.api_key_entries[env_var] = entry
        
        # Add some padding
        ctk.CTkFrame(keys_section, fg_color="transparent", height=10).pack()
        
        # Save button
        save_btn = ctk.CTkButton(
            frame,
            text="Save API Keys",
            height=40,
            command=self._save_api_keys
        )
        save_btn.pack(anchor="w", pady=(10, 0))
    
    def _save_config_settings(self):
        """Save configuration settings."""
        self.translation_model = self.trans_model_entry.get()
        self.mapping_model = self.map_model_entry.get()
        self.save_gui_config(save_all=True)
        messagebox.showinfo("Saved", "Configuration saved successfully!")
    
    def _save_api_keys(self):
        """Save API keys to .env file."""
        from dotenv import set_key
        env_path = get_user_env_path()
        
        for env_var, entry in self.api_key_entries.items():
            value = entry.get()
            if value:
                set_key(env_path, env_var, value)
        
        messagebox.showinfo("Saved", "API keys saved successfully!")
    
    # -------------------------------------------------------------------------
    # Core Methods (kept from original)
    # -------------------------------------------------------------------------
    
    def browse_pptx(self):
        filename = filedialog.askopenfilename(
            title="Select PowerPoint File", filetypes=[("PowerPoint files", "*.pptx")]
        )
        if filename:
            self.gui_pptx_path.set(filename)
            self.save_gui_config()
    
    def browse_output(self):
        if self.gui_pptx_path.get():
            startfolder = os.path.dirname(self.gui_pptx_path.get())
        else:
            startfolder = os.getcwd()
        folder = filedialog.askdirectory(
            title="Select Output Folder", initialdir=startfolder
        )
        if folder:
            self.gui_output_path.set(folder)
            self.save_gui_config()
    
    def update_translation_progress(self, slide_name, current, total):
        self.status_var.set(f"Translating slide {current} of {total} ({slide_name})")
        self.root.update()
    
    def process_presentation(self):
        if not self.gui_pptx_path.get() or not self.gui_output_path.get():
            messagebox.showerror("Error", "Please select both input file and output location")
            return
        
        self.processing = True
        self.stop_requested = False
        self.process_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.root.update()
        
        try:
            self.save_gui_config()
            
            path_manager = PathManager(
                self.gui_pptx_path.get(),
                self.gui_output_path.get(),
                overwrite=self.overwrite_file.get()
            )
            config = create_config(
                path_manager=path_manager,
                target_language=self.gui_target_language.get(),
            )
            
            if self.stop_requested:
                raise Exception("Processing stopped by user")
            
            if self.extract_var.get():
                self.status_var.set("Extracting PPTX...")
                self.root.update()
                success = self.extract_pptx()
                if not success:
                    raise Exception("Extraction failed")
            
            if self.stop_requested:
                raise Exception("Processing stopped by user")
            
            if self.polish_var.get():
                self.status_var.set("Polishing content...")
                self.root.update()
                polisher = PowerPointPolisher(
                    Further_StyleInstructions=self.gui_style_instructions.get(),
                    fresh_extract=not self.extract_var.get(),
                    pipeline_config=config,
                )
                success = polisher.polish_presentation()
                if not success:
                    raise Exception("Polishing failed")
            
            if self.stop_requested:
                raise Exception("Processing stopped by user")
            
            if self.translate_var.get():
                self.status_var.set("Starting translation...")
                self.root.update()
                translator = PowerPointTranslator(
                    progress_callback=self.update_translation_progress,
                    stop_check_callback=lambda: self.stop_requested,
                    pipeline_config=config,
                )
                success = translator.translate_presentation()
                if not success:
                    if self.stop_requested:
                        raise Exception("Processing stopped by user")
                    raise Exception("Translation failed")
            
            if self.stop_requested:
                raise Exception("Processing stopped by user")
            
            if self.merge_runs_var.get():
                self.status_var.set("Merging similar runs...")
                self.root.update()
                merger = PowerPointRunMerger(
                    fresh_extract=not (
                        self.extract_var.get()
                        or self.polish_var.get()
                        or self.translate_var.get()
                    ),
                    pipeline_config=config,
                )
                success = merger.merge_runs_in_presentation()
                if not success:
                    raise Exception("Run merging failed")
            
            self.status_var.set("Processing complete!")
            
            output_file = path_manager.output_pptx
            output_folder = path_manager.output_dir
            
            success_msg = (
                f"PowerPoint processing completed successfully!\n\n"
                f"Filename: {os.path.basename(output_file)}\n"
                f"Folder: {output_folder}"
            )
            messagebox.showinfo("Success", success_msg)
        
        except Exception as e:
            self.status_var.set(f"Error: {e!s}")
            messagebox.showerror("Error", f"An error occurred: {e!s}")
            logging.exception("Error in process_presentation")
        
        finally:
            self.processing = False
            self.process_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
    
    def stop_processing(self):
        self.stop_requested = True
        self.status_var.set("Stopping...")
    
    def open_settings(self):
        settings_root = tk.Toplevel(self.root)
        SettingsWindow(settings_root, self)
    
    def load_gui_config(self):
        try:
            config_path = get_user_config_path()
            if os.path.exists(config_path):
                with open(config_path) as f:
                    config = json.load(f)
                
                self.gui_pptx_path.set(config.get("pptx_path", ""))
                self.gui_output_path.set(config.get("output_path", ""))
                self.gui_target_language.set(config.get("target_language", "English"))
                self.extract_var.set(config.get("extract_pptx", True))
                self.merge_runs_var.set(config.get("pre_merge", False))
                self.polish_var.set(config.get("polish_content", False))
                self.translate_var.set(config.get("translate_content", True))
                self.update_language.set(config.get("update_language", False))
                self.reduce_slides.set(config.get("reduce_slides", False))
                self.translation_method.set(config.get("translation_method", "OpenAI"))
                self.gui_style_instructions.set(config.get("style_instructions", ""))
                self.mapping_method.set(config.get("mapping_method", "OpenAI"))
                self.translation_strategy.set(config.get("translation_strategy", "classic"))
                self.overwrite_file.set(config.get("overwrite_file", False))
                
                self.translation_model = config.get("translation_model", "gpt-4")
                self.mapping_model = config.get("mapping_model", "gpt-4")
                self.translation_api_url = config.get("translation_api_url", "http://localhost:1234")
                self.mapping_api_url = config.get("mapping_api_url", "http://localhost:1234")
        except Exception as e:
            print(f"Error loading GUI config: {e}")
    
    def save_gui_config(self, save_all=False):
        try:
            config_path = get_user_config_path()
            config = {}
            if os.path.exists(config_path):
                with open(config_path) as f:
                    config = json.load(f)
            
            if save_all:
                config.update({
                    "extract_pptx": self.extract_var.get(),
                    "pre_merge": self.merge_runs_var.get(),
                    "polish_content": self.polish_var.get(),
                    "translate_content": self.translate_var.get(),
                    "update_language": self.update_language.get(),
                    "reduce_slides": self.reduce_slides.get(),
                    "target_language": self.gui_target_language.get(),
                    "translation_method": self.translation_method.get(),
                    "mapping_method": self.mapping_method.get(),
                    "style_instructions": self.gui_style_instructions.get(),
                    "translation_model": self.translation_model,
                    "mapping_model": self.mapping_model,
                    "translation_api_url": self.translation_api_url,
                    "mapping_api_url": self.mapping_api_url,
                    "translation_strategy": self.translation_strategy.get(),
                    "overwrite_file": self.overwrite_file.get(),
                })
            else:
                config.update({
                    "pptx_path": self.gui_pptx_path.get(),
                    "output_path": self.gui_output_path.get(),
                    "target_language": self.gui_target_language.get(),
                })
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving GUI config: {e}")
    
    def update_config(self, new_values: dict):
        for key, value in new_values.items():
            if key == "translation_method":
                self.translation_method.set(value)
            elif key == "mapping_method":
                self.mapping_method.set(value)
            elif key == "translation_model":
                self.translation_model = value
            elif key == "mapping_model":
                self.mapping_model = value
            elif key == "translation_api_url":
                self.translation_api_url = value
            elif key == "mapping_api_url":
                self.mapping_api_url = value
            elif key == "translation_strategy":
                self.translation_strategy.set(value)
            elif key == "overwrite_file":
                self.overwrite_file.set(value)
        
        # Update display
        if hasattr(self, 'config_info_label'):
            info_text = f"Translation: {self.translation_method.get()} | Mapping: {self.mapping_method.get()}"
            self.config_info_label.configure(text=info_text)


if __name__ == "__main__":
    root = ctk.CTk()
    app = SlideMobGUI(root)
    root.mainloop()
