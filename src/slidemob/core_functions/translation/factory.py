
from .azure_translator import AzureTranslator
from .base import BaseTranslator
from .deepseek_translator import DeepSeekTranslator
from .google_translator import GoogleTranslator
from .hf_translator import HuggingFaceTranslator
from .lm_translator import LMStudioTranslator
from .openai_translator import OpenAITranslator

# Import other translators...


class TranslatorFactory:
    @staticmethod
    def create_translator(
        method: str,
        model: str,
        client: any | None = None,
        api_url: str | None = None,
        headers: dict | None = None,
        reasoning_model: bool = False,
        model_type: str = "unknown",
        config: dict | None = None,
    ) -> BaseTranslator:
        if method == "OpenAI":
            return OpenAITranslator(
                model=model, client=client, reasoning_model=reasoning_model
            )
        elif method == "Google":
            return GoogleTranslator()
        elif method == "Azure OpenAI":
            return AzureTranslator(
                model=model,
                client=client,
                reasoning_model=reasoning_model,
                config=config,
            )
        elif method == "HuggingFace":
            return HuggingFaceTranslator(model=model, api_url=api_url, headers=headers)
        elif method == "LMStudio":
            return LMStudioTranslator(
                model=model,
                client=client,
                model_type=model_type,
                reasoning_model=reasoning_model,
            )
        elif method == "DeepSeek":
            return DeepSeekTranslator(
                model=model, client=client, reasoning_model=reasoning_model
            )
        # Add other translators...
        else:
            raise ValueError(f"Unknown translation method: {method}")
