import os

def get_initial_config_path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")

class PathManager:
    def __init__(self, input_file: str):
        # Project root (where the application is installed)
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        print(self.project_root)
        
        # Working paths (specific to current PowerPoint)
        self.file_folder = os.path.dirname(input_file)
        self.input_file = os.path.abspath(input_file)
        self.working_dir = os.path.dirname(self.input_file)
        
        # Derived paths
        self.extracted_dir = os.path.join(self.working_dir, "extracted_pptx")
        self.output_dir = os.path.join(self.working_dir, "output")
        self.output_pptx=os.path.join(self.output_dir, f"translated_{os.path.basename(input_file)}")

    def get_config_path(self) -> str:
        return os.path.join(self.project_root, "config.json")
        
    def get_output_pptx_path(self, filename: str) -> str:
        return os.path.join(self.output_dir, f"translated_{filename}")
        
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.extracted_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)