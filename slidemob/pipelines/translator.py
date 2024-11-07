from ..core.base import PowerpointPipeline
from ..core.transformer import PPTXTransformer
from ..core.translator import SlideTranslator
import os

class PowerPointTranslator(PowerpointPipeline):
    def __init__(self, target_language:str, Further_StyleInstructions:str="None", fresh_extract:bool=True):
        super().__init__()
        self.fresh_extract = fresh_extract

        # Initialize transformer and translator
        self.transformer = PPTXTransformer(self.extract_path)
        self.translator = SlideTranslator(target_language, Further_StyleInstructions)

    def translate_presentation(self):
        """Main method to handle the full translation process"""
        try:
            # Extract PPTX
            if self.fresh_extract:  
                self.transformer.extract_pptx(self.pptx_path)
            
            #Get namespaces
            namespaces = self.transformer.get_namespace()
            self.translator.namespaces = namespaces
            
            # Process slides
            self.translator.process_slides(self.extract_path)
            
            # Compose final PPTX
            output_path = os.path.join(self.output_folder, self.output_pptx_name)
            self.transformer.compose_pptx(self.extract_path, output_path)
            
            return True
            
        except Exception as e:
            print(f"Error translating presentation: {e}")
            return False
