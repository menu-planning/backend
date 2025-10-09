"""Update webhook URL command handler.

Handles updating webhook URLs for existing onboarding forms with proper
webhook lifecycle management and database persistence.
"""

from typing import Callable
from src.contexts.client_onboarding.core.domain.commands import (
    UpdateWebhookUrlCommand,
)
from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
    OnboardingForm,
)
from src.contexts.client_onboarding.core.services.webhooks.manager import WebhookManager
from src.logging.logger import get_logger

from ..uow import UnitOfWork

logger = get_logger(__name__)


async def update_webhook_url_handler(
    cmd: UpdateWebhookUrlCommand,
    uow: UnitOfWork,
    webhook_manager: WebhookManager,
) -> OnboardingForm:
    """Handle updating webhook URL for an existing onboarding form.

    Updates the webhook URL for an existing onboarding form by using the
    webhook manager's update method for proper webhook lifecycle management.
    The operation includes updating both the TypeForm webhook configuration
    and the database record.

    Args:
        cmd: Update command with form_id and new_webhook_url.
        uow: Unit of work for database operations.
        webhook_manager: Injected webhook manager service.

    Returns:
        Updated OnboardingForm with the new webhook URL.

    Raises:
        ValueError: If the onboarding form is not found.
        WebhookConfigurationError: For webhook update failures.
        TypeFormAPIError: For TypeForm API communication errors.
    """
    logger.info("Updating webhook URL for form", form_id=cmd.form_id)

    # Convert form_id to int if needed
    form_id = int(cmd.form_id) if isinstance(cmd.form_id, str) else cmd.form_id

    # Use webhook manager's update method for proper webhook lifecycle management
    async with webhook_manager:
        await webhook_manager.update_webhook_url(uow, form_id, cmd.new_webhook_url)

    # Get the updated form
    async with uow:
        form = await uow.onboarding_forms.get_by_id(form_id)
        if not form:
            raise ValueError(f"Onboarding form {cmd.form_id} not found")

        logger.info(
            f"Updated webhook URL for form {cmd.form_id} to {cmd.new_webhook_url}"
        )
        return form


