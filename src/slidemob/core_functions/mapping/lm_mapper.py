from typing import Optional
from .base import BaseMapper
import json
import re
from utils.promts import mapping_prompt_llama2, mapping_prompt_deepseek


class LMStudioMapper(BaseMapper):
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

    def create_mapping(
        self, original_text_elements: set, original_text: str, translated_text: str
    ) -> dict:
        try:
            # Select prompt based on model type
            if self.model_type == "llama":
                prompt = mapping_prompt_llama2(
                    original_text_elements, original_text, translated_text
                )
            elif self.model_type == "deepseek":
                prompt = mapping_prompt_deepseek(
                    original_text_elements, original_text, translated_text
                )
            else:
                # Default to llama prompt if unknown
                prompt = mapping_prompt_llama2(
                    original_text_elements, original_text, translated_text
                )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional text alignment expert.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            return self._parse_response(response)

        except Exception as e:
            print(f"LMStudio mapping error: {e}")
            return {}

    def _parse_response(self, response: any) -> dict:
        try:
            content = response.choices[0].message.content.strip()

            if self.reasoning_model:
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)

            # If response contains [/INST], extract the content after it
            if "[/INST]" in content:
                content = content.split("[/INST]")[-1].strip()

            return json.loads(content)

        except Exception as e:
            print(f"Error parsing LMStudio response: {e}")
            return {}
