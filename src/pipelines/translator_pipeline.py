from core_functions.base_class import PowerpointPipeline
from core_functions.translator import SlideTranslator
from utils.path_manager import PathManager
import os
import traceback
from typing import Optional

from core_functions.base_class import PowerpointPipeline

class PowerPointTranslator():
    def __init__(self, progress_callback, stop_check_callback):
        # Initialize base class first to set up ModelSettings
        self.progress_callback=progress_callback
        self.stop_check_callback=stop_check_callback
        
    def translate_presentation(self, progress_callback=None, stop_check_callback=None):
        """Main method to handle the full translation process"""
        try:
            self.settings=PowerpointPipeline()
            self.translator=SlideTranslator(pipeline_settings=self.settings)
            # Extract PPTX if needed
            if self.settings.fresh_extract:  
                self.settings.extract_pptx()
            # Get namespaces
            namespaces = self.settings.get_namespace() 
            success = self.translator.process_slides(self.progress_callback, self.stop_check_callback)
            if not success:
                return False
            # Compose final PPTX
            self.settings.compose_pptx(self.settings.extract_path, self.settings.output_pptx)
            return True
            
        except Exception as e:
            print(f"Error translating presentation: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            return False
