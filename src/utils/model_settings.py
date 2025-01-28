import os
import json
from openai import OpenAI
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class ModelSettings:
    translation_headers: Dict[str, str] = field(default_factory=dict)
    mapping_headers: Dict[str, str] = field(default_factory=dict)
    translation_api_url: str = ""
    mapping_api_url: str = ""
    mapping_client: str = None
    translation_client: str = None

    def __post_init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.huggingface_api_key = os.getenv("HUGGINGFACE")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self._load_gui_config()
        self._update_model_settings()
        self._setup_clients()

    def _update_model_settings(self) -> None:
        """Update model settings based on GUI config"""
        self.translation_method = self.gui_config.get("translation_method", "OpenAI")
        self.translation_model = self.gui_config.get("translation_model", "gpt-4")
        self.mapping_method = self.gui_config.get("mapping_method", "OpenAI")
        self.mapping_model = self.gui_config.get("mapping_model", "gpt-4")
        self.translation_api_url = self.gui_config.get("translation_api_url", "http://localhost:1234")
        self.mapping_api_url = self.gui_config.get("mapping_api_url", "http://localhost:1234")
        self.reduce_slides = self.gui_config.get("reduce_slides", False)
        self.style_instructions = self.gui_config.get("style_instructions", "")
        self.update_language = self.gui_config.get("update_language", False)
        self.fresh_extract = self.gui_config.get("fresh_extract", False)
        

    def _setup_clients(self) -> None:
        """Setup translation and mapping clients based on configuration"""
        self.translation_client = self._setup_translation_client()
        self.mapping_client = self._setup_mapping_client()

    def _setup_translation_client(self) -> Optional[Any]:
        """Setup and return translation client based on configuration"""
        if self.translation_method == "OpenAI":
            self.translation_client = OpenAI(api_key=self.openai_api_key)
            return self.translation_client
                
        elif self.translation_method == "DeepSeek":
            self.translation_client = OpenAI(api_key=self.deepseek_api_key, base_url="https://api.deepseek.com")
            return self.translation_client
            
        elif self.translation_method == "HuggingFace":
            self.translation_api_url = self.huggingface_url
            self.translation_headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}

        elif self.translation_method == "LMStudio":
            self.translation_api_url = f"{self.lmstudio_server.rstrip('/')}/v1/chat/completions"
            self.translation_headers = {"Content-Type": "application/json"}


        print(f"\tUnsupported translation method: {self.translation_method}")
        return None

    def _setup_mapping_client(self) -> Optional[Any]:
        """Setup and return mapping client based on configuration"""
        if self.mapping_method == "OpenAI":
            self.mapping_client = OpenAI(api_key=self.openai_api_key)

        elif self.mapping_method == "DeepSeek":
            self.mapping_client = OpenAI(api_key=self.deepseek_api_key, base_url="https://api.deepseek.com")

        elif self.mapping_method == "HuggingFace":
            self.mapping_api_url = self.huggingface_url
            self.mapping_headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}

        elif self.mapping_method == "LMStudio":
            self.mapping_api_url = f"{self.lmstudio_server.rstrip('/')}/v1/chat/completions"
            self.mapping_headers = {"Content-Type": "application/json"}

        print(f"\tUnsupported mapping method: {self.mapping_method}")
        return None 
    
    def _load_gui_config(self) -> None:
        """Load configuration from config_gui.json"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_gui.json")
            with open(config_path, "r") as f:
                self.gui_config = json.load(f)
        except Exception as e:
            print(f"Error loading GUI config: {e}")
            self.gui_config = {}

