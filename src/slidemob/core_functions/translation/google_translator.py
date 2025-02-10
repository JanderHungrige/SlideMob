import asyncio

from googletrans import Translator

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

            async def translate_text():
                async with Translator() as translator:
                    result = await translator.translate(text, dest=google_lang_code)
                return result.text

            return asyncio.run(translate_text())

        except Exception as e:
            print(f"Google translation error: {e}")
            return text

    def _get_google_lang_code(self, target_language: str) -> str:
        # This should be implemented with proper language code mapping
        # For now returning simple mapping
        return target_language.split("-")[0].lower()
