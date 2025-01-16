from ..core.base_class import PowerpointPipeline
import traceback

class XMLcreator(PowerpointPipeline):
    def __init__(self, verbose: bool=False):
        super().__init__(verbose=verbose)
        # Initialize transformer and translator

    def extract_pptx(self):
        """Main method to handle the full translation process"""
        try:
            # Extract PPTX
            self.extract_pptx()
            return True
        
        except Exception as e:
            print(f"Error translating presentation: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            return False
