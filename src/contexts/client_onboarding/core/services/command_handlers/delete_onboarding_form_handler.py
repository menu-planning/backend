"""Delete onboarding form command handler.

Handles the deletion (soft delete) of onboarding forms and their associated
webhook configurations with ownership verification.
"""

from src.contexts.client_onboarding.core.domain.commands.delete_onboarding_form import (
    DeleteOnboardingFormCommand,
)
from src.contexts.client_onboarding.core.services.webhooks.manager import WebhookManager
from src.logging.logger import StructlogFactory

from ..uow import UnitOfWork

logger = StructlogFactory.get_logger(__name__)


async def delete_onboarding_form_handler(
    cmd: DeleteOnboardingFormCommand,
    uow: UnitOfWork,
    webhook_manager: WebhookManager,
) -> bool:
    """Handle deletion (soft) of an onboarding form and its webhook configuration.

    Verifies form ownership before proceeding with deletion. Performs soft delete
    by marking the form as deleted and removing associated webhook configuration.

    Args:
        cmd: Delete command containing form_id and user_id.
        uow: Unit of work for database operations.
        webhook_manager: Webhook manager for webhook lifecycle operations.

    Returns:
        True if deletion was successful.

    Raises:
        ValueError: If form not found or user lacks ownership.
    """
    logger.info(
        f"Deleting onboarding form {cmd.form_id} for user {cmd.user_id}"
    )

    # Verify ownership
    async with uow:
        form = await uow.onboarding_forms.get_by_id(int(cmd.form_id))
        if not form:
            raise ValueError(f"Onboarding form {cmd.form_id} not found")
        if form.user_id != cmd.user_id:
            raise ValueError("Access denied: You do not own this form")

    # Delete webhook configuration and mark deleted
    deleted = await webhook_manager.delete_webhook_configuration(uow, cmd.form_id)
    return deleted


