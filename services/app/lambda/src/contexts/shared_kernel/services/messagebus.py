from __future__ import annotations

import uuid
from collections.abc import Coroutine
from functools import partial

import anyio

# from fastapi.exceptions import RequestValidationError
from src.config.api_config import api_settings
from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.seedwork.shared.endpoints.exceptions import TimeoutException
from src.contexts.seedwork.shared.services.uow import UnitOfWork
from src.logging.logger import logger

TIMEOUT = api_settings.timeout


class MessageBus:
    """
    The message bus is responsible for dispatching commands and events to their handlers.
    It is the central point of the application where all messages are sent to be processed.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        event_handlers: dict[type[Event], list[Coroutine]],
        command_handlers: dict[type[Command], Coroutine],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    async def handle(self, message: Event | Command, timeout: int = TIMEOUT):
        if isinstance(message, Command):
            await self._handle_command(message, timeout)
        elif isinstance(message, Event):
            await self._handle_event(message)
        else:
            raise Exception(f"{message} is not a Command or Event")

    async def _completed(self, handler, message: Event | Command):
        await handler(message)
        if isinstance(message, Command):
            new_events = self.uow.collect_new_events()
            for event in new_events:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self.handle, event)

    def _extract_exception_that_has_fastapi_custom_handler(
        self, exc_group: ExceptionGroup
    ):
        """
        Extracts and re-raises specific exceptions that have a custom FastAPI exception handler.

        This is necessary because FastAPI exception handlers are not called when an exception is raised inside a
        sub-task of a task group. This method extracts the specific exception from the ExceptionGroup and re-raises it
        to ensure that the FastAPI exception handler is called.
        """
        specific_exceptions = (
            TimeoutError,
            ValueError,
            # RequestValidationError,
            EntityNotFoundException,
            MultipleEntitiesFoundException,
            Exception,
        )

        extracted_exception = None
        for exc in exc_group.exceptions:
            if isinstance(exc, specific_exceptions):
                extracted_exception = exc
                break  # Assume only one specific exception is to be handled

        if extracted_exception:
            raise extracted_exception from None
        else:
            raise exc_group  # Re-raise the original ExceptionGroup if no specific exception was found

    def _log_exception(self, message: Event | Command, exc: Exception):
        if isinstance(message, Event):
            logger.exception(f"Exception handling event {message}: {exc}")
        else:
            logger.exception(f"Exception handling command {message}: {exc}")

    async def _handle_event(self, event: Event, timeout: int = TIMEOUT):
        handlers = [handler for handler in self.event_handlers[type(event)]]
        with anyio.move_on_after(timeout) as scope:
            try:
                async with anyio.create_task_group() as tg:
                    for handler in handlers:
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
                if isinstance(exc, ExceptionGroup):
                    # Attempt to extract and re-raise specific exceptions directly
                    self._extract_exception_that_has_fastapi_custom_handler(exc)
                else:
                    raise
        if scope.cancel_called:
            logger.error("Timeout handling command %s", command)
            raise TimeoutException(f"Timeout handling command {command}")
