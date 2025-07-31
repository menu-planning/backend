"""
Configuration for Client Onboarding Context

Settings for TypeForm API integration, webhook security, and AWS Lambda deployment.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientOnboardingConfig(BaseSettings):
    """Configuration settings for client onboarding services."""
    
    # TypeForm API Configuration
    typeform_api_key: str = os.getenv("TYPEFORM_API_KEY", "")
    typeform_api_base_url: str = "https://api.typeform.com"
    typeform_api_version: str = "v1"
    typeform_rate_limit_requests_per_second: int = 2  # Changed from 4 to 2 for TypeForm API compliance
    typeform_timeout_seconds: int = 30
    
    # Webhook Configuration
    typeform_webhook_secret: str = os.getenv("TYPEFORM_WEBHOOK_SECRET", "")
    webhook_endpoint_url: str = os.getenv("WEBHOOK_ENDPOINT_URL", "")
    webhook_timeout_seconds: int = 30
    
    # Security Settings
    webhook_signature_header: str = "Typeform-Signature"
    max_webhook_payload_size: int = 1024 * 1024  # 1MB
    
    # Database Settings
    enable_response_encryption: bool = True
    response_retention_days: int = 365
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Allow extra env vars to be ignored
    )


# Global configuration instance
config = ClientOnboardingConfig() 