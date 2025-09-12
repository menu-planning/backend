"""Core application configuration management.

This module defines `APPSettings`, a Pydantic `BaseSettings` model that loads
core application configuration from environment variables. It provides database
connection settings, security parameters, and application metadata.
"""

import os
from functools import lru_cache

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
    """Core application settings loaded from environment variables.

    Attributes:
        project_name: Human-readable application name.
        enviroment: Current runtime environment name.
        postgres_server: PostgreSQL hostname or IP.
        postgres_user: PostgreSQL user name.
        postgres_password: PostgreSQL user password as a secret.
        postgres_port: PostgreSQL TCP port number.
        postgres_db: PostgreSQL database name.
        async_sqlalchemy_db_uri: Async SQLAlchemy DSN. If not provided, assembled
            by `assemble_async_db_connection`.
        sa_pool_size: SQLAlchemy connection pool size.
        first_admin_email: Bootstrap admin email address.
        token_secret_key: Symmetric secret used for signing tokens.
        email_confirmation_token_minutes: Minutes until email-confirm token expiry.
        access_token_expire_minutes: Minutes until access token expiry.
        algorithm: JWS/JWT signing algorithm.
        cleanup_timeout: Time in seconds for graceful cleanup operations.
    """

    project_name: str = "vlep"
    enviroment: str = os.getenv("APP_ENV") or "development"
    postgres_server: str = os.getenv("POSTGRES_SERVER") or "localhost"
    postgres_user: str = os.getenv("POSTGRES_USER") or "user-dev"
    postgres_password: SecretStr = Field(default=SecretStr("development"))
    postgres_port: int = int(os.getenv("POSTGRES_PORT") or 54321)
    postgres_db: str = os.getenv("POSTGRES_DB") or "appdb-dev"
    async_sqlalchemy_db_uri: PostgresDsn | None = None
    sa_pool_size: int = 5

    @field_validator("async_sqlalchemy_db_uri", mode="before")
    @classmethod
    def assemble_async_db_connection(
        cls, v: str | None, info: ValidationInfo
    ) -> str | PostgresDsn:
        """Build an async SQLAlchemy DSN when one is not provided.

        Args:
            v: Supplied DSN value, if any.
            info: Pydantic validation context with access to other fields.

        Returns:
            A fully-qualified PostgreSQL DSN suitable for async SQLAlchemy.
        """
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("postgres_user"),
            password=info.data.get("postgres_password").get_secret_value(),  # type: ignore
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


@lru_cache
def get_app_settings() -> APPSettings:
    """Return a cached `APPSettings` instance.

    Returns:
        A process-wide cached settings object.
    """
    return APPSettings()


app_settings = get_app_settings()
