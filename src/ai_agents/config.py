from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class AIAgentsSettings(BaseSettings):
    openai_api_key: str | None = None
    llm_model: str = "ollama/llama3.1:8b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

@lru_cache
def get_app_settings() -> AIAgentsSettings:
    return AIAgentsSettings()