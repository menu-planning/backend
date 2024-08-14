from collections.abc import Coroutine
from functools import partial

from src.contexts.iam.shared.domain import commands, events
from src.contexts.iam.shared.services import command_handlers as cmd_handlers
from src.contexts.iam.shared.services import event_handlers as evt_handlers
from src.contexts.iam.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager


def bootstrap(
    uow: UnitOfWork,
    aio_pika_manager: AIOPikaManager,
) -> MessageBus:
    injected_event_handlers: dict[type[events.Event], list[Coroutine]] = {
        # events.UserCreated: [
        #     partial(
        #         evt_handlers.publish_send_admin_new_user_notification,
        #         aio_pika_manager=aio_pika_manager,
        #     )
        # ],
    }

    injected_command_handlers: dict[type[commands.Command], Coroutine] = {
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
