import re

from utils.promts import translation_prompt_deepseek_0

from .base import BaseTranslator


class DeepSeekTranslator(BaseTranslator):
    def __init__(self, model: str, client: any, reasoning_model: bool = False):
        super().__init__(model=model, client=client)
        self.reasoning_model = reasoning_model

    def translate(
        self, text: str, target_language: str, style_instructions: str = ""
    ) -> str:
        try:
            prompt = translation_prompt_deepseek_0(
                text, target_language, style_instructions
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            return self._parse_response(response, text)

        except Exception as e:
            print(f"DeepSeek translation error: {e}")
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
