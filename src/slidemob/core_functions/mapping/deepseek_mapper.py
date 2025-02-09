from typing import Optional
from .base import BaseMapper
import json
import re
from utils.promts import mapping_prompt_deepseek


class DeepSeekMapper(BaseMapper):
    def __init__(self, model: str, client: any, reasoning_model: bool = False):
        super().__init__(model=model, client=client)
        self.reasoning_model = reasoning_model

    def create_mapping(
        self, original_text_elements: set, original_text: str, translated_text: str
    ) -> dict:
        try:
            prompt = mapping_prompt_deepseek(
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
            print(f"DeepSeek mapping error: {e}")
            return {}

    def _parse_response(self, response: any) -> dict:
        try:
            content = response.choices[0].message.content.strip()

            if self.reasoning_model:
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)

            return json.loads(content)

        except Exception as e:
            print(f"Error parsing DeepSeek response: {e}")
            return {}
