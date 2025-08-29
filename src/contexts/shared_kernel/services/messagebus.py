from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Generic, TypeVar

import anyio

from src.config.api_config import api_settings
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.seedwork.shared.services.uow import UnitOfWork
from src.logging.logger import logger

if TYPE_CHECKING:
    from collections.abc import Coroutine

TIMEOUT = api_settings.timeout

U = TypeVar("U", bound=UnitOfWork)


class MessageBus(Generic[U]):
    """
    The message bus is responsible for dispatching commands and events to their
    handlers.
    It is the central point of the application where all messages are sent to be
    processed.
    """

    def __init__(
        self,
        uow: U,
        event_handlers: dict[type[Event], list[partial[Coroutine]]],
        command_handlers: dict[type[Command], partial[Coroutine]],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    async def handle(self, message: Event | Command, timeout: int = TIMEOUT):
        if not isinstance(message, Command | Event):
            error_message = f"{message} is not a Command or Event"
            logger.error(error_message)
            raise TypeError(error_message)

        if isinstance(message, Command):
            await self._handle_command(message, timeout)
        elif isinstance(message, Event):
            await self._handle_event(message)

    async def _completed(self, handler, message: Event | Command):
        await handler(message)
        if isinstance(message, Command):
            new_events = self.uow.collect_new_events()
            for event in new_events:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self.handle, event)

    async def _handle_event(self, event: Event, timeout: int = TIMEOUT):
        with anyio.move_on_after(timeout) as scope:
            try:
                async with anyio.create_task_group() as tg:
                    for handler in self.event_handlers[type(event)]:
                        if isinstance(handler, partial):
                            handler_name = handler.func.__name__
                        else:
                            handler_name = handler.__name__
                        logger.debug(
                            f"Handling event {event} with handler {handler_name}"
                        )
                        tg.start_soon(self._completed, handler, event)
            except* Exception as exc:
                logger.exception(f"Exception handling event {event}: {exc}")
        if scope.cancel_called:
            pass

    async def _handle_command(self, command: Command, timeout: int = TIMEOUT):
        logger.debug(f"Handling command {command}")
        handler = self.command_handlers[type(command)]
        with anyio.move_on_after(timeout) as scope:
            try:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self._completed, handler, command)
            except* Exception as exc:
                logger.exception(f"Exception handling command {command}: {exc}")
                # Re-raise the exception - let the middleware handle it
                raise
        if scope.cancel_called:
            error_message = f"Timeout handling command {command}"
            raise TimeoutError(error_message)
