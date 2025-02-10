
from .azure_mapper import AzureMapper
from .base import BaseMapper
from .deepseek_mapper import DeepSeekMapper
from .hf_mapper import HuggingFaceMapper
from .lm_mapper import LMStudioMapper
from .openai_mapper import OpenAIMapper


class MapperFactory:
    @staticmethod
    def create_mapper(
        method: str,
        model: str,
        client: any | None = None,
        api_url: str | None = None,
        headers: dict | None = None,
        reasoning_model: bool = False,
        model_type: str = "unknown",
        config: dict | None = None,
    ) -> BaseMapper:
        if method == "OpenAI":
            return OpenAIMapper(
                model=model, client=client, reasoning_model=reasoning_model
            )
        elif method == "HuggingFace":
            return HuggingFaceMapper(model=model, api_url=api_url, headers=headers)
        elif method == "Azure OpenAI":
            return AzureMapper(
                model=model,
                client=client,
                reasoning_model=reasoning_model,
                config=config,
            )
        elif method == "LMStudio":
            return LMStudioMapper(
                model=model,
                client=client,
                model_type=model_type,
                reasoning_model=reasoning_model,
            )
        elif method == "DeepSeek":
            return DeepSeekMapper(
                model=model, client=client, reasoning_model=reasoning_model
            )
        else:
            raise ValueError(f"Unknown mapping method: {method}")
