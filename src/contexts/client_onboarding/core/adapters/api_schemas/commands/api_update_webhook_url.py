"""
API Command Schema: Update Webhook URL

Pydantic model for updating webhook URLs for existing onboarding forms.
Maps HTTP requests to domain commands for webhook URL updates.
"""

from pydantic import Field, HttpUrl
from src.contexts.client_onboarding.core.domain.commands.update_webhook_url import (
    UpdateWebhookUrlCommand,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)


class ApiUpdateWebhookUrl(BaseApiCommand[UpdateWebhookUrlCommand]):
    """API command schema for updating webhook URL for existing onboarding forms.

    Maps HTTP PUT/PATCH requests to domain UpdateWebhookUrlCommand.
    Updates the webhook endpoint URL for an existing form configuration.

    Attributes:
        form_id: Internal form ID to update (must be positive integer)
        new_webhook_url: New webhook URL (valid HTTP/HTTPS URL)

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        Updates existing webhook configuration without affecting form status.
    """

    form_id: int = Field(..., gt=0, description="Internal form ID to update")
    new_webhook_url: HttpUrl = Field(..., description="New webhook URL")

    def to_domain(self) -> UpdateWebhookUrlCommand:  # type: ignore[override]
        """Map API command to domain command.

        Returns:
            UpdateWebhookUrlCommand: Domain command for webhook URL update
        """
        return UpdateWebhookUrlCommand(
            form_id=str(self.form_id),
            new_webhook_url=str(self.new_webhook_url),
        )
