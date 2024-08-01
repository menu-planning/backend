import os
from functools import lru_cache

from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    max_concurrency: int = min(32, os.cpu_count() + 4)
    work_timeout: int = 20
    cleanup_timeout: int = 5
    model_config = SettingsConfigDict(case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
