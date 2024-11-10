from ..core.base_class import PowerpointPipeline
from ..core.translator import SlideTranslator
from ..utils.path_manager import PathManager
import os
import traceback

class PowerPointTranslator(PowerpointPipeline):
    def __init__(self, target_language:str, Further_StyleInstructions:str="None", fresh_extract:bool=True, verbose:bool=False):
        super().__init__(),
        self.fresh_extract = fresh_extract
        self.verbose = verbose

        # Initialize transformer and translator
        self.translator = SlideTranslator(target_language, Further_StyleInstructions,)

    def translate_presentation(self):
        """Main method to handle the full translation process"""
        try:
            # Extract PPTX
            if self.fresh_extract:  
                self.extract_pptx()
            
            #Get namespaces
            namespaces = self.get_namespace()
            self.translator.namespaces = namespaces
            
            # Process slides
            self.translator.process_slides(self.extract_path)
            
            # Compose final PPTX
            # output_path = os.path.join(self.output_folder, self.output_pptx_name)
            # self.transformer.compose_pptx(self.extract_path, output_path)
            self.compose_pptx(self.extract_path, self.output_pptx)
            return True
            
        except Exception as e:
            print(f"Error translating presentation: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            return False
