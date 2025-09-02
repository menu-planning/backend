"""
API Command Schema: Process Webhook

Pydantic model for processing TypeForm webhook payloads.
Maps HTTP webhook requests to domain commands for webhook processing.
"""

from __future__ import annotations

from pydantic import Field, field_validator
from src.contexts.client_onboarding.core.domain.commands.process_webhook import (
    ProcessWebhookCommand,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)


class ApiProcessWebhook(BaseApiCommand[ProcessWebhookCommand]):
    """API command schema for processing TypeForm webhook payloads.

    Maps HTTP webhook requests to domain ProcessWebhookCommand.
    Handles raw JSON payload and HTTP headers with normalization.

    Attributes:
        payload: Raw JSON payload from webhook request (non-empty string)
        headers: HTTP headers from webhook request (normalized to lowercase keys)

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        Headers are normalized to lowercase for case-insensitive transport.
    """

    payload: str = Field(
        ..., min_length=1, description="Raw JSON payload from webhook request"
    )
    headers: dict[str, str] = Field(
        default_factory=dict, description="HTTP headers from webhook request"
    )

    @field_validator("headers")
    @classmethod
    def normalize_headers(cls, value: dict[str, str]) -> dict[str, str]:
        """Normalize headers to lowercase keys.

        Args:
            value: Headers dictionary to normalize

        Returns:
            Headers with lowercase keys for case-insensitive processing
        """
        return {str(k).lower(): v for k, v in (value or {}).items()}

    def to_domain(self) -> ProcessWebhookCommand:  # type: ignore[override]
        """Map API command to domain command.

        Returns:
            ProcessWebhookCommand: Domain command for webhook processing
        """
        return ProcessWebhookCommand(
            payload=self.payload,
            headers=self.headers,
        )
