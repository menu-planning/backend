import os
from functools import lru_cache
from typing import Any

from pydantic import AnyHttpUrl, ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    max_concurrency: int = min(32, os.cpu_count() + 4)
    port: int = os.getenv("SELENIUM_PORT") or 4444
    server: str = os.getenv("SELENIUM_SERVER") or "localhost"

    url: AnyHttpUrl | None = None

    @field_validator("url", mode="before")
    def assemble_selenium_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        return AnyHttpUrl.build(
            scheme="http",
            host=info.data.get("server"),
            port=info.data.get("port", None),
            path="/wd/hub",
        )

    work_timeout: int = 20
    cleanup_timeout: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
