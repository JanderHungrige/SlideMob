from ..core.base import PowerpointPipeline
import zipfile
import os

class PPTXTransformer(PowerpointPipeline):
    def __init__(self, extract_path: str):
        self.extract_path = extract_path
        super().__init__()

    def extract_pptx(self, pptx_path: str) -> str:
        """Extract a PPTX file into its XML components."""
        os.makedirs(self.extract_path, exist_ok=True)
        
        with zipfile.ZipFile(pptx_path, 'r') as pptx:
            pptx.extractall(self.extract_path)
        
        # Get namespaces right after extraction
        if self.extract_namespaces:
            self.namespaces = self.get_namespace()
        return self.extract_path

    def get_namespace(self) -> dict:
        """Get the namespaces from the first slide XML using text processing."""
        slide_path = os.path.join(self.extract_path, 'ppt/slides/slide1.xml')
        
        try:
            with open(slide_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Find the root element opening tag
            start_idx = content.find('<p:sld')
            end_idx = content.find('>', start_idx)
            if start_idx == -1 or end_idx == -1:
                print("Could not find root element")
                return {}
            
            # Extract the root element declaration
            root_declaration = content[start_idx:end_idx]
            
            # Find all xmlns declarations
            namespaces = {}
            import re
            
            # Pattern to match xmlns:prefix="uri" or xmlns="uri"
            pattern = r'xmlns(?::([^=]+))?="([^"]+)"'
            matches = re.finditer(pattern, root_declaration)
            
            for match in matches:
                prefix = match.group(1)  # This might be None for default namespace
                uri = match.group(2)
                if prefix:
                    namespaces[prefix] = uri
                else:
                    namespaces['default'] = uri
            
            print("\tExtracted namespaces:", namespaces)
            return namespaces
            
        except Exception as e:
            print(f"\tError extracting namespaces: {e}")
            return {}

    def compose_pptx(self, source_path: str, output_pptx: str):
        """Compose a PPTX file from a directory containing the XML structure."""
        os.makedirs(os.path.dirname(output_pptx), exist_ok=True)
        
        with zipfile.ZipFile(output_pptx, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_path)
                    zf.write(file_path, arcname)