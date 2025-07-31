"""
Client Onboarding Command Handlers

Handles domain commands and publishes events using the Application Service Events pattern (Option 1).
"""

import logging
from typing import Tuple, Optional

from src.contexts.client_onboarding.models.onboarding_form import OnboardingForm
from src.contexts.client_onboarding.services.typeform_client import WebhookInfo
from src.contexts.client_onboarding.services.webhook_manager import WebhookManager
from src.contexts.client_onboarding.services.event_publisher import RoutedEventPublisher
from src.contexts.client_onboarding.core.domain.commands.setup_onboarding_form import SetupOnboardingFormCommand
from src.contexts.client_onboarding.core.domain.commands.update_webhook_url import UpdateWebhookUrlCommand
from src.contexts.client_onboarding.core.domain.events.onboarding_form_webhook_setup import OnboardingFormWebhookSetup
from .uow import UnitOfWork

logger = logging.getLogger(__name__)


async def setup_onboarding_form_handler(
    cmd: SetupOnboardingFormCommand,
    uow: UnitOfWork,
    webhook_manager: WebhookManager,
    event_publisher: RoutedEventPublisher
) -> Tuple[OnboardingForm, WebhookInfo]:
    """
    Handle setup of new onboarding form with webhook integration.
    
    This handler follows the Application Service Events pattern (Option 1):
    1. Execute the business logic
    2. Manually publish events after successful operations
    
    Args:
        cmd: Setup command with user_id, typeform_id, and optional webhook_url
        uow: Unit of work for database operations
        webhook_manager: Injected webhook manager service
        event_publisher: Publisher for application events
        
    Returns:
        Tuple of (OnboardingForm, WebhookInfo) on success
    """
    logger.info(f"Setting up onboarding form for user {cmd.user_id}, form {cmd.typeform_id}")
    
    # Execute the business logic using injected webhook manager
    result = await webhook_manager.setup_onboarding_form_webhook(
        uow=uow,
        user_id=cmd.user_id,
        typeform_id=cmd.typeform_id,
        webhook_url=cmd.webhook_url,
        validate_ownership=True
    )
    
    onboarding_form, webhook_info = result
    
    # Publish event after successful operation (Option 1 pattern)
    webhook_setup_event = OnboardingFormWebhookSetup(
        user_id=cmd.user_id,
        typeform_id=cmd.typeform_id,
        webhook_url=webhook_info.url,
        form_id=onboarding_form.id
    )
    
    published = await event_publisher.publish_event(webhook_setup_event)
    if published:
        logger.info(f"Published OnboardingFormWebhookSetup event for form {onboarding_form.id}")
    else:
        logger.warning(f"Failed to publish OnboardingFormWebhookSetup event for form {onboarding_form.id}")
    
    return result


async def update_webhook_url_handler(
    cmd: UpdateWebhookUrlCommand,
    uow: UnitOfWork,
    webhook_manager: WebhookManager,
    event_publisher: RoutedEventPublisher
) -> OnboardingForm:
    """
    Handle updating webhook URL for an existing onboarding form.
    
    Args:
        cmd: Update command with form_id and new_webhook_url
        uow: Unit of work for database operations
        webhook_manager: Injected webhook manager service
        event_publisher: Publisher for application events
        
    Returns:
        Updated OnboardingForm
    """
    logger.info(f"Updating webhook URL for form {cmd.form_id}")
    
    # Convert form_id to int if needed
    form_id = int(cmd.form_id) if isinstance(cmd.form_id, str) else cmd.form_id
    
    # Use webhook manager's update method for proper webhook lifecycle management
    webhook_info = await webhook_manager.update_webhook_url(uow, form_id, cmd.new_webhook_url)
    
    # Get the updated form
    async with uow:
        form = await uow.onboarding_forms.get_by_id(form_id)
        if not form:
            raise ValueError(f"Onboarding form {cmd.form_id} not found")
        
        logger.info(f"Updated webhook URL for form {cmd.form_id} to {cmd.new_webhook_url}")
        return form


# Legacy command classes for backward compatibility during transition
# These will be removed once all code is updated to use domain commands

class LegacySetupOnboardingFormCommand:
    """Legacy command class - use SetupOnboardingFormCommand instead."""
    
    def __init__(self, user_id: int, typeform_id: str, webhook_url: Optional[str] = None):
        self.user_id = user_id
        self.typeform_id = typeform_id
        self.webhook_url = webhook_url


class LegacyUpdateWebhookUrlCommand:
    """Legacy command class - use UpdateWebhookUrlCommand instead."""
    
    def __init__(self, form_id: str, new_webhook_url: str):
        self.form_id = form_id
        self.new_webhook_url = new_webhook_url 