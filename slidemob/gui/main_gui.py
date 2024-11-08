
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import logging


from ..pipelines.translator_pipeline import PowerPointTranslator
from ..pipelines.polisher_pipeline import PowerPointPolisher
from ..utils.errorhandler import setup_error_logging
from ..utils.config import create_config


class SlideMobGUI(PowerPointTranslator):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.root.title("SlideMob PowerPoint Processor")
        self.root.geometry("700x600")
        
        # Variables
        self.pptx_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.target_language = tk.StringVar(value="English")
        self.style_instructions = tk.StringVar()
        
        # Checkboxes
        self.extract_var = tk.BooleanVar(value=True)
        self.polish_var = tk.BooleanVar(value=False)
        self.translate_var = tk.BooleanVar(value=False)
        
        # Load the logo image
        current_dir = os.path.dirname(__file__)
        logo_path = os.path.join(current_dir, "../gui/assets/eraneos_bg Small.png")
        logo_path = os.path.abspath(logo_path)
        self.logo_image = tk.PhotoImage(file=logo_path)
        
        # Create a canvas for the logo with padding
        canvas_width = self.logo_image.width() + 8  # Add padding
        canvas_height = self.logo_image.height() + 8  # Add padding
        self.logo_canvas = tk.Canvas(self.root, width=canvas_width, height=canvas_height)
        # Center the image in the canvas
        self.logo_canvas.create_image(
            canvas_width//2, 
            canvas_height//2, 
            anchor="center", 
            image=self.logo_image
        )
        self.logo_canvas.pack(side="bottom", anchor="se")

        # Initialize error logging
        setup_error_logging()
        
        self.create_widgets()
        
    def create_widgets(self):
        # File Selection Frame
        file_frame = ttk.LabelFrame(self.root, text="File Selection", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(file_frame, text="PowerPoint File:").pack(anchor="w")
        ttk.Entry(file_frame, textvariable=self.pptx_path, width=50).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_pptx).pack(side="left")
        
        # Output Selection Frame
        output_frame = ttk.LabelFrame(self.root, text="Output Location", padding=10)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_frame, text="Output Folder:").pack(anchor="w")
        ttk.Entry(output_frame, textvariable=self.output_path, width=50).pack(side="left", padx=5)
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side="left")
        
        # Options Frame
        options_frame = ttk.LabelFrame(self.root, text="Processing Options", padding=10)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        # Checkboxes
        ttk.Checkbutton(options_frame, text="Extract PPTX", variable=self.extract_var).pack(anchor="w")
        ttk.Checkbutton(options_frame, text="Polish Content", variable=self.polish_var).pack(anchor="w")
        ttk.Checkbutton(options_frame, text="Translate Content", variable=self.translate_var).pack(anchor="w")
        
        # Translation Options (only enabled when translate is checked)
        translation_frame = ttk.Frame(options_frame)
        translation_frame.pack(fill="x", pady=5)
        
        ttk.Label(translation_frame, text="Target Language:").pack(side="left")
        languages = ["English", "German", "French", "Spanish", "Italian", "Chinese", "Japanese"]
        language_dropdown = ttk.Combobox(translation_frame, textvariable=self.target_language, values=languages)
        language_dropdown.pack(side="left", padx=5)
        
        # Style Instructions
        style_frame = ttk.LabelFrame(self.root, text="Style Instructions", padding=10)
        style_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(style_frame, text="Additional Style Instructions:").pack(anchor="w")
        style_entry = ttk.Entry(style_frame, textvariable=self.style_instructions, width=50)
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
            self.pptx_path.set(filename)
            
    def browse_output(self):
        if self.pptx_path.get():
            startfolder = os.path.dirname(self.pptx_path.get())
        else:
            startfolder = os.getcwd()
        folder = filedialog.askdirectory(title="Select Output Folder",initialdir=startfolder)
        if folder:
            self.output_path.set(folder)
            
    def process_presentation(self):
        if not self.pptx_path.get() or not self.output_path.get():
            messagebox.showerror("Error", "Please select both input file and output location")
            return
        
        try:
            config = create_config(
                path_manager=path_manager,
                pptx_folder="",
                pptx_name=os.path.basename(self.pptx_path.get()),
                extract_folder=os.path.join(self.output_path.get(), "extracted_pptx"),
                output_folder=self.output_path.get(),
                target_language=self.target_language.get()
            )
            
            with open("config.json", "w") as f:
                json.dump(config, f)
            
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
                    Further_StyleInstructions=self.style_instructions.get(),
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
                    target_language=self.target_language.get(),
                    Further_StyleInstructions=self.style_instructions.get(),
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
            self.status_var.set("Error occurred! Check error_logs folder for details.")
            messagebox.showerror("Error", "An error occurred. Check error_logs folder for details.")
            raise  # Re-raise the exception to be caught by the error handler

if __name__ == "__main__":
    root = tk.Tk()
    app = SlideMobGUI(root)
    root.mainloop()