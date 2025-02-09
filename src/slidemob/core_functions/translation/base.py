from abc import ABC, abstractmethod
from typing import Optional


class BaseTranslator(ABC):
    def __init__(
        self,
        model: str,
        api_url: Optional[str] = None,
        client: Optional[any] = None,
        headers: Optional[dict] = None,
    ):
        self.model = model
        self.api_url = api_url
        self.client = client
        self.headers = headers

    @abstractmethod
    def translate(
        self, text: str, target_language: str, style_instructions: str = ""
    ) -> str:
        """Translate text to target language"""
        pass


class BaseMapper(ABC):
    def __init__(
        self,
        model: str,
        api_url: Optional[str] = None,
        client: Optional[any] = None,
        headers: Optional[dict] = None,
    ):
        self.model = model
        self.api_url = api_url
        self.client = client
        self.headers = headers

    @abstractmethod
    def create_mapping(
        self, original_text_elements: set, original_text: str, translated_text: str
    ) -> dict:
        """Create mapping between original and translated text"""
        pass
