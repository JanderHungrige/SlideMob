from dataclasses import dataclass, field
import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@dataclass
class ModelSettings:
    translation_headers: dict[str, str] = field(default_factory=dict)
    mapping_headers: dict[str, str] = field(default_factory=dict)
    translation_api_url: str = ""
    mapping_api_url: str = ""
    mapping_client: str = None
    translation_client: str = None
    azure_config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Force reload environment variables
        load_dotenv(override=True)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.huggingface_api_key = os.getenv("HUGGINGFACE")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.azure_openai_key = os.getenv("AZURE_OPENAI_ENDPOINT_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self._load_gui_config()
        self._update_model_settings()
        self._setup_clients()

    def _update_model_settings(self) -> None:
        """Update model settings based on GUI config"""
        self.translation_method = self.gui_config.get("translation_method", "OpenAI")
        self.translation_model = self.gui_config.get("translation_model", "gpt-4")
        self.mapping_method = self.gui_config.get("mapping_method", "OpenAI")
        self.mapping_model = self.gui_config.get("mapping_model", "gpt-4")
        self.translation_api_url = self.gui_config.get(
            "translation_api_url", "http://localhost:1234"
        )
        self.mapping_api_url = self.gui_config.get(
            "mapping_api_url", "http://localhost:1234"
        )
        self.reduce_slides = self.gui_config.get("reduce_slides", False)
        self.style_instructions = self.gui_config.get("style_instructions", "")
        self.update_language = self.gui_config.get("update_language", False)
        self.fresh_extract = self.gui_config.get("fresh_extract", False)

    def _setup_clients(self) -> None:
        """Setup translation and mapping clients based on configuration"""
        self._setup_translation_client()
        self._setup_mapping_client()

    def _setup_translation_client(self) -> Any | None:
        """Setup and return translation client based on configuration"""
        try:
            if self.translation_method == "OpenAI":
                self.translation_client = OpenAI(api_key=self.openai_api_key)
                self.translation_headers = {
                    "Authorization": f"Bearer {self.openai_api_key}"
                }

            elif self.translation_method == "DeepSeek":
                self.translation_client = OpenAI(
                    api_key=self.deepseek_api_key, base_url="https://api.deepseek.com"
                )

            elif self.translation_method == "HuggingFace":
                self.translation_api_url = self.translation_api_url
                self.translation_headers = {
                    "Authorization": f"Bearer {self.huggingface_api_key}"
                }

            elif self.translation_method == "LMStudio":
                self.translation_client = OpenAI(base_url="http://localhost:1234/v1")
                self.translation_api_url = (
                    f"{self.translation_api_url.rstrip('/')}/v1/chat/completions"
                )
                self.translation_headers = {"Content-Type": "application/json"}

        except Exception as e:
            print(f"model_settings.py: Error setting up translation client: {e}")
            return None

    def _setup_mapping_client(self) -> Any | None:
        """Setup and return mapping client based on configuration"""
        try:
            if self.mapping_method == "OpenAI":
                self.mapping_client = OpenAI(api_key=self.openai_api_key)

            elif self.mapping_method == "DeepSeek":
                self.mapping_client = OpenAI(
                    api_key=self.deepseek_api_key, base_url="https://api.deepseek.com"
                )

            elif self.mapping_method == "HuggingFace":
                self.mapping_api_url = self.mapping_api_url
                self.mapping_headers = {
                    "Authorization": f"Bearer {self.huggingface_api_key}"
                }

            elif self.mapping_method == "LMStudio":
                self.mapping_client = OpenAI(base_url="http://localhost:1234/v1")
                self.mapping_api_url = (
                    f"{self.mapping_api_url.rstrip('/')}/v1/chat/completions"
                )
                self.mapping_headers = {"Content-Type": "application/json"}

        except Exception as e:
            print(f"model_settings.py: Error setting up mapping client: {e}")
            return None

    def _load_gui_config(self) -> None:
        """Load configuration from config_gui.json"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config_gui.json"
            )
            with open(config_path) as f:
                self.gui_config = json.load(f)
        except Exception as e:
            print(f"Error loading GUI config: {e}")
            self.gui_config = {}
