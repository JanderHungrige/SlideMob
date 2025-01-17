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

class SlideMobGUI(PowerpointPipeline):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.root.title("SlideMob PowerPoint Processor")
        self.root.geometry("700x750")

        #Load language codes
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_languages.json")) as f:
            language_config = json.load(f)
        self.language_options = [lang["language"].split(" (")[0] for lang in language_config["languages"]]
            
        # GUI Variables (StringVar)
        self.gui_pptx_path = tk.StringVar()
        self.gui_output_path = tk.StringVar()
        self.gui_target_language = tk.StringVar(value="English")
        self.gui_style_instructions = tk.StringVar()
        
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
        style.set_theme('equilux')  # 'clam' theme works better with custom colors
        # Configure the button style
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
        # File Selection Frame
        file_frame = ttk.LabelFrame(self.root, text="File Selection", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(file_frame, text="PowerPoint File:").pack(anchor="w")
        ttk.Entry(file_frame, textvariable=self.gui_pptx_path, width=50).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_pptx,style='Blue.TButton').pack(side="left")
        
        # Output Selection Frame
        output_frame = ttk.LabelFrame(self.root, text="Output Location", padding=10)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_frame, text="Output Folder:").pack(anchor="w")
        ttk.Entry(output_frame, textvariable=self.gui_output_path, width=50).pack(side="left", padx=5)
        ttk.Button(output_frame, text="Browse", command=self.browse_output,style='Blue.TButton').pack(side="left")
        
        # Options Frame with help button
        options_frame = ttk.LabelFrame(self.root, text="Processing Options", padding=10)
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
        
        ttk.Label(translation_frame, text="Target Language:").pack(side="left")
        #languages = ["English", "German", "French", "Spanish", "Italian", "Chinese", "Japanese", "Russian","Portuguese","Dutch","Polish"]
        
        language_dropdown = ttk.Combobox(translation_frame, textvariable=self.gui_target_language, values=self.language_options)
        language_dropdown.pack(side="left", padx=5)
        
        # Translation Method Frame
        method_frame = ttk.Frame(translation_frame)
        method_frame.pack(side="left", padx=(20, 0))

        ttk.Label(method_frame, text="Translation Method:").pack(side="left")
        ttk.Radiobutton(method_frame, text="OpenAI", variable=self.translation_method, value="OpenAI").pack(side="left")
        ttk.Radiobutton(method_frame, text="Google", variable=self.translation_method, value="Google").pack(side="left")
        ttk.Radiobutton(method_frame, text="HuggingFace", variable=self.translation_method, value="HuggingFace").pack(side="left")

        # Style Instructions
        style_frame = ttk.LabelFrame(self.root, text="Style Instructions", padding=10)
        style_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(style_frame, text="Additional Style Instructions:").pack(anchor="w")
        style_entry = ttk.Entry(style_frame, textvariable=self.gui_style_instructions, width=50)
        style_entry.pack(fill="x", pady=5)
        
        # Process Button
        ttk.Button(self.root, text="Process PowerPoint", command=self.process_presentation,style='Blue.TButton').pack(pady=20)
        
        # Progress
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(fill="x", padx=10, pady=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var).pack()
        
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
            
    def process_presentation(self):
        if not self.pptx_path or not self.output_path:
            messagebox.showerror("Error", "Please select both input file and output location")
            return
        
        # Save GUI config as soon as process button is clicked
        self.save_gui_config()
        
        try:
            # Create PathManager instance with the actual path string
            path_manager = PathManager(self.pptx_path)
            
            # Create config with the updated paths and target language
            config = create_config(
                path_manager=path_manager,
                target_language=self.gui_target_language.get()
            )

            self.progress['value'] = 0
            steps = sum([self.extract_var.get(), self.polish_var.get(), self.translate_var.get(), self.merge_runs_var.get()])
            step_size = 100 / steps if steps > 0 else 100
            
            # Extract
            if self.extract_var.get():
                self.status_var.set("Extracting PPTX...")
                self.root.update()
                
                success = self.extract_pptx()
                if not success:
                    raise Exception("Extraction failed")
                    
                self.progress['value'] += step_size
                self.root.update()
            
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
                    
                self.progress['value'] += step_size
                self.root.update()
            
            # Translate
            if self.translate_var.get():
                self.status_var.set("Translating content...")
                self.root.update()
                
                translator = PowerPointTranslator(
                    target_language=self.gui_target_language.get(),
                    Further_StyleInstructions=self.gui_style_instructions.get(),
                    update_language=self.update_language.get(),
                    fresh_extract=not (self.extract_var.get() or self.polish_var.get()),
                    translation_method=self.translation_method.get()
                )
                success = translator.translate_presentation()
                if not success:
                    print("Full traceback:")
                    print(traceback.format_exc())
                    raise Exception("Translation failed")

                    
                self.progress['value'] += step_size
                self.root.update()
            
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
                    
                self.progress['value'] += step_size
                self.root.update()
            
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
                'style_instructions': self.gui_style_instructions.get(),
                'pptx_path': self.gui_pptx_path.get(),
                'output_folder': self.gui_output_path.get()
            }
            
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_gui.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.warning(f"Could not save GUI config: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SlideMobGUI(root)
    root.mainloop()