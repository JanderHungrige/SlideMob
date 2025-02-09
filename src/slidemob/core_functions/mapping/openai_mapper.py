from typing import Optional
from .base import BaseMapper
from utils.promts import mapping_prompt_openai
import json

class OpenAIMapper(BaseMapper):
    def __init__(self, model: str, client: any, reasoning_model: bool = False):
        super().__init__(model=model, client=client)
        self.reasoning_model = reasoning_model

    def create_mapping(self, original_text_elements: set, original_text: str, 
                      translated_text: str) -> dict:
        try:
            prompt = mapping_prompt_openai(original_text_elements, original_text, translated_text)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional text alignment expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"OpenAI mapping error: {e}")
            return {} 