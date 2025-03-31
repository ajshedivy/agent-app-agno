from os import getenv
from agno.models.openai import OpenAIChat
from agno.models.ollama import Ollama
from agno.models.base import Model

OLLAMA_MODELS = ["qwen2.5:latest"]


def get_model(model_id: str) -> Model:
    if model_id in OLLAMA_MODELS:
        return Ollama(
            id=model_id,
            host=getenv("OLLAMA_API_BASE", "http://host.docker.internal:11434"),
        )
    else:
        return OpenAIChat(id=model_id)
