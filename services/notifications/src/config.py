import os
from functools import lru_cache

from pydantic import EmailStr, Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    max_concurrency: int = min(32, os.cpu_count() + 4)
    first_admin_email: EmailStr = os.getenv("FIRST_ADMIN_EMAIL")
    # smtp_http_port: int = os.getenv("SMTP_HTTP_PORT")
    smtp_port: int = os.getenv("SMTP_PORT")
    smtp_host: str = os.getenv("SMTP_HOST")
    smtp_user: str = os.getenv("SMTP_USER")
    smtp_password: SecretStr = Field(...)
    smtp_tls: bool = os.getenv("SMTP_TLS")
    work_timeout: int = 30
    cleanup_timeout: int = 5


@lru_cache()
def get_app_settings() -> Settings:
    return Settings()


settings = get_app_settings()
