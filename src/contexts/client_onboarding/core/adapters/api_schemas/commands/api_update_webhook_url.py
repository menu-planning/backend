from pydantic import Field, HttpUrl

from src.contexts.client_onboarding.core.domain.commands.update_webhook_url import (
    UpdateWebhookUrlCommand,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)


class ApiUpdateWebhookUrl(BaseApiCommand[UpdateWebhookUrlCommand]):
    """API command to update webhook URL for an existing onboarding form."""

    form_id: int = Field(..., gt=0, description="ID of the form to update")
    new_webhook_url: HttpUrl = Field(..., description="New webhook URL")

    def to_domain(self) -> UpdateWebhookUrlCommand:  # type: ignore[override]
        return UpdateWebhookUrlCommand(
            form_id=str(self.form_id),
            new_webhook_url=str(self.new_webhook_url),
        )
