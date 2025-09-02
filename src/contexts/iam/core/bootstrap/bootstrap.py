"""Bootstrap wiring for IAM message bus.

Builds a `MessageBus` with IAM command and event handlers registered.
"""

from collections.abc import Coroutine
from functools import partial

from src.contexts.iam.core.domain import commands, events
from src.contexts.iam.core.services import command_handlers as cmd_handlers
from src.contexts.iam.core.services import event_handlers as evt_handlers
from src.contexts.iam.core.services.uow import UnitOfWork
from src.contexts.seedwork.domain.commands.command import (
    Command as SeedworkCommand,
)
from src.contexts.seedwork.domain.event import Event as SeedworkEvent
from src.contexts.shared_kernel.services.messagebus import MessageBus


def bootstrap(
    uow: UnitOfWork,
) -> MessageBus:
    """Wire IAM command and event handlers into a MessageBus.
    
    Args:
        uow: UnitOfWork instance for transaction management.
        
    Returns:
        MessageBus: Configured message bus with IAM handlers registered.
        
    Notes:
        Registers command handlers for user creation and role management.
        Registers event handlers for user creation notifications.
    """
    injected_event_handlers: dict[type[SeedworkEvent], list[partial[Coroutine]]] = {
        events.UserCreated: [
            partial(
                evt_handlers.publish_send_admin_new_user_notification,
            )
        ],
    }

    injected_command_handlers: dict[type[SeedworkCommand], partial[Coroutine]] = {
        commands.CreateUser: partial(cmd_handlers.create_user, uow=uow),
        commands.AssignRoleToUser: partial(cmd_handlers.assign_role_to_user, uow=uow),
        commands.RemoveRoleFromUser: partial(
            cmd_handlers.remove_role_from_user, uow=uow
        ),
    }
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
