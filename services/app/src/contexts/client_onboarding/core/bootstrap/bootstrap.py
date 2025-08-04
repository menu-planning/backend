from collections.abc import Coroutine
from functools import partial

from src.contexts.client_onboarding.core.domain import commands
from src.contexts.client_onboarding.core.services import command_handlers as cmd_handlers
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.services.event_publisher import RoutedEventPublisher
from src.contexts.client_onboarding.core.services.webhook_manager import WebhookManager
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.seedwork.shared.domain.commands.command import (
    Command as SeedworkCommand,
)
from src.contexts.seedwork.shared.domain.event import Event as SeedworkEvent


def bootstrap(
    uow: UnitOfWork,
    webhook_manager: WebhookManager,
    event_publisher: RoutedEventPublisher,
) -> MessageBus:
    """
    Bootstrap the client onboarding context with command and event handlers.
    
    Args:
        uow: Unit of Work instance for this context
        webhook_manager: Webhook manager service (injected by container)
        event_publisher: Event publisher service (injected by container)
        
    Returns:
        MessageBus: Configured message bus ready for use
    """
    
    # Event handlers - currently empty but ready for future cross-context integration
    injected_event_handlers: dict[type[SeedworkEvent], list[partial[Coroutine]]] = {
        # Example for future use:
        # events.OnboardingFormWebhookSetup: [
        #     partial(evt_handlers.notify_user_of_webhook_setup, uow=uow),
        # ],
        # events.ClientDataExtracted: [
        #     partial(evt_handlers.create_client_in_recipes_catalog, uow=uow),
        # ],
    }

    # Command handlers mapping commands to their handlers
    injected_command_handlers: dict[type[SeedworkCommand], partial[Coroutine]] = {
        commands.SetupOnboardingFormCommand: partial(
            cmd_handlers.setup_onboarding_form_handler, 
            uow=uow,
            webhook_manager=webhook_manager,
            event_publisher=event_publisher
        ),
        commands.UpdateWebhookUrlCommand: partial(
            cmd_handlers.update_webhook_url_handler,
            uow=uow,
            webhook_manager=webhook_manager,
            event_publisher=event_publisher
        ),
    }
    
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    ) 