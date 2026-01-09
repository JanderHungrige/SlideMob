"""Tooltip module for SlideMob GUI."""
import customtkinter as ctk


class Tooltip:
    """Creates a tooltip for a given widget."""
    
    def __init__(self, widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.schedule_id = None
        
        self.widget.bind("<Enter>", self._schedule_show)
        self.widget.bind("<Leave>", self._hide)
        self.widget.bind("<ButtonPress>", self._hide)
    
    def _schedule_show(self, event=None):
        self._hide()
        self.schedule_id = self.widget.after(self.delay, self._show)
    
    def _show(self, event=None):
        if self.tooltip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        
        label = ctk.CTkLabel(
            tw,
            text=self.text,
            corner_radius=6,
            fg_color=("#333333", "#1a1a1a"),
            text_color=("#ffffff", "#ffffff"),
            padx=10,
            pady=6,
            wraplength=300
        )
        label.pack()
    
    def _hide(self, event=None):
        if self.schedule_id:
            self.widget.after_cancel(self.schedule_id)
            self.schedule_id = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


# Centralized tooltip texts
TOOLTIP_TEXTS = {
    # File Selection
    "pptx_file": "Select the PowerPoint file (.pptx) you want to process.",
    "output_folder": "Choose where the processed file will be saved.",
    
    # Processing Options
    "extract": "Extracts text content from the PowerPoint for processing. Required for most operations.",
    "pre_merge": "Merges fragmented text runs that PowerPoint sometimes creates. Recommended before translation for better quality.",
    "polish": "Uses AI to improve writing style, grammar, and professional tone of the content.",
    "translate": "Translates all text content to your target language while preserving formatting.",
    "update_language": "Updates PowerPoint's internal language metadata to match the translated content.",
    "reduce_slides": "Optimizes processing by identifying and handling redundant slide elements.",
    "overwrite": "If checked, overwrites the original file. Otherwise, creates a new file with '_slidemobbed' suffix.",
    
    # Translation Settings
    "target_language": "Select the language you want to translate your presentation into.",
    "translation_strategy": "Classic: Standard segment-by-segment translation.\nMarker-based: Advanced method for complex formatting.",
    "translation_method": "Choose which AI service to use for translation.",
    "mapping_method": "Choose which AI service to use for text alignment/mapping.",
    
    # Buttons
    "process": "Start processing the PowerPoint file with the selected options.",
    "stop": "Stop the current processing operation.",
    "settings": "Open settings to configure API keys and model preferences.",
}
