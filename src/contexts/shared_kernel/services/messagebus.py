from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import anyio
from src.config.api_config import api_settings
from src.contexts.seedwork.domain.commands.command import Command
from src.contexts.seedwork.domain.event import Event
from src.contexts.seedwork.services.uow import UnitOfWork
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Coroutine

TIMEOUT = api_settings.timeout

class MessageBus[U: UnitOfWork]:
    """Central orchestrator for command and event dispatching.

    Routes incoming messages to registered handler functions using AnyIO for
    concurrency and timeout/cancellation control. Maintains transaction boundaries
    through UnitOfWork integration.

    Attributes:
        uow: UnitOfWork instance for transaction management.
        event_handlers: Mapping of event types to handler function lists.
        command_handlers: Mapping of command types to single handler functions.

    Notes:
        Thread-safe: No. Async-safe: Yes. Requires active UnitOfWork context.
        Timeout: Configurable per message via api_settings.timeout.
    """

    def __init__(
        self,
        uow: U,
        event_handlers: dict[type[Event], list[partial[Coroutine]]],
        command_handlers: dict[type[Command], partial[Coroutine]],
    ):
        """Initialize the message bus with handlers and unit of work.

        Args:
            uow: UnitOfWork instance for transaction management.
            event_handlers: Mapping of event types to handler function lists.
            command_handlers: Mapping of command types to single handler functions.
        """
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    async def handle(self, message: Event | Command, timeout: int = TIMEOUT):
        """Process a single message by dispatching to appropriate handlers.

        Routes the message to either command or event handlers based on type.
        Commands execute with timeout protection; events execute without timeout.

        Args:
            message: Domain Command or Event instance to process.
            timeout: Per-message timeout in seconds (default: api_settings.timeout).

        Raises:
            TypeError: If message is not a Command or Event instance.
            TimeoutError: If command execution exceeds timeout.
            Exception: Any exception raised by command handlers.

        Side Effects:
            May emit new events during command processing.
        """
        if not isinstance(message, Command | Event):
            error_message = f"{message} is not a Command or Event"
            logger.error(
                "Invalid message type received",
                action="message_validation_error",
                message_type=type(message).__name__,
                error_message=error_message
            )
            raise TypeError(error_message)

        if isinstance(message, Command):
            await self._handle_command(message, timeout)
        elif isinstance(message, Event):
            await self._handle_event(message)

    async def _completed(self, handler, message: Event | Command):
        """Execute handler and process any new events emitted.

        Runs the provided handler with the message and collects any new events
        emitted during command processing for subsequent handling.

        Args:
            handler: Function to execute with the message.
            message: Command or Event instance to process.

        Side Effects:
            Processes new events emitted during command handling.
        """
        await handler(message)
        if isinstance(message, Command):
            new_events = self.uow.collect_new_events()
            for event in new_events:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self.handle, event)

    async def _handle_event(self, event: Event, timeout: int = TIMEOUT):
        """Dispatch an event to all subscribed handlers within a timeout.

        Executes all registered handlers for the event type concurrently.
        Handlers execute without timeout constraints but with error isolation.

        Args:
            event: Event instance to dispatch to handlers.
            timeout: Timeout in seconds (unused for events but kept for interface).

        Notes:
            Events execute without timeout protection. Errors in one handler
            do not affect other handlers for the same event.
        """
        with anyio.move_on_after(timeout) as scope:
            try:
                async with anyio.create_task_group() as tg:
                    for handler in self.event_handlers[type(event)]:
                        if isinstance(handler, partial):
                            handler_name = handler.func.__name__
                        else:
                            handler_name = handler.__name__
                        logger.debug(
                            "Handling event with handler",
                            action="event_handling",
                            event_type=type(event).__name__,
                            handler_name=handler_name
                        )
                        tg.start_soon(self._completed, handler, event)
            except* Exception as exc:
                logger.error(
                    "Exception occurred while handling event",
                    action="event_handling_error",
                    event_type=type(event).__name__,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    exc_info=True
                )
        if scope.cancel_called:
            pass

    async def _handle_command(self, command: Command, timeout: int = TIMEOUT):
        """Dispatch a command to its single handler within a timeout.

        Executes the registered handler for the command type with timeout
        protection and error propagation.

        Args:
            command: Command instance to dispatch to handler.
            timeout: Maximum execution time in seconds.

        Raises:
            TimeoutError: If command execution exceeds the allowed timeout.
            Exception: Any exception raised by the command handler.

        Notes:
            Commands execute with strict timeout protection. Handler exceptions
            are logged and re-raised for middleware handling.
        """
        logger.debug(
            "Handling command",
            action="command_handling",
            command_type=type(command).__name__
        )
        handler = self.command_handlers[type(command)]
        with anyio.move_on_after(timeout) as scope:
            try:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self._completed, handler, command)
            except* Exception as exc:
                logger.error(
                    "Exception occurred while handling command",
                    action="command_handling_error",
                    command_type=type(command).__name__,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    exc_info=True
                )
                # Re-raise the exception - let the middleware handle it
                raise
        if scope.cancel_called:
            error_message = f"Timeout handling command {command}"
            logger.error(
                "Command handling timeout",
                action="command_timeout_error",
                command_type=type(command).__name__,
                timeout_seconds=timeout,
                error_message=error_message
            )
            raise TimeoutError(error_message)
