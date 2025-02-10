import re

from utils.promts import translation_prompt_openai_1

from .base import BaseTranslator


class AzureTranslator(BaseTranslator):
    def __init__(
        self,
        model: str,
        client: any,
        reasoning_model: bool = False,
        config: dict | None = None,
    ):
        super().__init__(model=model, client=client)
        self.reasoning_model = reasoning_model
        self.config = config or {}

    def translate(
        self, text: str, target_language: str, style_instructions: str = ""
    ) -> str:
        try:
            prompt = translation_prompt_openai_1(
                text, target_language, style_instructions
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.get("temperature", 0.3),
                frequency_penalty=self.config.get("frequency_penalty", 0),
                presence_penalty=self.config.get("presence_penalty", 0),
                max_tokens=self.config.get("max_tokens_out", 2000),
            )

            return self._parse_response(response, text)

        except Exception as e:
            print(f"Azure translation error: {e}")
            return text

    def _parse_response(self, response: any, original_text: str) -> str:
        try:
            content = response.choices[0].message.content.strip()

            if self.reasoning_model:
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)

            translation_match = re.search(
                r"<translation>\s*(.*?)\s*</translation>", content, re.DOTALL
            )
            if translation_match:
                return translation_match.group(1).strip()

            return content or original_text

        except Exception:
            return original_text
