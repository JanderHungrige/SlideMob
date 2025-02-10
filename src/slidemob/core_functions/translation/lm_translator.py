import re

from utils.promts import translation_prompt_deepseek_0, translation_prompt_llama2_0

from .base import BaseTranslator


class LMStudioTranslator(BaseTranslator):
    def __init__(
        self,
        model: str,
        client: any,
        model_type: str = "unknown",
        reasoning_model: bool = False,
    ):
        super().__init__(model=model, client=client)
        self.model_type = model_type
        self.reasoning_model = reasoning_model

    def translate(
        self, text: str, target_language: str, style_instructions: str = ""
    ) -> str:
        try:
            # Select prompt based on model type
            if self.model_type == "llama":
                prompt = translation_prompt_llama2_0(
                    text, target_language, style_instructions
                )
            elif self.model_type == "deepseek":
                prompt = translation_prompt_deepseek_0(
                    text, target_language, style_instructions
                )
            else:
                # Default to llama prompt if unknown
                prompt = translation_prompt_llama2_0(
                    text, target_language, style_instructions
                )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            return self._parse_response(response, text)

        except Exception as e:
            print(f"LMStudio translation error: {e}")
            return text

    def _parse_response(self, response: any, original_text: str) -> str:
        try:
            content = response.choices[0].message.content.strip()

            if self.reasoning_model:
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)

            # Try to extract content between translation tags
            translation_match = re.search(
                r"<translation>\s*(.*?)\s*</translation>", content, re.DOTALL
            )
            if translation_match:
                return translation_match.group(1).strip()

            # If no translation tags, try to extract content between [/INST] tags
            if "[/INST]" in content:
                content = content.split("[/INST]")[-1].strip()

            return content or original_text

        except Exception:
            return original_text
