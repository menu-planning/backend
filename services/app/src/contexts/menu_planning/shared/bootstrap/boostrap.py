from collections.abc import Coroutine
from functools import partial

from src.contexts.menu_planning.shared.domain import commands, events
from src.contexts.menu_planning.shared.services import command_handlers as cmd_handlers
from src.contexts.menu_planning.shared.services import event_handlers as evt_handlers
from src.contexts.menu_planning.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager


def bootstrap(
    uow: UnitOfWork,
    aio_pika_manager: AIOPikaManager,
) -> MessageBus:
    injected_event_handlers: dict[type[events.Event], list[Coroutine]] = {}

    # event handlers
    async def place_holder_handler(e) -> Coroutine:
        await evt_handlers.place_holder(e)

    injected_event_handlers[events.RecipeCreated] = [
        place_holder_handler,
    ]

    # Command handlers
    async def place_holder(c) -> Coroutine:
        await cmd_handlers.place_holder(c, uow)

    injected_command_handlers: dict[type[commands.Command], Coroutine] = {
        commands.CreateRecipe: partial(place_holder),
    }
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
