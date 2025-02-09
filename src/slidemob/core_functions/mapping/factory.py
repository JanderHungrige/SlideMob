from typing import Optional
from .base import BaseMapper
from .openai_mapper import OpenAIMapper
from .hf_mapper import HuggingFaceMapper
from .azure_mapper import AzureMapper
from .lm_mapper import LMStudioMapper
from .deepseek_mapper import DeepSeekMapper

class MapperFactory:
    @staticmethod
    def create_mapper(method: str, model: str, client: Optional[any] = None,
                     api_url: Optional[str] = None, headers: Optional[dict] = None,
                     reasoning_model: bool = False, model_type: str = "unknown",
                     config: Optional[dict] = None) -> BaseMapper:
        if method == "OpenAI":
            return OpenAIMapper(model=model, client=client, reasoning_model=reasoning_model)
        elif method == "HuggingFace":
            return HuggingFaceMapper(model=model, api_url=api_url, headers=headers)
        elif method == "Azure OpenAI":
            return AzureMapper(model=model, client=client, reasoning_model=reasoning_model,
                             config=config)
        elif method == "LMStudio":
            return LMStudioMapper(model=model, client=client, model_type=model_type,
                                reasoning_model=reasoning_model)
        elif method == "DeepSeek":
            return DeepSeekMapper(model=model, client=client, reasoning_model=reasoning_model)
        else:
            raise ValueError(f"Unknown mapping method: {method}") 