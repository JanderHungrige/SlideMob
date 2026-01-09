import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # In dev, use the src/slidemob directory as base
        # path_manager.py is in src/slidemob/utils/
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # If relative path starts with 'slidemob/', strip it in dev mode 
        # because we are already IN slidemob folder
        if relative_path.startswith("slidemob/"):
            relative_path = relative_path.replace("slidemob/", "", 1)
            
    return os.path.join(base_path, relative_path)

def get_user_config_path():
    """Get path to user's writable config file"""
    user_dir = os.path.join(os.path.expanduser("~"), ".slidemob")
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "config_gui.json")

def get_user_env_path():
    """Get path to user's writable .env file"""
    user_dir = os.path.join(os.path.expanduser("~"), ".slidemob")
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, ".env")

def get_initial_config_path() -> str:
    # In spec: ('src/slidemob/config.json', 'slidemob') -> sys._MEIPASS/slidemob/config.json
    return get_resource_path("slidemob/config.json")


class PathManager:
    def __init__(self, input_file: str, output_file: str = None, overwrite: bool = False):
        # Project root should point to where configs are
        self.project_root = os.path.dirname(get_resource_path("slidemob/config.json"))
        print(f"Project root resolved to: {self.project_root}")

        # Working paths (specific to current PowerPoint)
        self.file_folder = os.path.dirname(input_file)
        self.input_file = os.path.abspath(input_file)
        self.working_dir = os.path.dirname(self.input_file)
        self.overwrite = overwrite

        # Derived paths
        self.extracted_dir = os.path.join(self.working_dir, "extracted_pptx")
        
        # Determine output directory
        if output_file:
            self.output_dir = os.path.abspath(output_file)
        else:
            self.output_dir = self.working_dir

        # Determine output filename
        if self.overwrite:
            self.output_pptx = self.input_file
        else:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            self.output_pptx = os.path.join(
                self.output_dir, f"{base_name}_slidemobbed.pptx"
            )

    def get_config_path(self) -> str:
        return get_resource_path("slidemob/config.json")

    def get_output_pptx_path(self, filename: str) -> str:
        if self.overwrite:
            return self.input_file
        base_name = os.path.splitext(filename)[0]
        return os.path.join(self.output_dir, f"{base_name}_slidemobbed.pptx")

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.extracted_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
