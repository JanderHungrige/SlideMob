"""Modern SlideMob GUI with CustomTkinter."""
import json
import logging
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import traceback
import webbrowser
import requests
import threading

import customtkinter as ctk

from ..core_functions.base_class import PowerpointPipeline
from ..pipelines.polisher_pipeline import PowerPointPolisher
from ..pipelines.run_merger_pipeline import PowerPointRunMerger
from ..pipelines.translator_pipeline import PowerPointTranslator
from ..utils.config import create_config
from ..utils.errorhandler import setup_error_logging
from ..utils.path_manager import PathManager, get_resource_path, get_user_config_path, get_user_env_path
# from .settings_window import SettingsWindow  # No longer needed as settings moved to tabs
from .tooltips import Tooltip, TOOLTIP_TEXTS

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SlideMobGUI:
    """Modern GUI for SlideMob PowerPoint Processor."""
    
    def __init__(self, root):
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
        self.gui_target_language = ctk.StringVar(value="English")
        self.gui_source_language = ctk.StringVar(value="English")
        self.gui_target_language.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.gui_style_instructions = ctk.StringVar(value="")
        self.translation_strategy = ctk.StringVar(value="")
        self.translation_strategy.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.translation_method = tk.StringVar(self.root, value="OpenAI")
        self.mapping_method = tk.StringVar(self.root, value="OpenAI")
        
        # Checkbox variables
        self.extract_var = tk.BooleanVar(value=True)
        self.polish_var = tk.BooleanVar(value=False)
        self.translate_var = tk.BooleanVar(value=True)
        self.update_language = tk.BooleanVar(value=False)
        self.reduce_slides = tk.BooleanVar(value=False)
        self.merge_runs_var = tk.BooleanVar(value=False)
        self.save_into_copy = tk.BooleanVar(value=True)
        self.gui_slide_selection = tk.StringVar(self.root, value="")
        
        # Status variable
        self.status_var = tk.StringVar(value="Ready")
        self.argos_install_btn_text = tk.StringVar(value="Install Language Pair")
        
        # Provider-specific variables
        self.openai_translation_model = tk.StringVar(value="gpt-4")
        self.lmstudio_translation_model = tk.StringVar(value="gpt-4")
        self.translation_lmstudio_server = tk.StringVar(value="http://localhost:1234")
        self.translation_huggingface_url = tk.StringVar(value="")
        self.deepseek_translation_model = tk.StringVar(value="deepseek-chat")
        self.azure_translation_model = tk.StringVar(value="gpt-4")
        
        self.openai_mapping_model = tk.StringVar(value="gpt-4")
        self.lmstudio_mapping_model = tk.StringVar(value="gpt-4")
        self.mapping_lmstudio_server = tk.StringVar(value="http://localhost:1234")
        self.mapping_huggingface_url = tk.StringVar(value="")
        self.deepseek_mapping_model = tk.StringVar(value="deepseek-chat")
        self.azure_mapping_model = tk.StringVar(value="gpt-4")

        # Traces
        self.gui_slide_selection.trace_add("write", lambda *args: self._refresh_sidebar_config())
        
        # Method traces for summary
        self.translation_method.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.mapping_method.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.openai_translation_model.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.openai_mapping_model.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.lmstudio_translation_model.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.lmstudio_mapping_model.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.deepseek_translation_model.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.deepseek_mapping_model.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.azure_translation_model.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.azure_mapping_model.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.save_into_copy.trace_add("write", lambda *args: self._refresh_sidebar_config())
        self.gui_target_language.trace_add("write", lambda *args: self._refresh_argos_btn())
        self.gui_source_language.trace_add("write", lambda *args: self._refresh_argos_btn())
        
        
        # Azure/Advanced parameters
        self.translation_temperature = tk.DoubleVar(value=0.7)
        self.translation_frequency_penalty = tk.DoubleVar(value=0.0)
        self.translation_presence_penalty = tk.DoubleVar(value=0.0)
        self.translation_max_tokens = tk.IntVar(value=2000)
        
        self.mapping_temperature = tk.DoubleVar(value=0.7)
        self.mapping_frequency_penalty = tk.DoubleVar(value=0.0)
        self.mapping_presence_penalty = tk.DoubleVar(value=0.0)
        self.mapping_max_tokens = tk.IntVar(value=2000)
        
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

            # Load contact avatars
            avatar_size = (100, 100)
            self.avatars = {}
            for name in ["jan", "martin", "taras"]:
                try:
                    path = get_resource_path(f"slidemob/images/{name}_avatar.png")
                    img = Image.open(path)
                    img = img.resize(avatar_size, Image.Resampling.LANCZOS)
                    self.avatars[name] = ctk.CTkImage(light_image=img, dark_image=img, size=avatar_size)
                except Exception as e:
                    print(f"Warning: Could not load {name} avatar: {e}")
                    self.avatars[name] = None
        except Exception as e:
            print(f"Warning: Could not load images: {e}")
            self.app_logo = None
            self.company_logo = None
            self.avatars = {}
    
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
        self.sidebar_visible = True
        self.sidebar = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        
        # Sidebar toggle button (small button that stays visible)
        self.toggle_btn = ctk.CTkButton(
            self.main_container,
            text="☰",
            width=30,
            height=30,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray25", "gray25"),
            command=self._toggle_sidebar
        )
        self.toggle_btn.place(x=5, y=5)
        
        # App title in sidebar
        self.title_label = ctk.CTkLabel(
            self.sidebar, 
            text="SlideMob", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(20, 10))
        
        # Logo centered below title
        if self.app_logo:
            logo_label = ctk.CTkLabel(self.sidebar, image=self.app_logo, text="")
            logo_label.pack(pady=(0, 10))
        
        # Horizontal separator line
        separator = ctk.CTkFrame(self.sidebar, height=2, fg_color="gray40")
        separator.pack(fill="x", padx=15, pady=(0, 15))
        
        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("home", "Home"),
            ("processing", "Processing"),
            ("translation", "Translation"),
            ("config", "Configuration"),
            ("api_keys", "API Keys"),
            ("info", "Info"),
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
        self._create_info_tab()
        
        # Add Configuration Summary section at the bottom of sidebar
        summary_separator = ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30")
        summary_separator.pack(fill="x", padx=10, pady=(20, 10))
        
        ctk.CTkLabel(
            self.sidebar,
            text="CURRENT CONFIG",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray50"
        ).pack(anchor="w", padx=20)
        
        self.sidebar_config_label = ctk.CTkLabel(
            self.sidebar,
            text=self._get_config_summary(),
            font=ctk.CTkFont(size=11),
            text_color="gray50",
            justify="left"
        )
        self.sidebar_config_label.pack(anchor="w", padx=20, pady=(5, 20))
        
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
        
        # Slide Selection Section
        slide_section = ctk.CTkFrame(frame, corner_radius=8)
        slide_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            slide_section,
            text="Slide Selection (Optional)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        slide_row = ctk.CTkFrame(slide_section, fg_color="transparent")
        slide_row.pack(fill="x", padx=15, pady=(0, 15))
        
        self.slide_entry = ctk.CTkEntry(
            slide_row,
            textvariable=self.gui_slide_selection,
            placeholder_text="e.g., 1,3,5-7,12",
            height=40
        )
        self.slide_entry.pack(fill="x", expand=True)
        Tooltip(self.slide_entry, TOOLTIP_TEXTS["slide_selection"])
        
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
        
        # Live Processing Log
        log_section = ctk.CTkFrame(frame, corner_radius=8)
        log_section.pack(fill="both", expand=True, pady=(20, 0))
        
        ctk.CTkLabel(
            log_section,
            text="Processing Log",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.log_textbox = ctk.CTkTextbox(
            log_section,
            font=ctk.CTkFont(family="Courier", size=12),
            corner_radius=5,
            border_width=1,
            fg_color=("#f8f9fa", "#1a1a1a"),
            text_color=("black", "gray80")
        )
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.log_textbox.configure(state="disabled")
    
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
            ("save_into_copy", "Save into Copy", "overwrite"),
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

    def _create_info_tab(self):
        """Create the Info tab with uniform contact details for the team."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.tab_frames["info"] = frame
        
        # Title
        ctk.CTkLabel(
            frame,
            text="App Information",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w", pady=(0, 20))
        
        # Team Section container
        team_container = ctk.CTkFrame(frame, fg_color="transparent")
        team_container.pack(fill="x", pady=(0, 20), padx=10)
        
        # Configure 3 equal-width columns that stay uniform regardless of content size
        # Using grid_columnconfigure individually to ensure uniform group is applied correctly
        for i in range(3):
            team_container.grid_columnconfigure(i, weight=1, uniform="team_columns")
        
        team_members = [
            {
                "id": "jan",
                "name": "Jan Werth",
                "company": "Product Owner",
                "linkedin": "https://www.linkedin.com/in/jan-werth/",
            }
        ]
        
        for idx, member in enumerate(team_members):
            # The "White Box" (Contact Card)
            card = ctk.CTkFrame(
                team_container, 
                corner_radius=12,
                fg_color=("#ffffff", "#2b2b2b"), # Light mode white, dark mode gray
                border_width=1,
                border_color=("gray80", "gray30")
            )
            card.grid(row=0, column=idx, padx=10, sticky="nsew")
            
            # Sub-elements
            # Avatar
            avatar_img = self.avatars.get(member["id"])
            if avatar_img:
                avatar_label = ctk.CTkLabel(card, image=avatar_img, text="")
                avatar_label.pack(pady=(20, 10))
            else:
                # Placeholder circle
                ctk.CTkLabel(
                    card, 
                    text=member["name"][0], 
                    font=ctk.CTkFont(size=30, weight="bold"),
                    width=100,
                    height=100,
                    corner_radius=50,
                    fg_color="gray40"
                ).pack(pady=(20, 10))
            
            # Name
            ctk.CTkLabel(
                card,
                text=member["name"],
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(5, 0))
            
            # Company/Role
            ctk.CTkLabel(
                card,
                text=member["company"],
                font=ctk.CTkFont(size=14),
                text_color="gray60"
            ).pack(pady=(0, 15))
            
            # LinkedIn Button
            linked_in_btn = ctk.CTkButton(
                card,
                text="LinkedIn",
                height=30,
                width=100,
                command=lambda url=member["linkedin"]: webbrowser.open(url)
            )
            linked_in_btn.pack(pady=(0, 20))
        
        # Version or other info can go here
        version_section = ctk.CTkFrame(frame, corner_radius=8)
        version_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            version_section,
            text="Version: 1.2.0 (Modern UI)",
            font=ctk.CTkFont(size=12),
            text_color="gray50"
        ).pack(padx=15, pady=10)
        
    def _refresh_argos_btn(self):
        """Update Argos install button text based on selection."""
        source = self.gui_source_language.get()
        target = self.gui_target_language.get()
        self.argos_install_btn_text.set(f"Install {source} -> {target}")

    def install_common_argos_packs(self):
        """Install common Argos language packs."""
        from ..core_functions.translator import SlideTranslator
        
        def run_install():
            self.status_var.set("Installing common Argos languages...")
            self.root.configure(cursor="watch")
            try:
                success = SlideTranslator.install_common_argos_languages()
                self.root.after(0, lambda: self.status_var.set("Common languages installed!" if success else "Installation failed."))
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Common Argos language packs installed successfully."))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to install common language packs."))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda msg=err_msg: messagebox.showerror("Error", f"Error installing languages: {msg}"))
            finally:
                self.root.after(0, lambda: self.root.configure(cursor=""))
                self.root.after(0, self._refresh_argos_info)
        
        threading.Thread(target=run_install, daemon=True).start()

    def install_argos_languages_gui(self):
        """Callback to install specific Argos language pair."""
        from ..core_functions.translator import SlideTranslator
        
        source = self.gui_source_language.get()
        target = self.gui_target_language.get()
        
        # Simple mapping for now, ideally reused from translator logic
        # But for GUI button we just need codes.
        # Assuming we can get codes from translator instance or just search list here.
        # We need a way to get the code for the language name.
        # We can create a temporary translator or access language list if available.
        # translator.py has language_codes but it's an instance attribute.
        # We can duplicate the logic or instantiate a dummy translator.
        # Given we have json config...
        
        # Let's instantiate a dummy translator to get codes, or use hardcoded map for common ones?
        # Better: use the static mapping data if possible.
        # Actually SlideTranslator loads config_languages.json.
        
        def run_install():
            self.status_var.set(f"Installing {source} -> {target}...")
            self.root.configure(cursor="watch")
            try:
                # Helper to find code
                translator = SlideTranslator() 
                # This init might be heavy? It loads language codes.
                
                s_code = "en"
                t_code = "en"
                
                for lang in translator.language_codes.get("languages", []):
                    if lang["language"].lower().startswith(source.lower()):
                         s_code = lang["code"].split('-')[0]
                    if lang["language"].lower().startswith(target.lower()):
                         t_code = lang["code"].split('-')[0]

                success = SlideTranslator.install_argos_pair(s_code, t_code)
                
                self.root.after(0, lambda: self.status_var.set("Installation complete!" if success else "Installation failed."))
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Installed {source} -> {target} ({s_code}->{t_code})"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to install {source} -> {target}"))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda msg=err_msg: messagebox.showerror("Error", f"Error: {msg}"))
            finally:
                self.root.after(0, lambda: self.root.configure(cursor=""))
                self.root.after(0, self._refresh_argos_info)
        
        threading.Thread(target=run_install, daemon=True).start()
    
    def _refresh_argos_info(self):
        """Update the label showing installed Argos languages."""
        from ..core_functions.translator import SlideTranslator
        if hasattr(self, 'argos_installed_label'):
            installed = SlideTranslator.get_installed_argos_languages()
            if installed:
                text = "Installed pairs: " + ", ".join(installed)
            else:
                text = "No language packs installed yet."
            self.argos_installed_label.configure(text=text)

    def _check_lmstudio_connection(self, url: str) -> bool:
        """Verify that the LM Studio server is reachable."""
        try:
            # Clean up URL and ensure /v1/models is used for check
            base_url = url.rstrip('/')
            if not base_url.endswith("/v1") and "/v1/" not in base_url:
                check_url = f"{base_url}/v1/models"
            elif base_url.endswith("/v1"):
                check_url = f"{base_url}/models"
            else:
                # Fallback if URL is already complex
                check_url = base_url

            response = requests.get(check_url, timeout=3)
            return response.status_code == 200
        except Exception as e:
            print(f"LM Studio connection check failed: {e}")
            return False

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
    
    def _create_azure_config_frame(self, parent, prefix: str):
        """Replicate the Azure config frame from SettingsWindow."""
        config_frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        # Temperature
        row1 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        ctk.CTkLabel(row1, text="Temperature:", font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkEntry(row1, textvariable=getattr(self, f"{prefix}_temperature"), width=60, height=28).pack(side="left", padx=5)
        
        # Frequency Penalty
        ctk.CTkLabel(row1, text="Freq Penalty:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 0))
        ctk.CTkEntry(row1, textvariable=getattr(self, f"{prefix}_frequency_penalty"), width=60, height=28).pack(side="left", padx=5)
        
        row2 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        
        # Presence Penalty
        ctk.CTkLabel(row2, text="Pres Penalty:", font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkEntry(row2, textvariable=getattr(self, f"{prefix}_presence_penalty"), width=60, height=28).pack(side="left", padx=5)
        
        # Max Tokens
        ctk.CTkLabel(row2, text="Max Tokens:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 0))
        ctk.CTkEntry(row2, textvariable=getattr(self, f"{prefix}_max_tokens"), width=60, height=28).pack(side="left", padx=5)
        
        return config_frame

    def update_translation_frames(self, *args):
        """Show the appropriate frame based on selected translation method."""
        for frame in [
            self.openai_translation_models_frame,
            self.lmstudio_translation_frame,
            self.huggingface_translation_frame,
            self.deepseek_translation_frame,
            self.azure_translation_frame,
            self.argos_translation_frame,
        ]:
            frame.pack_forget()

        method = self.translation_method.get()
        if method == "OpenAI":
            self.openai_translation_models_frame.pack(fill="x", padx=10, pady=5)
        elif method == "LMStudio":
            self.lmstudio_translation_frame.pack(fill="x", padx=10, pady=5)
        elif method == "HuggingFace":
            self.huggingface_translation_frame.pack(fill="x", padx=10, pady=5)
        elif method == "DeepSeek":
            self.deepseek_translation_frame.pack(fill="x", padx=10, pady=5)
        elif method == "Azure OpenAI":
            self.azure_translation_frame.pack(fill="x", padx=10, pady=5)
        elif method == "Argos Translate":
            self.argos_translation_frame.pack(fill="x", padx=10, pady=5)
            self._refresh_argos_info()

    def update_mapping_frames(self, *args):
        """Show the appropriate frame based on selected mapping method."""
        for frame in [
            self.openai_mapping_models_frame,
            self.lmstudio_mapping_frame,
            self.huggingface_mapping_frame,
            self.deepseek_mapping_frame,
            self.azure_mapping_frame,
        ]:
            frame.pack_forget()

        method = self.mapping_method.get()
        if method == "OpenAI":
            self.openai_mapping_models_frame.pack(fill="x", padx=10, pady=5)
        elif method == "LMStudio":
            self.lmstudio_mapping_frame.pack(fill="x", padx=10, pady=5)
        elif method == "HuggingFace":
            self.huggingface_mapping_frame.pack(fill="x", padx=10, pady=5)
        elif method == "DeepSeek":
            self.deepseek_mapping_frame.pack(fill="x", padx=10, pady=5)
        elif method == "Azure OpenAI":
            self.azure_mapping_frame.pack(fill="x", padx=10, pady=5)

    def _create_config_tab(self):
        """Create the Configuration tab with 1:1 replication of dynamic SettingsWindow behavior."""
        # Use a scrollable frame for settings if they get long
        container = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.tab_frames["config"] = container
        
        # Title
        ctk.CTkLabel(
            container,
            text="Configuration",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # --- Translation Settings Section ---
        trans_main = ctk.CTkFrame(container, corner_radius=8)
        trans_main.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            trans_main,
            text="Translation Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 5))
        
        trans_main.columnconfigure(0, weight=0)
        trans_main.columnconfigure(1, weight=1)
        
        # Method Selection
        trans_methods = ["OpenAI", "DeepSeek", "Azure OpenAI", "HuggingFace", "LMStudio", "Argos Translate"]
        ctk.CTkLabel(trans_main, text="Method:").grid(row=1, column=0, padx=(15, 10), pady=10, sticky="w")
        trans_dropdown = ctk.CTkComboBox(
            trans_main,
            values=trans_methods,
            variable=self.translation_method,
            width=200,
            command=self.update_translation_frames
        )
        trans_dropdown.grid(row=1, column=1, padx=(0, 15), pady=10, sticky="w")
        
        # Provider-specific Model Selection Frame
        self.trans_model_container = ctk.CTkFrame(trans_main, fg_color="transparent")
        self.trans_model_container.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        # 1. OpenAI Translation
        self.openai_translation_models_frame = ctk.CTkFrame(self.trans_model_container, fg_color="transparent")
        ctk.CTkLabel(self.openai_translation_models_frame, text="Model:", width=70, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkComboBox(self.openai_translation_models_frame, values=["gpt-4", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"], variable=self.openai_translation_model).pack(side="left", padx=(5, 15))
        
        # 2. LMStudio Translation
        self.lmstudio_translation_frame = ctk.CTkFrame(self.trans_model_container, fg_color="transparent")
        ctk.CTkLabel(self.lmstudio_translation_frame, text="Model:", width=70, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkEntry(self.lmstudio_translation_frame, textvariable=self.lmstudio_translation_model, width=150).pack(side="left", padx=5)
        ctk.CTkLabel(self.lmstudio_translation_frame, text="URL:").pack(side="left", padx=(10, 0))
        ctk.CTkEntry(self.lmstudio_translation_frame, textvariable=self.translation_lmstudio_server, width=180).pack(side="left", padx=(5, 15))
        
        # 3. HuggingFace Translation
        self.huggingface_translation_frame = ctk.CTkFrame(self.trans_model_container, fg_color="transparent")
        ctk.CTkLabel(self.huggingface_translation_frame, text="URL:", width=70, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkEntry(self.huggingface_translation_frame, textvariable=self.translation_huggingface_url, width=300).pack(side="left", padx=(5, 15))
        
        # 4. DeepSeek Translation
        self.deepseek_translation_frame = ctk.CTkFrame(self.trans_model_container, fg_color="transparent")
        ctk.CTkLabel(self.deepseek_translation_frame, text="Model:", width=70, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkComboBox(self.deepseek_translation_frame, values=["deepseek-chat", "deepseek-coder", "deepseek-reasoner"], variable=self.deepseek_translation_model).pack(side="left", padx=(5, 15))
        
        # 5. Azure Translation
        self.azure_translation_frame = ctk.CTkFrame(self.trans_model_container, fg_color="transparent")
        ctk.CTkLabel(self.azure_translation_frame, text="Model:", width=70, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkEntry(self.azure_translation_frame, textvariable=self.azure_translation_model, width=150).pack(side="left", padx=5)
        self.azure_trans_params = self._create_azure_config_frame(self.azure_translation_frame, "translation")
        self.azure_trans_params.pack(fill="x", pady=5)
        
        # 6. Argos Translate
        self.argos_translation_frame = ctk.CTkFrame(self.trans_model_container, fg_color="transparent")
        ctk.CTkLabel(self.argos_translation_frame, text="Local offline translation using Argos Translate.", text_color="gray60").pack(anchor="w", padx=15)
        ctk.CTkLabel(self.argos_translation_frame, text="Source Language:", width=100, anchor="w").pack(side="left", padx=(15, 0))
        self.argos_source_dropdown = ctk.CTkComboBox(
            self.argos_translation_frame, 
            values=self.language_options, 
            variable=self.gui_source_language,
            width=200
        )
        self.argos_source_dropdown.pack(side="left", padx=(5, 15))

        self.argos_install_btn = ctk.CTkButton(
            self.argos_translation_frame, 
            textvariable=self.argos_install_btn_text,
            command=self.install_argos_languages_gui
        )
        self.argos_install_btn.pack(side="left", padx=5)
        
        self.argos_common_btn = ctk.CTkButton(
            self.argos_translation_frame,
            text="Install Common Packs",
            width=150,
            fg_color="gray50",
            hover_color="gray40",
            command=self.install_common_argos_packs
        )
        self.argos_common_btn.pack(side="left", padx=5)
        
        self.argos_installed_label = ctk.CTkLabel(
            self.argos_translation_frame, 
            text="Checking installed packs...",
            text_color="gray50",
            font=ctk.CTkFont(size=11),
            wraplength=500,
            justify="left"
        )
        self.argos_installed_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # --- Mapping Settings Section ---
        map_main = ctk.CTkFrame(container, corner_radius=8)
        map_main.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            map_main,
            text="Mapping Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 5))
        
        map_main.columnconfigure(0, weight=0)
        map_main.columnconfigure(1, weight=1)
        
        # Method Selection
        ctk.CTkLabel(map_main, text="Method:").grid(row=1, column=0, padx=(15, 10), pady=10, sticky="w")
        map_dropdown = ctk.CTkComboBox(
            map_main,
            values=trans_methods,
            variable=self.mapping_method,
            width=200,
            command=self.update_mapping_frames
        )
        map_dropdown.grid(row=1, column=1, padx=(0, 15), pady=10, sticky="w")
        
        # Provider-specific Model Selection Frame
        self.map_model_container = ctk.CTkFrame(map_main, fg_color="transparent")
        self.map_model_container.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        # 1. OpenAI Mapping
        self.openai_mapping_models_frame = ctk.CTkFrame(self.map_model_container, fg_color="transparent")
        ctk.CTkLabel(self.openai_mapping_models_frame, text="Model:", width=70, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkComboBox(self.openai_mapping_models_frame, values=["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"], variable=self.openai_mapping_model).pack(side="left", padx=(5, 15))
        
        # 2. LMStudio Mapping
        self.lmstudio_mapping_frame = ctk.CTkFrame(self.map_model_container, fg_color="transparent")
        ctk.CTkLabel(self.lmstudio_mapping_frame, text="Model:", width=70, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkEntry(self.lmstudio_mapping_frame, textvariable=self.lmstudio_mapping_model, width=150).pack(side="left", padx=5)
        ctk.CTkLabel(self.lmstudio_mapping_frame, text="URL:").pack(side="left", padx=(10, 0))
        ctk.CTkEntry(self.lmstudio_mapping_frame, textvariable=self.mapping_lmstudio_server, width=180).pack(side="left", padx=(5, 15))
        
        # 3. HuggingFace Mapping
        self.huggingface_mapping_frame = ctk.CTkFrame(self.map_model_container, fg_color="transparent")
        ctk.CTkLabel(self.huggingface_mapping_frame, text="URL:", width=70, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkEntry(self.huggingface_mapping_frame, textvariable=self.mapping_huggingface_url, width=300).pack(side="left", padx=(5, 15))
        
        # 4. DeepSeek Mapping
        self.deepseek_mapping_frame = ctk.CTkFrame(self.map_model_container, fg_color="transparent")
        ctk.CTkLabel(self.deepseek_mapping_frame, text="Model:", width=70, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkComboBox(self.deepseek_mapping_frame, values=["deepseek-chat", "deepseek-coder", "deepseek-reasoner"], variable=self.deepseek_mapping_model).pack(side="left", padx=(5, 15))
        
        # 5. Azure Mapping
        self.azure_mapping_frame = ctk.CTkFrame(self.map_model_container, fg_color="transparent")
        ctk.CTkLabel(self.azure_mapping_frame, text="Model:", width=70, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkEntry(self.azure_mapping_frame, textvariable=self.azure_mapping_model, width=150).pack(side="left", padx=5)
        self.azure_map_params = self._create_azure_config_frame(self.azure_mapping_frame, "mapping")
        self.azure_map_params.pack(fill="x", pady=5)
        
        # Save button
        save_btn = ctk.CTkButton(
            container,
            text="Save Configuration",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._save_config_settings
        )
        save_btn.pack(anchor="w", pady=(10, 20), padx=5)

        # Initial frame update
        self.update_translation_frames()
        self.update_mapping_frames()
    
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
        save_btn.pack(anchor="w", pady=(10, 0), padx=5)
    
    def _save_config_settings(self, show_message=True):
        """Save configuration settings by mapping provider-specific variables to main variables."""
        # Mapping selected method's values to main class variables
        trans_method = self.translation_method.get()
        if trans_method == "OpenAI":
            self.translation_model = self.openai_translation_model.get()
        elif trans_method == "LMStudio":
            self.translation_model = self.lmstudio_translation_model.get()
            self.translation_api_url = self.translation_lmstudio_server.get()
        elif trans_method == "HuggingFace":
            self.translation_api_url = self.translation_huggingface_url.get()
        elif trans_method == "DeepSeek":
            self.translation_model = self.deepseek_translation_model.get()
        elif trans_method == "Azure OpenAI":
            self.translation_model = self.azure_translation_model.get()
            # Pull URL from .env (Azure Endpoint)
            self.translation_api_url = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        
        map_method = self.mapping_method.get()
        if map_method == "OpenAI":
            self.mapping_model = self.openai_mapping_model.get()
        elif map_method == "LMStudio":
            self.mapping_model = self.lmstudio_mapping_model.get()
            self.mapping_api_url = self.mapping_lmstudio_server.get()
        elif map_method == "HuggingFace":
            self.mapping_api_url = self.mapping_huggingface_url.get()
        elif map_method == "DeepSeek":
            self.mapping_model = self.deepseek_mapping_model.get()
        elif map_method == "Azure OpenAI":
            self.mapping_model = self.azure_mapping_model.get()
            self.mapping_api_url = os.getenv("AZURE_OPENAI_ENDPOINT", "")

        self.save_gui_config(save_all=True)
        self._refresh_sidebar_config()
        if show_message:
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
    
    def _get_config_summary(self) -> str:
        """Generate a compact summary of current configuration for display."""
        lang = self.gui_target_language.get()
        strategy = self.translation_strategy.get() or "None"
        
        # Get active models
        trans_method = self.translation_method.get()
        if trans_method == "OpenAI":
            trans_model = self.openai_translation_model.get()
        elif trans_method == "LMStudio":
            trans_model = f"LMS:{self.lmstudio_translation_model.get()}"
        elif trans_method == "DeepSeek":
            trans_model = f"DS:{self.deepseek_translation_model.get()}"
        elif trans_method == "Azure OpenAI":
            trans_model = f"Azure:{self.azure_translation_model.get()}"
        elif trans_method == "Argos Translate":
            trans_model = "Argos (Local)"
        else:
            trans_model = "HF"

        map_method = self.mapping_method.get()
        if map_method == "OpenAI":
            map_model = self.openai_mapping_model.get()
        elif map_method == "LMStudio":
            map_model = f"LMS:{self.lmstudio_mapping_model.get()}"
        elif map_method == "DeepSeek":
            map_model = f"DS:{self.deepseek_mapping_model.get()}"
        elif map_method == "Azure OpenAI":
            map_model = f"Azure:{self.azure_mapping_model.get()}"
        else:
            map_model = "HF"

        into_copy = "Yes" if self.save_into_copy.get() else "No"
        slides = self.gui_slide_selection.get() or "All"
        
        return (
            f"Language: {lang}\n"
            f"Strategy: {strategy}\n"
            f"Trans: {trans_model}\n"
            f"Map: {map_model}\n"
            f"Slides: {slides}\n"
            f"Save into Copy: {into_copy}"
        )

    def _toggle_sidebar(self):
        """Toggle sidebar visibility."""
        if self.sidebar_visible:
            self.sidebar.pack_forget()
            self.sidebar_visible = False
            self.toggle_btn.configure(text="☰")
            # Move toggle button to corner
            self.toggle_btn.place(x=5, y=5)
        else:
            self.sidebar.pack(side="left", fill="y", padx=(0, 10), before=self.content_area)
            self.sidebar_visible = True
            self.toggle_btn.configure(text="✕")
            # Move toggle button to stay visible or inside sidebar
            self.toggle_btn.place(x=5, y=5)
    
    def _refresh_sidebar_config(self):
        """Refresh the config summary on the sidebar."""
        if hasattr(self, 'sidebar_config_label'):
            self.sidebar_config_label.configure(text=self._get_config_summary())

    def _log_to_gui(self, original, transformed):
        """Callback to log processing steps to the Home tab textbox."""
        if hasattr(self, 'log_textbox'):
            def update():
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", f"--- {original[:30]}... ---\n")
                self.log_textbox.insert("end", f"→ {transformed}\n\n")
                self.log_textbox.see("end")
                self.log_textbox.configure(state="disabled")
            
            self.root.after(0, update)

    def _clear_log(self):
        """Clear the log textbox."""
        if hasattr(self, 'log_textbox'):
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("1.0", "end")
            self.log_textbox.configure(state="disabled")
    
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
        self.root.after(0, lambda: self.status_var.set(f"Translating slide {current} of {total} ({slide_name})"))
    
    def process_presentation(self):
        if not self.gui_pptx_path.get() or not self.gui_output_path.get():
            messagebox.showerror("Error", "Please select both input file and output location")
            return
        
        self.processing = True
        self.stop_requested = False
        self.process_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # Connection Checks (still on main thread for immediate feedback)
        try:
            # Check translation method
            if self.translate_var.get() and self.translation_method.get() == "LMStudio":
                url = self.translation_lmstudio_server.get()
                if not self._check_lmstudio_connection(url):
                    messagebox.showerror("Error", f"Could not connect to LM Studio translation server at {url}. Make sure LM Studio is running and the server is started.")
                    self.stop_processing()
                    return

            # Check mapping method
            if self.mapping_method.get() == "LMStudio":
                url = self.mapping_lmstudio_server.get()
                if not self._check_lmstudio_connection(url):
                    messagebox.showerror("Error", f"Could not connect to LM Studio mapping server at {url}. Make sure LM Studio is running and the server is started.")
                    self.stop_processing()
                    return
            
            # Additional check for model name validity
            import re
            def is_valid_lm_model(m):
                m_low = m.lower()
                return any(x in m_low for x in ["gpt", "openai", "llama", "deepseek"]) and m_low != "unknown"

            if self.translate_var.get() and self.translation_method.get() == "LMStudio":
                model_name = self.lmstudio_translation_model.get()
                if not is_valid_lm_model(model_name):
                    messagebox.showerror("Error", f"Invalid translation model name: '{model_name}'.\n\nPlease ensure the model name is correctly copied from LM Studio and contains one of these keywords: gpt, openai, llama, or deepseek.")
                    self.stop_processing()
                    return

            if self.mapping_method.get() == "LMStudio":
                model_name = self.lmstudio_mapping_model.get()
                if not is_valid_lm_model(model_name):
                    messagebox.showerror("Error", f"Invalid mapping model name: '{model_name}'.\n\nPlease ensure the model name is correctly copied from LM Studio and contains one of these keywords: gpt, openai, llama, or deepseek.")
                    self.stop_processing()
                    return
        except Exception as e:
            messagebox.showerror("Error", f"Early connection check failed: {e}")
            self.stop_processing()
            return

        # Prepare settings on main thread
        self._save_config_settings(show_message=False)
        self.save_gui_config()
        self._refresh_sidebar_config()
        self._clear_log()
        
        # Collect values needed for PathManager and config
        pptx_path = self.gui_pptx_path.get()
        output_path = self.gui_output_path.get()
        overwrite = not self.save_into_copy.get()
        target_lang = self.gui_target_language.get()
        style_instr = self.gui_style_instructions.get()
        slide_selection = self.gui_slide_selection.get().strip()
        
        # Validate slide selection if provided
        if slide_selection:
            try:
                import zipfile
                with zipfile.ZipFile(pptx_path, 'r') as z:
                    slide_files = [f for f in z.namelist() if f.startswith("ppt/slides/slide") and f.endswith(".xml")]
                    all_slide_nums = set()
                    for f in slide_files:
                        num_part = f[len("ppt/slides/slide"):-4]
                        if num_part.isdigit():
                            all_slide_nums.add(int(num_part))
                
                selected_nums = PowerpointPipeline.parse_slide_selection(slide_selection)
                invalid_nums = selected_nums - all_slide_nums
                
                if invalid_nums:
                    messagebox.showerror(
                        "Invalid Slide Selection",
                        f"The following slide numbers do not exist in the presentation: {sorted(list(invalid_nums))}\n"
                        f"Total slides available: {len(all_slide_nums)}"
                    )
                    self.stop_processing()
                    return
            except Exception as e:
                print(f"Warning: Could not pre-validate slide selection: {e}")

        # Start processing in a separate thread
        thread = threading.Thread(
            target=self._run_processing_thread,
            args=(pptx_path, output_path, overwrite, target_lang, style_instr, slide_selection, self.gui_source_language.get())
        )
        thread.daemon = True
        thread.start()

    def _run_processing_thread(self, pptx_path, output_path, overwrite, target_lang, style_instr, slide_selection, source_lang=None):
        """Core processing logic to be run in a separate thread."""
        try:
            path_manager = PathManager(
                pptx_path,
                output_path,
                overwrite=overwrite
            )
            config = create_config(
                path_manager=path_manager,
                target_language=target_lang,
                selected_slides=slide_selection,
                source_language=source_lang
            )
            
            # Sync internal pipeline attributes with the new config
            self.pipeline_config = config
            self.get_config()
            
            if self.stop_requested:
                raise Exception("Processing stopped by user")
            
            if self.extract_var.get():
                self.root.after(0, lambda: self.status_var.set("Extracting PPTX..."))
                # Create a local pipeline instance for extraction since we no longer inherit it
                extraction_pipeline = PowerpointPipeline(pipeline_config=config)
                success = extraction_pipeline.extract_pptx()
                if not success:
                    raise Exception("Extraction failed")
            
            if self.stop_requested:
                raise Exception("Processing stopped by user")
            
            if self.polish_var.get():
                self.root.after(0, lambda: self.status_var.set("Polishing content..."))
                polisher = PowerPointPolisher(
                    Further_StyleInstructions=style_instr,
                    fresh_extract=not self.extract_var.get(),
                    log_callback=self._log_to_gui,
                    pipeline_config=config,
                )
                success = polisher.polish_presentation()
                if not success:
                    raise Exception("Polishing failed")
            
            if self.stop_requested:
                raise Exception("Processing stopped by user")
            
            if self.translate_var.get():
                self.root.after(0, lambda: self.status_var.set("Starting translation..."))
                translator = PowerPointTranslator(
                    progress_callback=self.update_translation_progress,
                    stop_check_callback=lambda: self.stop_requested,
                    log_callback=self._log_to_gui,
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
                self.root.after(0, lambda: self.status_var.set("Merging similar runs..."))
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
            
            self.root.after(0, lambda: self.status_var.set("Processing complete!"))
            
            output_file = path_manager.output_pptx
            output_folder = path_manager.output_dir
            
            success_msg = (
                f"PowerPoint processing completed successfully!\n\n"
                f"Filename: {os.path.basename(output_file)}\n"
                f"Folder: {output_folder}"
            )
            self.root.after(0, lambda: messagebox.showinfo("Success", success_msg))
        
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.status_var.set(f"Error: {msg}"))
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", f"An error occurred: {msg}"))
            logging.exception("Error in process_presentation thread")
        
        finally:
            def reset_ui():
                self.processing = False
                self.stop_requested = False  # Reset stop flag for next run
                self.process_btn.configure(state="normal")
                self.stop_btn.configure(state="disabled")
            self.root.after(0, reset_ui)
    
    def stop_processing(self):
        self.stop_requested = True
        self.status_var.set("Stopping...")
    
    def load_gui_config(self):
        try:
            config_path = get_user_config_path()
            if os.path.exists(config_path):
                with open(config_path) as f:
                    config = json.load(f)
                
                self.gui_pptx_path.set(config.get("pptx_path", ""))
                self.gui_output_path.set(config.get("output_path", ""))
                self.gui_target_language.set(config.get("target_language", "English"))
                self.gui_source_language.set(config.get("source_language", "English"))
                self.extract_var.set(config.get("extract_pptx", True))
                self.merge_runs_var.set(config.get("pre_merge", False))
                self.polish_var.set(config.get("polish_content", False))
                self.translate_var.set(config.get("translate_content", True))
                self.update_language.set(config.get("update_language", False))
                self.reduce_slides.set(config.get("reduce_slides", False))
                self.translation_method.set(config.get("translation_method", "OpenAI"))
                self.gui_style_instructions.set(config.get("style_instructions", ""))
                self.mapping_method.set(config.get("mapping_method", "OpenAI"))
                self.translation_strategy.set(config.get("translation_strategy", ""))
                
                # Handle legacy overwrite_file
                if "save_into_copy" in config:
                    self.save_into_copy.set(config.get("save_into_copy", True))
                elif "overwrite_file" in config:
                    # Invert old overwrite logic: Overwrite=True -> SaveIntoCopy=False
                    self.save_into_copy.set(not config.get("overwrite_file"))
                else:
                    self.save_into_copy.set(True)
                
                self.translation_model = config.get("translation_model", "gpt-4")
                self.mapping_model = config.get("mapping_model", "gpt-4")
                self.translation_api_url = config.get("translation_api_url", "http://localhost:1234")
                self.mapping_api_url = config.get("mapping_api_url", "http://localhost:1234")
                
                # Provider specific
                self.openai_translation_model.set(config.get("openai_translation_model", "gpt-4"))
                self.lmstudio_translation_model.set(config.get("lmstudio_translation_model", "gpt-4"))
                self.translation_lmstudio_server.set(config.get("translation_lmstudio_server", "http://localhost:1234"))
                self.translation_huggingface_url.set(config.get("translation_huggingface_url", ""))
                self.deepseek_translation_model.set(config.get("deepseek_translation_model", "deepseek-chat"))
                self.azure_translation_model.set(config.get("azure_translation_model", "gpt-4"))
                
                self.openai_mapping_model.set(config.get("openai_mapping_model", "gpt-4o-mini"))
                self.lmstudio_mapping_model.set(config.get("lmstudio_mapping_model", "gpt-4"))
                self.mapping_lmstudio_server.set(config.get("mapping_lmstudio_server", "http://localhost:1234"))
                self.mapping_huggingface_url.set(config.get("mapping_huggingface_url", ""))
                self.deepseek_mapping_model.set(config.get("deepseek_mapping_model", "deepseek-chat"))
                self.azure_mapping_model.set(config.get("azure_mapping_model", "gpt-4"))
                
                # Azure parameters
                self.translation_temperature.set(config.get("translation_temperature", 0.7))
                self.translation_frequency_penalty.set(config.get("translation_frequency_penalty", 0.0))
                self.translation_presence_penalty.set(config.get("translation_presence_penalty", 0.0))
                self.translation_max_tokens.set(config.get("translation_max_tokens", 2000))
                
                self.mapping_temperature.set(config.get("mapping_temperature", 0.7))
                self.mapping_frequency_penalty.set(config.get("mapping_frequency_penalty", 0.0))
                self.mapping_presence_penalty.set(config.get("mapping_presence_penalty", 0.0))
                self.mapping_max_tokens.set(config.get("mapping_max_tokens", 2000))
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
                    "source_language": self.gui_source_language.get(),
                    "translation_method": self.translation_method.get(),
                    "mapping_method": self.mapping_method.get(),
                    "style_instructions": self.gui_style_instructions.get(),
                    "translation_model": self.translation_model,
                    "mapping_model": self.mapping_model,
                    "translation_api_url": self.translation_api_url,
                    "mapping_api_url": self.mapping_api_url,
                    "translation_strategy": self.translation_strategy.get(),
                    "save_into_copy": self.save_into_copy.get(),
                    
                    # Provider specific
                    "openai_translation_model": self.openai_translation_model.get(),
                    "lmstudio_translation_model": self.lmstudio_translation_model.get(),
                    "translation_lmstudio_server": self.translation_lmstudio_server.get(),
                    "translation_huggingface_url": self.translation_huggingface_url.get(),
                    "deepseek_translation_model": self.deepseek_translation_model.get(),
                    "azure_translation_model": self.azure_translation_model.get(),
                    
                    "openai_mapping_model": self.openai_mapping_model.get(),
                    "lmstudio_mapping_model": self.lmstudio_mapping_model.get(),
                    "mapping_lmstudio_server": self.mapping_lmstudio_server.get(),
                    "mapping_huggingface_url": self.mapping_huggingface_url.get(),
                    "deepseek_mapping_model": self.deepseek_mapping_model.get(),
                    "azure_mapping_model": self.azure_mapping_model.get(),
                    
                    # Azure parameters
                    "translation_temperature": self.translation_temperature.get(),
                    "translation_frequency_penalty": self.translation_frequency_penalty.get(),
                    "translation_presence_penalty": self.translation_presence_penalty.get(),
                    "translation_max_tokens": self.translation_max_tokens.get(),
                    
                    "mapping_temperature": self.mapping_temperature.get(),
                    "mapping_frequency_penalty": self.mapping_frequency_penalty.get(),
                    "mapping_presence_penalty": self.mapping_presence_penalty.get(),
                    "mapping_max_tokens": self.mapping_max_tokens.get(),
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
            elif key == "save_into_copy":
                self.save_into_copy.set(value)
        
        # Update display
        if hasattr(self, 'config_info_label'):
            info_text = f"Translation: {self.translation_method.get()} | Mapping: {self.mapping_method.get()}"
            self.config_info_label.configure(text=info_text)


if __name__ == "__main__":
    root = ctk.CTk()
    app = SlideMobGUI(root)
    root.mainloop()
