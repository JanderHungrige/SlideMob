from core_functions.base_class import PowerpointPipeline
from core_functions.translator import SlideTranslator
from utils.path_manager import PathManager
import os
import traceback

class PowerPointTranslator(PowerpointPipeline):
    def __init__(self, target_language:str, Further_StyleInstructions:str="None", update_language:bool=False, fresh_extract:bool=True, verbose:bool=False, reduce_slides:bool=False, translation_method:str="OpenAI", mapping_method:str="OpenAI"):
        super().__init__(),
        self.fresh_extract = fresh_extract
        self.verbose = verbose
        self.reduce_slides = reduce_slides
        self.translation_method = translation_method
        self.mapping_method = mapping_method
        # Initialize transformer and translator
        self.translator = SlideTranslator(target_language, Further_StyleInstructions, update_language, reduce_slides, verbose, translation_method, mapping_method)

    def translate_presentation(self, progress_callback=None, stop_check_callback=None):
        """Main method to handle the full translation process"""
        try:
            # Extract PPTX
            if self.fresh_extract:  
                self.extract_pptx()
            #Get namespaces
            namespaces = self.get_namespace()
            self.translator.namespaces = namespaces
            # Process slides with callbacks
            success = self.translator.process_slides(self.extract_path, progress_callback, stop_check_callback)
            if not success:
                return False
            # Compose final PPTX
            self.compose_pptx(self.extract_path, self.output_pptx)
            return True
            
        except Exception as e:
            print(f"Error translating presentation: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            return False
