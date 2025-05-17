import os
from functools import lru_cache
from typing import Any

from pydantic import (
    EmailStr,
    Field,
    PostgresDsn,
    SecretStr,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings


class APPSettings(BaseSettings):
    project_name: str = "vlep"
    enviroment: str = os.getenv("APP_ENVIROMENT") or "development"
    postgres_server: str = os.getenv("POSTGRES_SERVER") or "localhost"
    postgres_user: str = os.getenv("POSTGRES_USER") or "user-dev"
    postgres_password: SecretStr = Field(default=SecretStr("development"))
    postgres_port: int = int(os.getenv("POSTGRES_PORT") or 54321)
    postgres_db: str = os.getenv("POSTGRES_DB") or "appdb-dev"
    async_sqlalchemy_db_uri: PostgresDsn | None = None
    sa_pool_size: int = 5

    @field_validator("async_sqlalchemy_db_uri", mode="before")
    def assemble_async_db_connection(cls, v: str | None, info: ValidationInfo) -> str | PostgresDsn:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("postgres_user"),
            password=info.data.get("postgres_password").get_secret_value(), # type: ignore
            host=info.data.get("postgres_server"),
            port=info.data.get("postgres_port"),
            path=info.data.get("postgres_db"),
        )

    first_admin_email: EmailStr = os.getenv("FIRST_ADMIN_EMAIL") or "fake@email.com"
    token_secret_key: SecretStr = Field(default=SecretStr("fake"))
    email_confirmation_token_minutes: int = 15
    access_token_expire_minutes: int = 60 * 24 * 8
    algorithm: str = "HS256"
    cleanup_timeout: int = 5


@lru_cache()
def get_app_settings() -> APPSettings:
    return APPSettings()


app_settings = get_app_settings()
