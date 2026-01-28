import os
import requests
from .base import BaseTranslator


class GoogleTranslator(BaseTranslator):
    def __init__(self):
        super().__init__(model="google")

    def translate(
        self, text: str, target_language: str, style_instructions: str = ""
    ) -> str:
        try:
            # Convert target language to Google code
            google_lang_code = self._get_google_lang_code(target_language)

            # Get API Key from environment
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("Error: GOOGLE_API_KEY not found in environment variables.")
                return text

            url = f"https://translation.googleapis.com/language/translate/v2?key={api_key}"
            payload = {
                "q": text,
                "target": google_lang_code,
                "format": "text"
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result["data"]["translations"][0]["translatedText"]

        except Exception as e:
            print(f"Google translation error: {e}")
            return text

    def _get_google_lang_code(self, target_language: str) -> str:
        # This should be implemented with proper language code mapping
        # For now returning simple mapping
        return target_language.split("-")[0].lower()
