import re
from typing import Optional
from .base import BaseTranslator
from utils.promts import translation_prompt_openai_0, translation_prompt_openai_1

class OpenAITranslator(BaseTranslator):
    def __init__(self, model: str, client: any, reasoning_model: bool = False):
        super().__init__(model=model, client=client)
        self.reasoning_model = reasoning_model

    def translate(self, text: str, target_language: str, style_instructions: str = "") -> str:
        prompt = translation_prompt_openai_1(text, target_language, style_instructions)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=1.5
            )

            content = response.choices[0].message.content.strip()
            
            if self.reasoning_model:
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            
            translation_match = re.search(r'<translation>\s*(.*?)\s*</translation>', 
                                       content, re.DOTALL)
            
            if translation_match:
                return translation_match.group(1).strip()
            return text

        except Exception as e:
            print(f"OpenAI translation error: {e}")
            return text 