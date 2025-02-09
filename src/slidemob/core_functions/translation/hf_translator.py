from typing import Optional
from .base import BaseTranslator
import requests
import json
import re


class HuggingFaceTranslator(BaseTranslator):
    def __init__(self, model: str, api_url: str, headers: dict):
        super().__init__(model=model, api_url=api_url, headers=headers)

    def translate(
        self, text: str, target_language: str, style_instructions: str = ""
    ) -> str:
        try:
            payload = {
                "inputs": self._create_prompt(text, target_language, style_instructions)
            }

            response = requests.post(
                self.api_url, headers=self.headers, json=payload, timeout=30
            )
            response.raise_for_status()

            return self._parse_response(response, text)

        except Exception as e:
            print(f"HuggingFace translation error: {e}")
            return text

    def _create_prompt(
        self, text: str, target_language: str, style_instructions: str
    ) -> str:
        return f"Translate to {target_language}: {text}\nStyle: {style_instructions}"

    def _parse_response(self, response: requests.Response, original_text: str) -> str:
        try:
            response_json = response.json()
            generated_text = response_json[0]["generated_text"]
            # Extract translation from between [/INST] tags if present
            if "[/INST]" in generated_text:
                generated_text = generated_text.split("[/INST]")[-1].strip()
            return generated_text
        except Exception:
            return original_text
