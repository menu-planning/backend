"""API configuration management.

This module defines `APISettings`, a Pydantic `BaseSettings` model that reads
API-related configuration from environment variables. Currently used for
request timeout configuration in the message bus.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """Application API settings loaded from environment variables.

    Fields are loaded from environment variables using the "API" prefix.

    Attributes:
        timeout: Default request timeout in seconds.
    """
    model_config = SettingsConfigDict(env_prefix="API")
    timeout: int = 30


@lru_cache
def get_api_settings() -> APISettings:
    """Return a cached `APISettings` instance.

    Returns:
        A process-wide cached settings object.
    """
    return APISettings()


api_settings = get_api_settings()
