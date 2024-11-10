import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import logging

from ..core.base_class import PowerpointPipeline
from ..pipelines.translator_pipeline import PowerPointTranslator
from ..pipelines.polisher_pipeline import PowerPointPolisher
from ..utils.errorhandler import setup_error_logging
from ..utils.config import create_config
from ..utils.path_manager import PathManager

class SlideMobGUI(PowerpointPipeline):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.root.title("SlideMob PowerPoint Processor")
        self.root.geometry("800x600")
        
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
        self.translate_var = tk.BooleanVar(value=False)
        
        # Load the logo image
        current_dir = os.path.dirname(__file__)
        company_logo_path = os.path.join(current_dir, "../gui/assets/eraneos_bg Small.png")
        company_logo_path = os.path.abspath(company_logo_path)
        self.company_logo_image = tk.PhotoImage(file=company_logo_path)

        #Load Icon 
        app_logo_path = os.path.join(current_dir, "../gui/assets/doppelfahreimer Small Small.png")
        app_logo_path = os.path.abspath(app_logo_path)
        self.app_logo_image = tk.PhotoImage(file=app_logo_path)


        # Create a frame to hold both logos at the bottom
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(side="bottom", fill="x")

        # Add the app logo to the lower left corner
        canvas_width = self.app_logo_image.width() + 8
        canvas_height = self.app_logo_image.height() + 8  # Base height for both canvases
        self.app_logo_canvas = tk.Canvas(bottom_frame, width=canvas_width, height=canvas_height)
        self.app_logo_canvas.create_image(
            canvas_width//2,
            canvas_height//2,
            anchor="center",
            image=self.app_logo_image
        )
        self.app_logo_canvas.pack(side="left")

        # Add the company logo to the lower right corner
        canvas_width = self.company_logo_image.width() + 8
        self.logo_canvas = tk.Canvas(bottom_frame, width=canvas_width, height=canvas_height)  # Using app_logo height
        self.logo_canvas.create_image(
            canvas_width//2, 
            canvas_height//2, 
            anchor="center", 
            image=self.company_logo_image
        )
        self.logo_canvas.pack(side="right")

        # Initialize error logging
        setup_error_logging()
        
        self.create_widgets()

    def _update_pptx_path(self, *args):
        """Update the parent class pptx_path when GUI var changes"""
        self.pptx_path = self.gui_pptx_path.get()

    def _update_output_path(self, *args):
        """Update the parent class output_path when GUI var changes"""
        self.output_path = self.gui_output_path.get()
        
    def create_widgets(self):
        # File Selection Frame
        file_frame = ttk.LabelFrame(self.root, text="File Selection", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(file_frame, text="PowerPoint File:").pack(anchor="w")
        ttk.Entry(file_frame, textvariable=self.gui_pptx_path, width=50).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_pptx).pack(side="left")
        
        # Output Selection Frame
        output_frame = ttk.LabelFrame(self.root, text="Output Location", padding=10)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_frame, text="Output Folder:").pack(anchor="w")
        ttk.Entry(output_frame, textvariable=self.gui_output_path, width=50).pack(side="left", padx=5)
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side="left")
        
        # Options Frame
        options_frame = ttk.LabelFrame(self.root, text="Processing Options", padding=10)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        # Checkboxes
        ttk.Checkbutton(options_frame, text="Extract PPTX", variable=self.extract_var).pack(anchor="w")
        ttk.Checkbutton(options_frame, text="Polish Content", variable=self.polish_var).pack(anchor="w")
        ttk.Checkbutton(options_frame, text="Translate Content", variable=self.translate_var).pack(anchor="w")
        
        # Translation Options
        translation_frame = ttk.Frame(options_frame)
        translation_frame.pack(fill="x", pady=5)
        
        ttk.Label(translation_frame, text="Target Language:").pack(side="left")
        languages = ["English", "German", "French", "Spanish", "Italian", "Chinese", "Japanese"]
        language_dropdown = ttk.Combobox(translation_frame, textvariable=self.gui_target_language, values=languages)
        language_dropdown.pack(side="left", padx=5)
        
        # Style Instructions
        style_frame = ttk.LabelFrame(self.root, text="Style Instructions", padding=10)
        style_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(style_frame, text="Additional Style Instructions:").pack(anchor="w")
        style_entry = ttk.Entry(style_frame, textvariable=self.gui_style_instructions, width=50)
        style_entry.pack(fill="x", pady=5)
        
        # Process Button
        ttk.Button(self.root, text="Process PowerPoint", command=self.process_presentation).pack(pady=20)
        
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
        
        try:
            # Create PathManager instance with the actual path string
            path_manager = PathManager(self.pptx_path)
            
            # Create config with the updated paths and target language
            config = create_config(
                path_manager=path_manager,
                target_language=self.gui_target_language.get()
            )

            self.progress['value'] = 0
            steps = sum([self.extract_var.get(), self.polish_var.get(), self.translate_var.get()])
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
                    fresh_extract=not (self.extract_var.get() or self.polish_var.get())
                )
                success = translator.translate_presentation()
                if not success:
                    raise Exception("Translation failed")
                    
                self.progress['value'] += step_size
                self.root.update()
            
            self.status_var.set("Processing complete!")
            messagebox.showinfo("Success", "PowerPoint processing completed successfully!")
            
        except Exception as e:
            self.status_var.set(f"Error occurred: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}\nCheck error_logs folder for details.")
            logging.exception("Error in process_presentation")
            raise e

if __name__ == "__main__":
    root = tk.Tk()
    app = SlideMobGUI(root)
    root.mainloop()