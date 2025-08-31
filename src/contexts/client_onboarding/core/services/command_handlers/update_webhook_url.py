"""
Update Webhook URL Command Handler

Split from the monolithic command_handlers module.
"""

from src.contexts.client_onboarding.core.domain.commands import (
    UpdateWebhookUrlCommand,
)
from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
    OnboardingForm,
)
from src.contexts.client_onboarding.core.services.webhooks.manager import WebhookManager
from src.logging.logger import StructlogFactory

from ..uow import UnitOfWork

logger = StructlogFactory.get_logger(__name__)


async def update_webhook_url_handler(
    cmd: UpdateWebhookUrlCommand,
    uow: UnitOfWork,
    webhook_manager: WebhookManager,
) -> OnboardingForm:
    """
    Handle updating webhook URL for an existing onboarding form.

    Args:
        cmd: Update command with form_id and new_webhook_url
        uow: Unit of work for database operations
        webhook_manager: Injected webhook manager service

    Returns:
        Updated OnboardingForm
    """
    logger.info("Updating webhook URL for form", form_id=cmd.form_id)

    # Convert form_id to int if needed
    form_id = int(cmd.form_id) if isinstance(cmd.form_id, str) else cmd.form_id

    # Use webhook manager's update method for proper webhook lifecycle management
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


