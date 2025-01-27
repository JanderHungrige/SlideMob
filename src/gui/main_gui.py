import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import logging
from ttkthemes import ThemedStyle  
import traceback

from core_functions.base_class import PowerpointPipeline
from pipelines.translator_pipeline import PowerPointTranslator
from pipelines.polisher_pipeline import PowerPointPolisher
from utils.errorhandler import setup_error_logging
from utils.config import create_config
from utils.path_manager import PathManager
from pipelines.run_merger_pipeline import PowerPointRunMerger
from gui.settings_window import SettingsWindow

class SlideMobGUI(PowerpointPipeline):
    def __init__(self, root):
        super().__init__()
        self.root = root
        tk.Tk.report_callback_exception = self.show_error
        self.root.title("SlideMob PowerPoint Processor")
        self.root.geometry("700x790")
        
        # Initialize LMStudio settings

        
        # Load language codes first
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_languages.json")) as f:
            language_config = json.load(f)
        self.language_options = [lang["language"].split(" (")[0] for lang in language_config["languages"]]
        
        # Initialize tk variables
        self.gui_pptx_path = tk.StringVar(self.root)
        self.gui_output_path = tk.StringVar(self.root)
        self.gui_target_language = tk.StringVar(self.root, value="English")
        self.gui_style_instructions = tk.StringVar(self.root)
        self.translation_method = tk.StringVar(self.root, value="OpenAI")
        self.mapping_method = tk.StringVar(self.root, value="OpenAI")
        self.openai_model = tk.StringVar(self.root, value="gpt-4")
        self.mapping_model = tk.StringVar(self.root, value="gpt-4")
        
        self.lmstudio_server = "http://localhost:1234"
        self.lmstudio_model_api = ""
        
        # Update the parent class variables whenever GUI vars change
        self.gui_pptx_path.trace_add('write', self._update_pptx_path)
        self.gui_output_path.trace_add('write', self._update_output_path)
        
        # Checkboxes
        self.extract_var = tk.BooleanVar(value=True)
        self.polish_var = tk.BooleanVar(value=False)
        self.translate_var = tk.BooleanVar(value=True)
        self.update_language = tk.BooleanVar(value=False)
        self.reduce_slides = tk.BooleanVar(value=False)
        self.merge_runs_var = tk.BooleanVar(value=False)
        
        # Load the logo image
        current_dir = os.path.dirname(__file__)
        company_logo_path = os.path.join(current_dir, "../gui/assets/eraneos_bg Small.png")
        company_logo_path = os.path.abspath(company_logo_path)
        self.company_logo_image = tk.PhotoImage(file=company_logo_path)

        #Load Icon 
        app_logo_path = os.path.join(current_dir, "../gui/assets/doppelfahreimer Small Small.png")
        app_logo_path = os.path.abspath(app_logo_path)
        self.app_logo_image = tk.PhotoImage(file=app_logo_path)

        # Load Settings Icon
        settings_icon_path = os.path.join(current_dir, "../gui/assets/Setting_icon.png")
        settings_icon_path = os.path.abspath(settings_icon_path)
        print(f"Looking for settings icon at: {settings_icon_path}")  # Debug print
        self.settings_icon_image = tk.PhotoImage(file=settings_icon_path)

        # Create a bottom frame matching theme background
        bottom_frame = tk.Frame(self.root, bg='#464646')  # equilux theme background color
        bottom_frame.pack(side="bottom", fill="x", pady=(0, 4))

        # Add the app logo to the lower left corner
        canvas_width = self.app_logo_image.width() + 8
        canvas_height = self.app_logo_image.height() + 8
        self.app_logo_canvas = tk.Canvas(bottom_frame, width=canvas_width, height=canvas_height, 
                                       highlightthickness=0, bg='#464646')
        self.app_logo_canvas.create_image(
            canvas_width//2,
            canvas_height//2,
            anchor="center",
            image=self.app_logo_image
        )
        self.app_logo_canvas.pack(side="left", padx=4)

        # Add spacing between logos with matching background
        tk.Frame(bottom_frame, bg='#464646').pack(side="left", fill="x", expand=True)

        # Add the company logo to the lower right corner
        canvas_width = self.company_logo_image.width() + 8
        self.logo_canvas = tk.Canvas(bottom_frame, width=canvas_width, height=canvas_height,
                                   highlightthickness=0, bg='#464646')
        self.logo_canvas.create_image(
            canvas_width//2, 
            canvas_height//2, 
            anchor="center", 
            image=self.company_logo_image
        )
        self.logo_canvas.pack(side="right", padx=4)

        # Initialize error logging
        setup_error_logging()
        
        # Add help text descriptions
        self.help_texts = {
            "all": """Available Options:

• Extract PPTX: Extracts text content from the PowerPoint file for processing.

• Pre Merge: Due to ppt stuff, paragraphs can be split in runs which schould not be split. This will premerge those runs and could increase the quality of e.g., the translation.

• Polish Content: Improves the writing style and formatting of the content.

• Translate Content: Translates the content to the selected target language.

• Update PPTX Language: Updates PowerPoint's internal language settings to match the target language."""
        }

        self.translation_method = tk.StringVar(value="OpenAI")

        self.processing = False
        self.stop_requested = False

        self.create_widgets()

        self.load_gui_config()

    def _update_pptx_path(self, *args):
        """Update the parent class pptx_path when GUI var changes"""
        self.pptx_path = self.gui_pptx_path.get()

    def _update_output_path(self, *args):
        """Update the parent class output_path when GUI var changes"""
        self.output_path = self.gui_output_path.get()
        
    def create_widgets(self):
        # Create and configure styles
        style = ThemedStyle(self.root)
        style.set_theme('equilux')
        style.configure(
            'Blue.TButton',
            background='#0052cc',
            foreground='white',
            padding=(10, 5)
        )
    
        style.map('Blue.TButton',
            background=[
                ('pressed', '#003d99'), 
                ('active', '#0052cc'),
                ('!disabled', '#0052cc')
            ],
            foreground=[
                ('!disabled', 'white'),
                ('disabled', '#999999')
            ]
        )
        # Create a main container frame
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)
        
        # Create a canvas with scrollbar
        self.canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        # Create main frame that will contain all widgets
        self.scrollable_frame = ttk.Frame(self.canvas)
        
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
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas for the frame
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the scrollbar first, then the canvas
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Update idletasks to ensure proper initial layout
        self.root.update_idletasks()

        # File Selection Frame
        file_frame = ttk.LabelFrame(self.scrollable_frame, text="File Selection", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(file_frame, text="PowerPoint File:").pack(anchor="w")
        ttk.Entry(file_frame, textvariable=self.gui_pptx_path, width=50).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_pptx,style='Blue.TButton').pack(side="left")
        
        # Output Selection Frame
        output_frame = ttk.LabelFrame(self.scrollable_frame, text="Output Location", padding=10)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_frame, text="Output Folder:").pack(anchor="w")
        ttk.Entry(output_frame, textvariable=self.gui_output_path, width=50).pack(side="left", padx=5)
        ttk.Button(output_frame, text="Browse", command=self.browse_output,style='Blue.TButton').pack(side="left")
        
        # Options Frame with help button
        options_frame = ttk.LabelFrame(self.scrollable_frame, text="Processing Options", padding=10)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        # Create a frame for the help button
        help_button_frame = ttk.Frame(options_frame)
        help_button_frame.pack(anchor="e", padx=5, pady=5)
        ttk.Button(help_button_frame, text="?", width=2, command=lambda: self.show_help("all"), style='Blue.TButton').pack(side="right")
        
        # Checkboxes (without individual help buttons)
        ttk.Checkbutton(options_frame, text="Extract PPTX", variable=self.extract_var).pack(anchor="w")
        ttk.Checkbutton(options_frame, text="Pre Merge", variable=self.merge_runs_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Polish Content", variable=self.polish_var).pack(anchor="w")
        
        # Translation checkbox frame
        translate_checkbox_frame = ttk.Frame(options_frame)
        translate_checkbox_frame.pack(fill="x", anchor="w")
        ttk.Checkbutton(translate_checkbox_frame, text="Translate Content", variable=self.translate_var).pack(side="left")
        ttk.Checkbutton(translate_checkbox_frame, text="Update PPTX Language", variable=self.update_language).pack(side="left", padx=(20, 0))
        ttk.Checkbutton(translate_checkbox_frame, text="Reduce Slides", variable=self.reduce_slides).pack(side="left", padx=(20, 0))
        
        # Translation Options
        translation_frame = ttk.Frame(options_frame)
        translation_frame.pack(fill="x", pady=5)
        
        # Language selection row
        language_row = ttk.Frame(translation_frame)
        language_row.pack(fill="x", pady=(0, 5))
        
        ttk.Label(language_row, text="Target Language:").pack(side="left")
        language_dropdown = ttk.Combobox(language_row, textvariable=self.gui_target_language, values=self.language_options)
        language_dropdown.pack(side="left", padx=5)
        
        # Methods row
        methods_row = ttk.Frame(translation_frame)
        methods_row.pack(fill="x")
        
        # Translation Method
        ttk.Label(methods_row, text="Translation Method:").pack(side="left")
        self.translation_method_label = ttk.Label(methods_row, textvariable=self.translation_method)
        self.translation_method_label.pack(side="left", padx=5)
        
        # Mapping Method
        ttk.Label(methods_row, text="Mapping Method:").pack(side="left", padx=(20, 0))
        self.mapping_method_label = ttk.Label(methods_row, textvariable=self.mapping_method)
        self.mapping_method_label.pack(side="left", padx=5)

        # Style Instructions
        style_frame = ttk.LabelFrame(self.scrollable_frame, text="Style Instructions", padding=10)
        style_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(style_frame, text="Additional Style Instructions:").pack(anchor="w")
        style_entry = ttk.Entry(style_frame, textvariable=self.gui_style_instructions, width=50)
        style_entry.pack(fill="x", pady=5)
        
        # Process and Stop Buttons
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(pady=20)

        self.process_button = ttk.Button(button_frame, text="Process PowerPoint", 
                                       command=self.process_presentation, style='Blue.TButton')
        self.process_button.pack(side="left", padx=10, pady=10)

        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                     command=self.stop_processing, style='Blue.TButton',
                                     width=5)
        self.stop_button.pack(side="left", padx=10, pady=10)
        self.stop_button.configure(state="disabled")  # Initially disabled
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.scrollable_frame, textvariable=self.status_var).pack()
        
        # Create settings button in top right
        settings_frame = ttk.Frame(self.scrollable_frame)
        settings_frame.pack(anchor="ne", padx=5, pady=5)
        settings_button = ttk.Button(settings_frame, image=self.settings_icon_image, 
                                   command=self.open_settings, style='Blue.TButton')
        settings_button.pack(side="right")

    def browse_pptx(self):
        filename = filedialog.askopenfilename(
            title="Select PowerPoint File",
            filetypes=[("PowerPoint files", "*.pptx")]
        )
        if filename:
            self.gui_pptx_path.set(filename)
            
    def browse_output(self):
        if self.gui_pptx_path.get():
            startfolder = os.path.dirname(self.gui_pptx_path.get())
        else:
            startfolder = os.getcwd()
        folder = filedialog.askdirectory(title="Select Output Folder", initialdir=startfolder)
        if folder:
            self.gui_output_path.set(folder)
            
    def update_translation_progress(self, slide_name, current, total):
        """Update the status text with current translation progress"""
        self.status_var.set(f"Translating slide {current} of {total} ({slide_name})")
        self.root.update()

    def process_presentation(self):
        if not self.pptx_path or not self.output_path:
            messagebox.showerror("Error", "Please select both input file and output location")
            return
        
        # Set processing state
        self.processing = True
        self.stop_requested = False
        self.process_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.root.update()
        
        try:
            # Save GUI config as soon as process button is clicked
            self.save_gui_config()
            
            path_manager = PathManager(self.pptx_path)
            config = create_config(
                path_manager=path_manager,
                target_language=self.gui_target_language.get()
            )

            # Check for stop request between each major step
            if self.stop_requested:
                raise Exception("Processing stopped by user")

            # Extract
            if self.extract_var.get():
                self.status_var.set("Extracting PPTX...")
                self.root.update()
                
                success = self.extract_pptx()
                if not success:
                    raise Exception("Extraction failed")

            if self.stop_requested:
                raise Exception("Processing stopped by user")

            # Polish
            if self.polish_var.get():
                self.status_var.set("Polishing content...")
                self.root.update()
                
                polisher = PowerPointPolisher(
                    Further_StyleInstructions=self.gui_style_instructions.get(),
                    fresh_extract=not self.extract_var.get()
                )
                success = polisher.polish_presentation()
                if not success:
                    raise Exception("Polishing failed")

            if self.stop_requested:
                raise Exception("Processing stopped by user")

            # Translate
            if self.translate_var.get():
                self.status_var.set("Starting translation...")
                self.root.update()
                
                translator = PowerPointTranslator(
                    target_language=self.gui_target_language.get(),
                    Further_StyleInstructions=self.gui_style_instructions.get(),
                    update_language=self.update_language.get(),
                    fresh_extract=not (self.extract_var.get() or self.polish_var.get()),
                    translation_method=self.translation_method.get(),
                    mapping_method=self.mapping_method.get()
                )
                success = translator.translate_presentation(
                    progress_callback=self.update_translation_progress,
                    stop_check_callback=lambda: self.stop_requested
                )
                if not success:
                    if self.stop_requested:
                        raise Exception("Processing stopped by user")
                    print("Full traceback:")
                    print(traceback.format_exc())
                    raise Exception("Translation failed")

            if self.stop_requested:
                raise Exception("Processing stopped by user")

            # Add run merging step
            if self.merge_runs_var.get():
                self.status_var.set("Merging similar runs...")
                self.root.update()
                
                merger = PowerPointRunMerger(
                    fresh_extract=not (self.extract_var.get() or 
                                     self.polish_var.get() or 
                                     self.translate_var.get())
                )
                success = merger.merge_runs_in_presentation()
                if not success:
                    raise Exception("Run merging failed")

            self.status_var.set("Processing complete!")
            messagebox.showinfo("Success", "PowerPoint processing completed successfully!")
            
        except Exception as e:
            self.status_var.set(f"Error occurred: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}\nCheck error_logs folder for details.")
            logging.exception("Error in process_presentation")
            raise e

    def show_help(self, help_key):
        messagebox.showinfo("Processing Options Help", self.help_texts[help_key])

    def load_gui_config(self):
        """Load GUI configuration from config file"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_gui.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                # Add loading of OpenAI model
                self.openai_model = config.get('openai_model', 'gpt-4')
                
                # Add loading of LMStudio settings
                self.lmstudio_server = config.get('lmstudio_server', 'http://localhost:1234')
                self.lmstudio_model_api = config.get('lmstudio_model_api', '')
                
                # Set GUI variables from config
                self.extract_var.set(config.get('extract_pptx', True))
                self.merge_runs_var.set(config.get('pre_merge', False))
                self.polish_var.set(config.get('polish_content', False))
                self.translate_var.set(config.get('translate_content', True))
                self.update_language.set(config.get('update_language', False))
                self.reduce_slides.set(config.get('reduce_slides', False))
                self.gui_target_language.set(config.get('target_language', 'English'))
                self.translation_method.set(config.get('translation_method', 'OpenAI'))
                self.gui_style_instructions.set(config.get('style_instructions', ''))
                self.mapping_method.set(config.get('mapping_method', 'OpenAI'))
                
                # Load path settings if they exist
                if 'pptx_path' in config:
                    self.gui_pptx_path.set(config.get('pptx_path'))
                if 'output_folder' in config:
                    self.gui_output_path.set(config.get('output_folder'))
                
        except Exception as e:
            logging.warning(f"Could not load GUI config: {str(e)}")

    def save_gui_config(self):
        """Save current GUI configuration to config file"""
        try:
            config = {
                'extract_pptx': self.extract_var.get(),
                'pre_merge': self.merge_runs_var.get(),
                'polish_content': self.polish_var.get(),
                'translate_content': self.translate_var.get(),
                'update_language': self.update_language.get(),
                'reduce_slides': self.reduce_slides.get(),
                'target_language': self.gui_target_language.get(),
                'translation_method': self.translation_method.get(),
                'mapping_method': self.mapping_method.get(),
                'style_instructions': self.gui_style_instructions.get(),
                'pptx_path': self.gui_pptx_path.get(),
                'output_folder': self.gui_output_path.get(),
                'openai_model': self.openai_model,
                'lmstudio_server': self.lmstudio_server,
                'lmstudio_model_api': self.lmstudio_model_api
            }
            
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_gui.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.warning(f"Could not save GUI config: {str(e)}")

    def open_settings(self):
        """Open the settings window"""
        settings = SettingsWindow(self.root, self)

    def stop_processing(self):
        if self.processing:
            self.stop_requested = True
            self.status_var.set("Stopping...")
            self.root.update()

    def get_config_value(self, key, default=""):
        """Get a value from the config file"""
        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_gui.json")) as f:
                config = json.load(f)
                return config.get(key, default)
        except Exception as e:
            print(f"Error reading config: {e}")
            return default
            
    def update_config(self, new_values):
        """Update the config with new values"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_gui.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update config with new values
            config.update(new_values)
            
            # Update class variables from settings window
            self.lmstudio_server = new_values.get('lmstudio_server', self.lmstudio_server)
            self.lmstudio_model_api = new_values.get('lmstudio_model', self.lmstudio_model_api)
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
        except Exception as e:
            print(f"Error updating config: {e}")

    def show_error(self, exc, val, tb):
        """Show error message in a dialog"""
        err = traceback.format_exception(exc, val, tb)
        messagebox.showerror("Error", f"An error occurred:\n{''.join(err)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SlideMobGUI(root)
    root.mainloop()