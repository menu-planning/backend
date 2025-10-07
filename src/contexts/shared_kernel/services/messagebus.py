from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, Awaitable, Callable

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

class MessageBus[U: Callable[[],UnitOfWork]]:
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
        uow_factory: U,
        event_handlers: dict[type[Event], list[partial[Coroutine]]],
        command_handlers: dict[type[Command], partial[Coroutine]],
        *,
        spawn_fn: Callable[[Coroutine[Any, Any, None]], None] | None = None,
        limiter: anyio.CapacityLimiter | None = None,
    ):
        """Initialize the message bus with handlers and unit of work.

        Args:
            uow: UnitOfWork instance for transaction management.
            event_handlers: Mapping of event types to handler function lists.
            command_handlers: Mapping of command types to single handler functions.
        """
        self.uow_factory = uow_factory
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.spawn_fn = spawn_fn
        self.handler_limiter = limiter

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
        command: Command,
        *,
        cmd_timeout: int = CMD_TIMEOUT,
        event_timeout: int = EVENT_TIMEOUT,
    ):
        """Execute command and process generated events.

        Routes command to registered handler with timeout protection. Events
        generated during command execution are automatically processed after
        successful completion. Command failures prevent event processing.

        Args:
            command: Command instance to execute.
            cmd_timeout: Command execution timeout in seconds.
            event_timeout: Event handler timeout in seconds.

        Returns:
            None: Command executed successfully.

        Raises:
            TypeError: If command is not a Command instance.
            TimeoutError: If command execution exceeds cmd_timeout.
            Exception: Any exception raised by command handlers.

        Events:
            Events are collected from UnitOfWork after successful command
            execution and processed concurrently by all registered handlers.

        Side Effects:
            Publishes events to registered handlers. Event handler failures
            are logged but do not affect command execution or other handlers.
        """
        if not isinstance(command, Command):
            error_message = f"{command} is not a Command"
            logger.error(
                "Invalid message type received",
                action="message_validation_error",
                message_type=type(command).__name__,
                error_message=error_message,
            )
            raise TypeError(error_message)

        try:
            logger.debug(
                "Handling command",
                action="command_handling",
                command_type=type(command).__name__,
            )
            handler = self.command_handlers[type(command)]
        except KeyError:
            error_message = f"No handler found for command type {type(command).__name__}"
            logger.error(
                "No handler found for command type",
                action="command_handling_error",
                command_type=type(command).__name__,
                error_message=error_message,
            )
            raise KeyError(error_message)

        uow = self.uow_factory()
        try:
            with anyio.move_on_after(cmd_timeout) as scope:
                response = await handler(command, uow=uow)
            if scope.cancel_called:
                error_message = f"Timeout handling command {command}"
                raise TimeoutError(error_message)
        except Exception as exc:
            logger.error(
                "Command handler failed",
                action="command_handling_error",
                command_type=type(command).__name__,
                error_type=type(exc).__name__,
                error_message=str(exc),
                exc_info=True,
            )
            # Re-raise the exception - let the middleware handle it
            raise
        else:
            # handle only event that were generated during command execution
            # events generated during event handling are not handled
            event_list = list(uow.collect_new_events())

            if self.spawn_fn is not None:
                for ev in event_list:
                    for h in self.event_handlers.get(type(ev), []):
                        self.spawn_fn(
                            run_event_handler(h, ev, timeout_s=event_timeout, limiter=self.handler_limiter)
                        )
            else:
                async with anyio.create_task_group() as tg:
                    for ev in event_list:
                        for h in self.event_handlers.get(type(ev), []):
                            # Create a closure to capture the current values
                            async def _run_handler(handler=h, event=ev):
                                await run_event_handler(handler, event, timeout_s=event_timeout, limiter=self.handler_limiter)
                            tg.start_soon(_run_handler)
        return response

async def run_event_handler(
    handler: Callable[[Event], Awaitable[None]],
    event: Event,
    *,
    timeout_s: float,
    limiter: anyio.CapacityLimiter | None = None,
) -> None:
    """
    Runs ONE event handler with:
      - optional CapacityLimiter (global cap across handlers),
      - per-handler timeout (only this cancels it),
      - exception isolation (never lets errors escape).
    """
    async def _do() -> None:
        with anyio.move_on_after(timeout_s) as scope:
            try:
                await handler(event)
            except anyio.get_cancelled_exc_class():
                # If *our* timeout triggered, scope.cancel_called is True.
                # Treat as a timeout; swallow and return immediately (no further awaits).
                if scope.cancel_called:
                    return
                # Otherwise it's an external/parent cancel: re-raise.
                raise
            except BaseException as exc:
                logger.error(
                    "Event handler failed",
                    action="event_handling_error",
                    command_type=type(event).__name__,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    exc_info=True,
                )
                return
        if scope.cancel_called:
            error_message = f"Timeout handling event {event}"
            logger.warning(
                "Event handling timeout",
                action="event_timeout_error",
                event_type=type(event).__name__,
                timeout_seconds=timeout_s,
                error_message=error_message,
            )

    if limiter is not None:
        async with limiter:
            await _do()
    else:
        await _do()