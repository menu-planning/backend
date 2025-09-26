"""Setup onboarding form command handler.

Handles the setup of new onboarding forms with webhook integration,
including form validation, webhook creation, and database persistence.
"""

from typing import Callable
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
from src.logging.logger import get_logger

from ..uow import UnitOfWork

logger = get_logger(__name__)


async def setup_onboarding_form_handler(
    cmd: SetupOnboardingFormCommand,
    uow: UnitOfWork,
    webhook_manager: WebhookManager,
) -> tuple[OnboardingForm, WebhookInfo]:
    """Handle setup of new onboarding form with webhook integration.

    This handler follows the Application Service Events pattern (Option 1):
    1. Execute the business logic
    2. Manually publish events after successful operations

    Sets up a new onboarding form by validating TypeForm access, creating
    webhook configuration, and persisting the form record. Honors the
    auto_activate flag to control initial form status.

    Args:
        cmd: Setup command with user_id, typeform_id, and optional webhook_url.
        uow: Unit of work for database operations.
        webhook_manager: Injected webhook manager service.

    Returns:
        Tuple of (OnboardingForm, WebhookInfo) on success.

    Raises:
        TypeFormAPIError: For TypeForm API access or validation failures.
        WebhookConfigurationError: For webhook setup failures.
        ValueError: For invalid form configuration or ownership issues.
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


