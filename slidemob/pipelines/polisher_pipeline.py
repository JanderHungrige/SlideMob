## Pipeline - Polisher
from ..core.base_class import PowerpointPipeline
from ..core.polisher import SlidePolisher
import os

class PowerPointPolisher(PowerpointPipeline):
    def __init__(self, Further_StyleInstructions:str="None", fresh_extract:bool=True):
        super().__init__()
        
        self.fresh_extract = fresh_extract
        # Initialize transformer and translator
        self.polisher = SlidePolisher(Further_StyleInstructions)

    def polish_presentation(self):
        """Main method to handle the full translation process"""
        try:
            # Extract PPTX
            if self.fresh_extract:
                self.extract_pptx()
            
            #Get namespaces
            namespaces = self.get_namespace()
            self.polisher.namespaces = namespaces
            
            # Process slides
            self.polisher.process_slides(self.extract_path)
            
            # Compose final PPTX
            # output_path = os.path.join(self.output_folder, self.output_pptx_name)
            # self.transformer.compose_pptx(self.extract_path, output_path)
            self.compose_pptx(self.extract_path, self.output_folder)
            return True
            
        except Exception as e:
            print(f"Error polishing presentation: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            return False
