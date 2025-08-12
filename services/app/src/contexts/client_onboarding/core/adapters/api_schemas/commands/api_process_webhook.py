from __future__ import annotations

from typing import Dict

from pydantic import Field, field_validator

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.client_onboarding.core.domain.commands.process_webhook import (
    ProcessWebhookCommand,
)


class ApiProcessWebhook(BaseApiCommand[ProcessWebhookCommand]):
    """
    API command for processing a Typeform webhook payload.

    Accepts raw JSON payload as a string and request headers. Normalizes
    headers to lowercase keys to account for case-insensitive transport.
    """

    payload: str = Field(..., min_length=1, description="Raw JSON payload from webhook request")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers from webhook request")

    @field_validator("headers")
    @classmethod
    def normalize_headers(cls, value: Dict[str, str]) -> Dict[str, str]:
        return {str(k).lower(): v for k, v in (value or {}).items()}

    def to_domain(self) -> ProcessWebhookCommand:  # type: ignore[override]
        return ProcessWebhookCommand(
            payload=self.payload,
            headers=self.headers,
        )


