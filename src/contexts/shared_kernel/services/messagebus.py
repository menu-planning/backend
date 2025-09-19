from __future__ import annotations

import copy
import time
from functools import partial
from typing import TYPE_CHECKING

import anyio
from src.config.api_config import api_settings
from src.contexts.seedwork.domain.commands.command import Command
from src.contexts.seedwork.domain.event import Event
from src.contexts.seedwork.services.uow import UnitOfWork
from src.logging.logger import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Coroutine

CMD_TIMEOUT = api_settings.cmd_timeout
EVENT_TIMEOUT = api_settings.event_timeout


class MessageBus[U: UnitOfWork]:
    """Execute command processing with automatic event dispatching.

    Routes commands to registered handlers with timeout protection and processes
    generated events concurrently. Events are only processed after successful
    command execution. Each event handler runs in isolation to prevent failure
    cascading.

    Args:
        uow: UnitOfWork instance for transaction management.
        event_handlers: Mapping of event types to handler function lists.
        command_handlers: Mapping of command types to single handler functions.

    Events:
        Events are automatically collected from UnitOfWork after successful
        command execution and processed concurrently by all registered handlers.

    Idempotency:
        No. Each command execution may generate different events based on
        current state and business rules.

    Transactions:
        One UnitOfWork per command. Events are processed within the same
        transaction context. Command failures prevent event processing.

    Side Effects:
        Publishes events to registered handlers. Each event handler runs
        in its own task group for complete isolation.

    Notes:
        Command-only interface: handle() only accepts Command objects.
        Event handler failures are logged but do not affect other handlers
        or command execution. Async-safe but not thread-safe.
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

    def _get_handler_name(self, handler) -> str:
        """Extract handler name for logging purposes.

        Args:
            handler: Event handler function (may be partial or regular function).

        Returns:
            String representation of handler name.
        """
        if isinstance(handler, partial):
            if hasattr(handler.func, "__name__"):
                return handler.func.__name__
            else:
                return handler.func.__class__.__name__
        else:
            if hasattr(handler, "__name__"):
                return handler.__name__
            else:
                return handler.__class__.__name__

    async def handle(
        self,
        message: Command,
        cmd_timeout: int = CMD_TIMEOUT,
        event_timeout: int = EVENT_TIMEOUT,
    ):
        """Execute command and process generated events.

        Routes command to registered handler with timeout protection. Events
        generated during command execution are automatically processed after
        successful completion. Command failures prevent event processing.

        Args:
            message: Command instance to execute.
            cmd_timeout: Command execution timeout in seconds.
            event_timeout: Event handler timeout in seconds.

        Returns:
            None: Command executed successfully.

        Raises:
            TypeError: If message is not a Command instance.
            TimeoutError: If command execution exceeds cmd_timeout.
            Exception: Any exception raised by command handlers.

        Events:
            Events are collected from UnitOfWork after successful command
            execution and processed concurrently by all registered handlers.

        Side Effects:
            Publishes events to registered handlers. Event handler failures
            are logged but do not affect command execution or other handlers.
        """
        if not isinstance(message, Command):
            error_message = f"{message} is not a Command"
            logger.error(
                "Invalid message type received",
                action="message_validation_error",
                message_type=type(message).__name__,
                error_message=error_message,
            )
            raise TypeError(error_message)

        try:
            await self._handle_command(message, cmd_timeout)
        except* Exception as exc:
            # Extract detailed error information from ExceptionGroup
            if isinstance(exc, ExceptionGroup):
                # This is an ExceptionGroup - extract individual exceptions
                error_details = []
                for i, sub_exc in enumerate(exc.exceptions):
                    error_details.append(
                        {
                            "index": i,
                            "type": type(sub_exc).__name__,
                            "message": str(sub_exc),
                            "traceback": sub_exc.__traceback__,
                        }
                    )
                logger.error(
                    "Exception occurred while handling command",
                    action="command_handling_error",
                    command_type=type(message).__name__,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    error_count=len(exc.exceptions),
                    error_details=error_details,
                    exc_info=True,
                )
            else:
                # Single exception
                logger.error(
                    "Exception occurred while handling command",
                    action="command_handling_error",
                    command_type=type(message).__name__,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    exc_info=True,
                )
            # Re-raise the exception - let the middleware handle it
            raise
        else:
            # handle only event that were generated during command execution
            # events generated during event handling are not handled
            event_list = list(self.uow.collect_new_events())
            await self._handle_events(event_list, event_timeout)

    async def _handle_events(
        self, event_list: list[Event], timeout: int = EVENT_TIMEOUT
    ):
        """Process all events from UnitOfWork with timeout protection.

        Dispatches each event to all registered handlers concurrently. Each
        handler runs in its own task group for complete isolation. Handler
        failures are logged but do not affect other handlers.

        Args:
            timeout: Maximum execution time per event handler in seconds.

        Side Effects:
            Calls all registered event handlers. Failures are logged but
            do not propagate or affect other handlers.
        """
        for event in event_list:
            with anyio.move_on_after(timeout, shield=True) as scope:
                async with anyio.create_task_group() as tg:
                    for handler in self.event_handlers[type(event)]:
                        logger.debug(
                            "Handling event",
                            action="event_handling",
                            lambda_event=event,
                            handler_name=self._get_handler_name(handler),
                        )
                        tg.start_soon(handler, event)
            if scope.cancel_called:
                error_message = f"Timeout handling event {event}"
                logger.error(
                    "Event handling timeout",
                    action="event_timeout_error",
                    event_type=type(event).__name__,
                    timeout_seconds=timeout,
                    error_message=error_message,
                )
            # for handler in self.event_handlers[type(event)]:
            #     logger.debug(
            #         "Handling event",
            #         action="event_handling",
            #         event_type=type(event).__name__,
            #         handler_name=self._get_handler_name(handler),
            #     )
            #     try:
            #         with anyio.move_on_after(timeout, shield=True) as scope:
            #             async with anyio.create_task_group() as tg:
            #                 tg.start_soon(handler, event)
            #     except* Exception as exc:
            #         # Log this specific event handler failure
            #         # Other event handlers continue unaffected
            #         handler_name = self._get_handler_name(handler)
            #         if isinstance(exc, ExceptionGroup):
            #             error_details = []
            #             for i, sub_exc in enumerate(exc.exceptions):
            #                 error_details.append(
            #                     {
            #                         "index": i,
            #                         "type": type(sub_exc).__name__,
            #                         "message": str(sub_exc),
            #                         "traceback": sub_exc.__traceback__,
            #                     }
            #                 )
            #             logger.error(
            #                 "Event handler failed",
            #                 action="event_handler_error",
            #                 event_type=type(event).__name__,
            #                 handler_name=handler_name,
            #                 error_type=type(exc).__name__,
            #                 error_message=str(exc),
            #                 error_count=len(exc.exceptions),
            #                 error_details=error_details,
            #                 exc_info=True,
            #             )
            #         else:
            #             logger.error(
            #                 "Event handler failed",
            #                 action="event_handler_error",
            #                 event_type=type(event).__name__,
            #                 handler_name=handler_name,
            #                 error_type=type(exc).__name__,
            #                 error_message=str(exc),
            #                 exc_info=True,
            #             )

    async def _handle_command(self, command: Command, timeout: int = CMD_TIMEOUT):
        """Dispatch a command to its single handler within a timeout.

        Executes the registered handler for the command type with timeout
        protection. Events generated by the command are processed in separate
        task groups to ensure independence from command execution.

        Args:
            command: Command instance to dispatch to handler.
            timeout: Maximum execution time in seconds.

        Raises:
            TimeoutError: If command execution exceeds the allowed timeout.
            Exception: Any exception raised by the command handler.

        Notes:
            Commands execute with strict timeout protection. Events are processed
            independently - their failures do not affect command execution.
            Handler exceptions are logged and re-raised for middleware handling.
        """
        logger.debug(
            "Handling command",
            action="command_handling",
            command_type=type(command).__name__,
        )
        handler = self.command_handlers[type(command)]

        with anyio.move_on_after(timeout) as scope:
            async with anyio.create_task_group() as tg:
                tg.start_soon(handler, command)

        if scope.cancel_called:
            error_message = f"Timeout handling command {command}"
            logger.error(
                "Command handling timeout",
                action="command_timeout_error",
                command_type=type(command).__name__,
                timeout_seconds=timeout,
                error_message=error_message,
            )
            raise TimeoutError(error_message)
