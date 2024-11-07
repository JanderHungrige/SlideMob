from ..core.base import PowerpointPipeline
from ..core.transformer import PPTXTransformer

class XMLcreator(PowerpointPipeline):
    def __init__(self, verbose: bool=False):
        super().__init__(verbose=verbose)
        # Initialize transformer and translator
        self.transformer = PPTXTransformer(self.extract_path)

    def extract_pptx(self):
        """Main method to handle the full translation process"""
        try:
            # Extract PPTX
            self.transformer.extract_pptx(self.pptx_path)
            
            return True
            
        except Exception as e:
            print(f"Error translating presentation: {e}")
            return False
