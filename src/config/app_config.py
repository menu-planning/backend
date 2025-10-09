"""Core application configuration management.

This module defines `APPSettings`, a Pydantic `BaseSettings` model that loads
core application configuration from environment variables. It provides database
connection settings, security parameters, and application metadata.
"""

import os
from functools import lru_cache

from pydantic import (
    Field,
    PostgresDsn,
    SecretStr,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    database_url: str | None = os.getenv("DATABASE_URL")
    postgres_server: str = os.getenv("POSTGRES_SERVER") or "localhost"
    postgres_user: str = os.getenv("POSTGRES_USER") or "user-dev"
    postgres_password: SecretStr = Field(default=SecretStr("development"))
    postgres_port: int = int(os.getenv("POSTGRES_PORT") or 54321)
    postgres_db: str = os.getenv("POSTGRES_DB") or "appdb-dev"
    async_sqlalchemy_db_uri: PostgresDsn | None = None
    sa_pool_size: int = 5
    # FastAPI-specific database settings
    fastapi_pool_size: int = 10
    fastapi_max_overflow: int = 20
    fastapi_pool_pre_ping: bool = True
    fastapi_pool_recycle: int = 3600
    
    # Optimized HTTP client settings (for both FastAPI and Lambda)
    http_timeout_connect: float = 5.0
    http_timeout_read: float = 30.0
    http_timeout_write: float = 10.0
    http_timeout_pool: float = 5.0
    http_max_connections: int = 100
    http_max_keepalive: int = 50
    
    # Message bus timeout settings
    messagebus_cmd_timeout: int = int(os.getenv("MESSAGEBUS_CMD_TIMEOUT") or 10)
    messagebus_event_timeout: int = int(os.getenv("MESSAGEBUS_EVENT_TIMEOUT") or 10)
    
    # FastAPI development configuration
    fastapi_host: str = os.getenv("FASTAPI_HOST") or "0.0.0.0"
    fastapi_port: int = int(os.getenv("FASTAPI_PORT") or 8000)
    fastapi_reload: bool = os.getenv("FASTAPI_RELOAD", "true").lower() == "true"
    fastapi_debug: bool = os.getenv("FASTAPI_DEBUG", "false").lower() == "true"
    fastapi_api_prefix: str = os.getenv("FASTAPI_API_PREFIX") or "/v1"
    fastapi_docs_url: str = os.getenv("FASTAPI_DOCS_URL") or "/docs"
    fastapi_redoc_url: str = os.getenv("FASTAPI_REDOC_URL") or "/redoc"
    fastapi_openapi_url: str = os.getenv("FASTAPI_OPENAPI_URL") or "/openapi.json"
    fastapi_cors_origins_str: str = Field(
        default="*",
        alias="FASTAPI_CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins.",
    )
    fastapi_cors_origins: list[str] = Field(default_factory=list)
    fastapi_cors_allow_credentials: bool = True
    fastapi_cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    fastapi_cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    
    # Cognito authentication settings
    cognito_region: str = os.getenv("COGNITO_REGION") or "us-east-1"
    cognito_user_pool_id: str = os.getenv("COGNITO_USER_POOL_ID") or "us-east-1_EXAMPLE"
    cognito_client_id: str = os.getenv("COGNITO_CLIENT_ID") or "example-client-id"
    
    # Rate limiting settings
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable or disable rate limiting.",
        alias="RATE_LIMIT_ENABLED",
    )
    rate_limit_default: str = Field(
        default="100/minute",
        description="Default rate limit for all routes.",
        alias="RATE_LIMIT_DEFAULT",
    )
    
    @field_validator("fastapi_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str], info: ValidationInfo) -> list[str]:
        """Parse CORS origins from a comma-separated string."""
        if v and isinstance(v, list):
            return v

        origins_str = info.data.get("fastapi_cors_origins_str", "*")
        result = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
        return result

    # Dev mode authentication bypass settings
    dev_mode_auth_bypass: bool = os.getenv("DEV_MODE_AUTH_BYPASS", "false").lower() == "true"
    dev_user_id: str = os.getenv("DEV_USER_ID") or "dev-user-123"
    dev_user_email: str = os.getenv("DEV_USER_EMAIL") or "dev@localhost.dev"
    dev_user_roles: str = os.getenv("DEV_USER_ROLES") or "admin,user"

    @field_validator("async_sqlalchemy_db_uri", mode="before")
    @classmethod
    def assemble_async_db_connection(
        cls, v: str | None, info: ValidationInfo
    ) -> str | PostgresDsn:
        """
        Usa a DATABASE_URL se disponível (Railway), senão, constrói a partir
        das partes (desenvolvimento local).
        """
        # Prioridade 1: Usar a DATABASE_URL fornecida pelo Railway
        if database_url := info.data.get("database_url"):
            # Substitui o esquema para ser compatível com asyncpg
            return database_url.replace("postgresql://", "postgresql+asyncpg://")

        # Prioridade 2: Usar uma DSN já fornecida (se houver)
        if isinstance(v, str):
            return v
        
        # Prioridade 3: Construir a DSN para ambiente local
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("postgres_user"),
            password=info.data.get("postgres_password").get_secret_value(), # type: ignore
            host=info.data.get("postgres_server"),
            port=info.data.get("postgres_port"),
            path=info.data.get("postgres_db"),
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_app_settings() -> APPSettings:
    """Return a cached `APPSettings` instance.

    Returns:
        A process-wide cached settings object.
    """
    return APPSettings()
