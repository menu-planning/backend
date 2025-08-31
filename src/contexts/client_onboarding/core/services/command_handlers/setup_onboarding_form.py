"""
Setup Onboarding Form Command Handler

Split from the monolithic command_handlers module.
"""

from typing import Tuple

from src.contexts.client_onboarding.core.domain.commands import (
    SetupOnboardingFormCommand,
)
from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
    OnboardingForm,
    OnboardingFormStatus,
)
from src.contexts.client_onboarding.core.services.integrations.typeform.client import (
    WebhookInfo,
)
from src.contexts.client_onboarding.core.services.webhooks.manager import WebhookManager
from src.logging.logger import StructlogFactory

from ..uow import UnitOfWork

logger = StructlogFactory.get_logger(__name__)


async def setup_onboarding_form_handler(
    cmd: SetupOnboardingFormCommand,
    uow: UnitOfWork,
    webhook_manager: WebhookManager,
) -> tuple[OnboardingForm, WebhookInfo]:
    """
    Handle setup of new onboarding form with webhook integration.

    This handler follows the Application Service Events pattern (Option 1):
    1. Execute the business logic
    2. Manually publish events after successful operations

    Args:
        cmd: Setup command with user_id, typeform_id, and optional webhook_url
        uow: Unit of work for database operations
        webhook_manager: Injected webhook manager service

    Returns:
        Tuple of (OnboardingForm, WebhookInfo) on success
    """
    logger.info(
        f"Setting up onboarding form for user {cmd.user_id}, form {cmd.typeform_id}"
    )

    # Execute the business logic using injected webhook manager
    result = await webhook_manager.setup_onboarding_form_webhook(
        uow=uow,
        user_id=cmd.user_id,
        typeform_id=cmd.typeform_id,
        webhook_url=cmd.webhook_url,
        validate_ownership=True,
    )

    onboarding_form, _ = result

    # Honor auto_activate flag from command by setting status to DRAFT when requested
    if hasattr(cmd, "auto_activate") and not cmd.auto_activate:
        async with uow:
            form = await uow.onboarding_forms.get_by_id(onboarding_form.id)
            if form:
                form.status = OnboardingFormStatus.DRAFT
                await uow.commit()

    return result


