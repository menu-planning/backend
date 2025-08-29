from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from src.contexts.seedwork.shared.domain.commands.command import (
        Command as SeedworkCommand,
    )
    from src.contexts.seedwork.shared.domain.event import Event as SeedworkEvent

from functools import partial

from src.contexts.client_onboarding.core.domain import commands
from src.contexts.client_onboarding.core.services import (
    command_handlers as cmd_handlers,
)
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.services.webhooks.manager import WebhookManager
from src.contexts.shared_kernel.services.messagebus import MessageBus


def bootstrap(
    uow: UnitOfWork,
    webhook_manager: WebhookManager,
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
    injected_event_handlers: dict[type[SeedworkEvent], list[partial[Coroutine]]] = {}

    # Command handlers mapping commands to their handlers
    injected_command_handlers: dict[type[SeedworkCommand], partial[Coroutine]] = {
        commands.SetupOnboardingFormCommand: partial(
            cmd_handlers.setup_onboarding_form_handler,
            uow=uow,
            webhook_manager=webhook_manager,
        ),
        commands.UpdateWebhookUrlCommand: partial(
            cmd_handlers.update_webhook_url_handler,
            uow=uow,
            webhook_manager=webhook_manager,
        ),
        commands.DeleteOnboardingFormCommand: partial(
            cmd_handlers.delete_onboarding_form_handler,
            uow=uow,
            webhook_manager=webhook_manager,
        ),
        commands.ProcessWebhookCommand: partial(
            cmd_handlers.process_webhook_handler,
            uow=uow,
        ),
    }

    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
