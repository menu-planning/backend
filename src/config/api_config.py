"""API configuration management.

This module defines `APISettings`, a Pydantic `BaseSettings` model that reads
API-related configuration from environment variables. It provides API routing,
documentation, CORS, and URL assembly based on environment.
"""

import os
from functools import lru_cache

from pydantic import AnyHttpUrl, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """Application API settings loaded from environment variables.

    Fields are loaded from environment variables using the "API" prefix.

    Attributes:
        api_v1_str: Base path for versioned API routes.
        debug: Enables debug features in the API layer.
        docs_url: Path where API documentation is served.
        openapi_prefix: Prefix prepended to OpenAPI endpoints.
        openapi_url: Path to the generated OpenAPI JSON.
        redoc_url: Path to ReDoc UI.
        title: Human-friendly API title.
        version: Application/API version.
        api_url: Absolute base URL for the API. If not provided, assembled by
            `assemble_api_url`.
        liveness_check_url: Health probe path.
        backend_cors_origins: Allowed CORS origins.
        timeout: Default request timeout in seconds.
    """
    model_config = SettingsConfigDict(env_prefix="API")
    api_v1_str: str = "/api/v1"
    debug: bool = False
    docs_url: str = "/docs"
    openapi_prefix: str = "/api/v1"
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    title: str = "FastAPI"
    version: str = "0.1.0"
    api_url: AnyHttpUrl | None = None

    # TODO: This is a hack to get around the fact that the API server is not
    #       running on the same port as the frontend server. This should be
    #       fixed by using a reverse proxy.
    @field_validator("api_url", mode="before")
    @classmethod
    def assemble_api_url(cls, v: str | None, info: ValidationInfo) -> str | AnyHttpUrl:
        """Assemble `api_url` from environment and settings.

        Args:
            v: Existing value supplied for `api_url`.
            info: Pydantic validation context with access to other fields.

        Returns:
            A fully-qualified API base URL as a string or `AnyHttpUrl`.
        """
        if isinstance(v, str):
            return v
        env = os.getenv("APP_ENVIRONMENT") or "production"
        if env == "production":
            return AnyHttpUrl.build(
                scheme="https",
                host=info.data.get("api_server", "vlep.io"),
                port=info.data.get("api_port", None),
            )
        else:
            return AnyHttpUrl.build(
                scheme="http",
                host=info.data.get("api_server", "vlep.io.test"),
                port=info.data.get("api_port", None),
            )

    liveness_check_url: str = "/liveness"

    backend_cors_origins: list[str] = [
        "https://10.0.2.2",
        "https://localhost",
        "https://127.0.0.1",
        "https://localhost:9000",
        "https://127.0.0.1:9000",
        "https://172.18.0.1:9000",
        "https://www.vlep.io",
        "https://vlep.io",
        "http://vlep.io.test",
        "http://www.vlep.io.test",
    ]
    timeout: int = 30

    # class Config:
    #     env_prefix = "API_"
    #     validate_assignment = True


@lru_cache
def get_api_settings() -> APISettings:
    """Return a cached `APISettings` instance.

    Returns:
        A process-wide cached settings object.
    """
    return APISettings()


api_settings = get_api_settings()
