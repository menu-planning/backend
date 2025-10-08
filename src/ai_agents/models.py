from enum import Enum, unique

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.grok import GrokProvider
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.anthropic import AnthropicModel

@unique
class LLMModel(str, Enum):
    OPENAI = "gpt-5-nano"
    OLLAMA = "llama3.1"
    XAI = "grok-4-fast-reasoning"
    MISTRAL = "mistral-small-latest"
    ANTHROPIC = "anthropic/claude-3-5-sonnet-20240620"
    DEEPSEEK = "deepseek-chat"

def get_ollama_model() -> OpenAIChatModel:
    return OpenAIChatModel(
        LLMModel.OLLAMA.value,
        provider=OllamaProvider(base_url='http://localhost:11434/v1'),
    )

def get_openai_model() -> OpenAIChatModel:
    return OpenAIChatModel(
        LLMModel.OPENAI.value
    )

def get_grok_model() -> OpenAIChatModel:
    return OpenAIChatModel(
        LLMModel.XAI.value,
        provider=GrokProvider(),
    )

def get_deepseek_model() -> OpenAIChatModel:
    return OpenAIChatModel(
        LLMModel.DEEPSEEK.value,
        provider=DeepSeekProvider(),
    )

def get_mistral_model() -> MistralModel:
    return MistralModel(
        LLMModel.MISTRAL.value,
    )

def get_anthropic_model() -> AnthropicModel:
    return AnthropicModel(
        LLMModel.MISTRAL.value,
    )