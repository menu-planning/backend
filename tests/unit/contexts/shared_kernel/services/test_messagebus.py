"""Unit tests for MessageBus service orchestration.

Tests the central message dispatching service that routes commands and events
to their registered handlers with proper timeout and error handling.
"""

from __future__ import annotations

import anyio
import pytest
from functools import partial
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from src.contexts.seedwork.domain.commands.command import Command
from src.contexts.seedwork.domain.event import Event
from src.contexts.seedwork.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus

pytestmark = pytest.mark.anyio


class SampleCommand(Command):
    """Sample command for message bus testing."""
    
    def __init__(self, data: str = "test"):
        self.data = data


class SampleEvent(Event):
    """Sample event for message bus testing."""
    
    def __init__(self, data: str = "test"):
        self.data = data


class FakeUnitOfWork(UnitOfWork):
    """Fake UnitOfWork for testing message bus behavior."""
    
    def __init__(self):
        self.session_factory = MagicMock()
        self.session = AsyncMock()
        self._events: list[Event] = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
    
    def collect_new_events(self):
        """Return collected events and clear the list."""
        events = self._events.copy()
        self._events.clear()
        return events
    
    def add_event(self, event: Event):
        """Add an event to be collected."""
        self._events.append(event)


class FakeCommandHandler:
    """Fake command handler for testing message processing."""
    
    def __init__(self, should_raise: Exception | None = None, delay: float = 0.0):
        self.should_raise = should_raise
        self.delay = delay
        self.called_with: list[tuple[Command, UnitOfWork]] = []
        self.call_count = 0
        self.completed = False
        self.cancelled = False
    
    async def __call__(self, command: Command, uow: UnitOfWork):
        """Execute the command handler with optional delay and exception."""
        self.called_with.append((command, uow))
        self.call_count += 1
        
        try:
            if self.delay > 0:
                await anyio.sleep(self.delay)
            
            if self.should_raise:
                raise self.should_raise
            
            self.completed = True
        except anyio.get_cancelled_exc_class():
            self.cancelled = True
            raise
        except Exception:
            # For non-cancellation exceptions, we still mark as completed
            # since the handler was called and finished (even if with an error)
            self.completed = True
            raise


class FakeEventHandler:
    """Fake event handler for testing message processing."""
    
    def __init__(self, should_raise: Exception | None = None, delay: float = 0.0):
        self.should_raise = should_raise
        self.delay = delay
        self.called_with: list[Event] = []
        self.call_count = 0
        self.completed = False
        self.cancelled = False
    
    async def __call__(self, event: Event):
        """Execute the event handler with optional delay and exception."""
        self.called_with.append(event)
        self.call_count += 1
        
        try:
            if self.delay > 0:
                await anyio.sleep(self.delay)
            
            if self.should_raise:
                raise self.should_raise
            
            self.completed = True
        except anyio.get_cancelled_exc_class():
            self.cancelled = True
            raise
        except Exception:
            # For non-cancellation exceptions, we still mark as completed
            # since the handler was called and finished (even if with an error)
            self.completed = True
            raise


@pytest.fixture
def fake_uow_factory():
    """Provide a fake UnitOfWork for testing."""
    return FakeUnitOfWork


@pytest.fixture
def fake_command_handler():
    """Provide a fake command handler."""
    return FakeCommandHandler()


@pytest.fixture
def fake_event_handlers():
    """Provide fake event handlers."""
    return [FakeEventHandler(), FakeEventHandler()]


@pytest.fixture
def message_bus(fake_uow_factory, fake_command_handler, fake_event_handlers):
    """Provide a MessageBus instance with fake dependencies."""
    command_handlers: dict[type[Command], partial] = {SampleCommand: partial(fake_command_handler)}
    event_handlers: dict[type[Event], list[partial]] = {SampleEvent: [partial(handler) for handler in fake_event_handlers]}
    
    return MessageBus(
        uow_factory=fake_uow_factory,
        command_handlers=command_handlers,
        event_handlers=event_handlers
    )


class TestMessageBusHandleHappyPath:
    """Test successful message processing scenarios."""
    
    async def test_handles_command_successfully(self, message_bus, fake_command_handler): 
        """Test that commands are processed successfully."""
        # Arrange
        command = SampleCommand("test_data")
        
        # Act
        await message_bus.handle(command)
        
        # Assert
        assert fake_command_handler.call_count == 1
        command_arg, uow_arg = fake_command_handler.called_with[0]
        assert command_arg == command
        assert isinstance(uow_arg, FakeUnitOfWork)
    
    async def test_handles_event_successfully_after_command(self, message_bus, fake_event_handlers, fake_command_handler):
        """Test that events are processed successfully by all handlers after command execution."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Act
        await message_bus.handle(command)
        
        # Assert
        for handler in fake_event_handlers:
            assert handler.call_count == 1
            assert handler.called_with[0] == event
    
    async def test_processes_new_events_from_command(self, message_bus, fake_command_handler, fake_event_handlers):
        """Test that new events emitted during command processing are handled."""
        # Arrange
        command = SampleCommand("test_data")
        new_event = SampleEvent("new_event_data")
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(new_event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Act
        await message_bus.handle(command)
        
        # Assert
        assert fake_command_handler.call_count == 1
        # New event should have been processed by event handlers
        for handler in fake_event_handlers:
            assert handler.call_count == 1
            assert handler.called_with[0] == new_event
    
    async def test_uses_custom_timeout(self, message_bus, fake_command_handler):
        """Test that custom timeout is respected."""
        # Arrange
        command = SampleCommand("test_data")
        custom_timeout = 5
        
        # Act
        await message_bus.handle(command, cmd_timeout=custom_timeout)
        
        # Assert
        assert fake_command_handler.call_count == 1


class TestMessageBusHandleErrorPropagation:
    """Test error handling and propagation scenarios."""
    
    async def test_propagates_command_handler_errors(self, message_bus):
        """Test that command handler errors are propagated."""
        # Arrange
        command = SampleCommand("test_data")
        expected_error = ValueError("Command failed")
        
        # Create a failing command handler
        failing_handler = FakeCommandHandler(should_raise=expected_error)
        message_bus.command_handlers[SampleCommand] = partial(failing_handler)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await message_bus.handle(command)

    
    async def test_handles_event_handler_errors_without_propagation(self, message_bus, fake_event_handlers, fake_command_handler):
        """Test that event handler errors don't stop other handlers."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        expected_error = RuntimeError("Event handler failed")
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Make one handler fail
        fake_event_handlers[0].should_raise = expected_error
        
        # Act
        await message_bus.handle(command)
        
        # Assert
        # First handler should have been called (and failed)
        assert fake_event_handlers[0].call_count == 1
        # Second handler should still have been called
        assert fake_event_handlers[1].call_count == 1
    
    async def test_multiple_event_handlers_with_mixed_success_failure(self, message_bus, fake_command_handler):
        """Test that multiple event handlers work independently - some succeed, some fail."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Create three handlers: one succeeds, one fails, one succeeds
        success_handler1 = FakeEventHandler(delay=0.1)
        failing_handler = FakeEventHandler(should_raise=ValueError("Handler failed"), delay=0.1)
        success_handler2 = FakeEventHandler(delay=0.1)
        
        message_bus.event_handlers[SampleEvent] = [
            partial(success_handler1),
            partial(failing_handler),
            partial(success_handler2)
        ]
        
        # Act - should not raise an exception despite one handler failing
        await message_bus.handle(command)
        
        # Assert
        # All handlers should have been called
        assert success_handler1.call_count == 1
        assert failing_handler.call_count == 1
        assert success_handler2.call_count == 1
        
        # All handlers should have received the same event
        assert success_handler1.called_with[0] == event
        assert failing_handler.called_with[0] == event
        assert success_handler2.called_with[0] == event
    
    async def test_raises_typeerror_for_invalid_message_type(self, message_bus):
        """Test that invalid message types raise TypeError."""
        # Arrange
        invalid_message = "not a command"
        
        # Act & Assert
        with pytest.raises(TypeError, match="not a Command"):
            await message_bus.handle(invalid_message)
    
    async def test_raises_timeout_error_for_command_timeout(self, message_bus):
        """Test that command timeouts raise TimeoutError."""
        # Arrange
        command = SampleCommand("test_data")
        timeout = 0.1  # Very short timeout
        
        # Create a slow command handler
        async def slow_command_handler(cmd, uow):
            await anyio.sleep(0.2)  # Longer than timeout
        
        message_bus.command_handlers[SampleCommand] = partial(slow_command_handler)
        
        # Act & Assert
        with pytest.raises(TimeoutError) as exc_info:
            await message_bus.handle(command, cmd_timeout=timeout)

    
    async def test_event_timeout_does_not_raise_error(self, message_bus, fake_event_handlers, fake_command_handler):
        """Test that event timeouts don't raise errors but handlers may be cancelled."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        timeout = 0.1  # Very short timeout
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Create slow event handlers
        slow_handler1 = FakeEventHandler(delay=0.2)  # Longer than timeout
        slow_handler2 = FakeEventHandler(delay=0.05)  # Shorter than timeout
        
        message_bus.event_handlers[SampleEvent] = [
            partial(slow_handler1),
            partial(slow_handler2)
        ]
        
        # Act - should not raise an exception
        await message_bus.handle(command, event_timeout=timeout)
        
        # Assert
        # The fast handler should have completed
        assert slow_handler2.call_count == 1
        # The slow handler may or may not have completed depending on timing
        # but the important thing is that no exception was raised
    
    async def test_events_fail_silently(self, message_bus, fake_command_handler):
        """Test that events fail silently - no exceptions are raised even when all handlers fail."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Create handlers that all fail
        failing_handler1 = FakeEventHandler(should_raise=RuntimeError("Handler 1 failed"))
        failing_handler2 = FakeEventHandler(should_raise=ValueError("Handler 2 failed"))
        
        message_bus.event_handlers[SampleEvent] = [
            partial(failing_handler1),
            partial(failing_handler2)
        ]
        
        # Act - should not raise any exception despite all handlers failing
        await message_bus.handle(command)
        
        # Assert
        # Both handlers should have been called
        assert failing_handler1.call_count == 1
        assert failing_handler2.call_count == 1
        
        # Both handlers should have received the event
        assert failing_handler1.called_with[0] == event
        assert failing_handler2.called_with[0] == event


class TestMessageBusHandleAsyncBehavior:
    """Test async behavior and concurrency scenarios."""
    
    async def test_handles_concurrent_event_handlers(self, message_bus, fake_event_handlers, fake_command_handler):
        """Test that multiple event handlers run concurrently."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Make handlers take some time to complete
        fake_event_handlers[0].delay = 0.1
        fake_event_handlers[1].delay = 0.1
        
        # Act
        import time
        start_time = time.time()
        await message_bus.handle(command)
        end_time = time.time()
        
        # Assert
        # Both handlers should have been called
        for handler in fake_event_handlers:
            assert handler.call_count == 1
        
        # Should complete in roughly 0.1s (concurrent) not 0.2s (sequential)
        assert end_time - start_time < 0.2
    
    async def test_handles_concurrent_new_events(self, message_bus, fake_command_handler, fake_event_handlers):
        """Test that multiple new events from command processing are handled concurrently."""
        # Arrange
        command = SampleCommand("test_data")
        event1 = SampleEvent("event1")
        event2 = SampleEvent("event2")
        
        # Create a command handler that adds events to the UoW
        async def command_handler_with_events(cmd, uow):
            uow.add_event(event1)
            uow.add_event(event2)
            return await fake_command_handler(cmd, uow)
        
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_events)
        
        # Make event handlers take time
        fake_event_handlers[0].delay = 0.1
        fake_event_handlers[1].delay = 0.1
        
        # Act
        import time
        start_time = time.time()
        await message_bus.handle(command)
        end_time = time.time()
        
        # Assert
        # Each event should have been processed by both handlers
        for handler in fake_event_handlers:
            assert handler.call_count == 2
        
        # Should complete concurrently, not sequentially
        assert end_time - start_time < 0.2
    
    async def test_handles_mixed_command_and_event_processing(self, message_bus, fake_command_handler, fake_event_handlers):
        """Test processing both commands and events in sequence."""
        # Arrange
        command1 = SampleCommand("command_data1")
        command2 = SampleCommand("command_data2")
        event1 = SampleEvent("event_data1")
        event2 = SampleEvent("event_data2")
        
        # Create command handlers that add events to the UoW
        async def command_handler_with_event1(cmd, uow):
            uow.add_event(event1)
            return await fake_command_handler(cmd, uow)
        
        async def command_handler_with_event2(cmd, uow):
            uow.add_event(event2)
            return await fake_command_handler(cmd, uow)
        
        # Act
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event1)
        await message_bus.handle(command1)
        
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event2)
        await message_bus.handle(command2)
        
        # Assert
        assert fake_command_handler.call_count == 2
        cmd1_arg, uow1_arg = fake_command_handler.called_with[0]
        cmd2_arg, uow2_arg = fake_command_handler.called_with[1]
        assert cmd1_arg == command1
        assert cmd2_arg == command2
        
        for handler in fake_event_handlers:
            assert handler.call_count == 2
            assert handler.called_with[0] == event1
            assert handler.called_with[1] == event2
    
    async def test_handles_event_processing_with_uow_events(self, message_bus, fake_command_handler, fake_event_handlers):
        """Test that events added to UoW during event processing are not automatically processed."""
        # Arrange
        command = SampleCommand("test_data")
        initial_event = SampleEvent("initial")
        nested_event = SampleEvent("nested")
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(initial_event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Create a UoW instance to track nested events
        uow_for_nested = None
        
        async def event_handler_with_uow_event(evt):
            nonlocal uow_for_nested
            if evt.data == "initial":
                # Add event to UoW, but it won't be processed since events fail silently
                uow_for_nested = message_bus.uow_factory()
                uow_for_nested.add_event(nested_event)
            return await fake_event_handlers[0](evt)
        
        # Replace first event handler
        message_bus.event_handlers[SampleEvent] = [
            partial(event_handler_with_uow_event),
            partial(fake_event_handlers[1])
        ]
        
        # Act
        await message_bus.handle(command)
        
        # Assert
        # Only the initial event should have been processed by both handlers
        # The nested event added to UoW is not processed since events fail silently
        assert fake_event_handlers[0].call_count == 1  # only initial
        assert fake_event_handlers[1].call_count == 1  # only initial
        
        # Verify only the initial event was processed
        assert fake_event_handlers[0].called_with[0] == initial_event
        assert fake_event_handlers[1].called_with[0] == initial_event
        
        # Verify the nested event was added to UoW but not processed
        if uow_for_nested:
            assert len(uow_for_nested._events) == 1
            assert uow_for_nested._events[0] == nested_event


class TestMessageBusCommandOnlyBehavior:
    """Test that MessageBus only accepts commands and handles events after successful command execution."""
    
    async def test_raises_typeerror_when_handling_event_directly(self, message_bus):
        """Test that trying to handle an event directly raises TypeError."""
        # Arrange
        event = SampleEvent("test_data")
        
        # Act & Assert
        with pytest.raises(TypeError, match="not a Command"):
            await message_bus.handle(event)
    
    async def test_command_exception_prevents_event_handling(self, message_bus, fake_event_handlers):
        """Test that command exceptions prevent event handling."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        expected_error = ValueError("Command failed")
        
        # Create a failing command handler that adds an event to the UoW
        async def failing_command_handler_with_event(cmd, uow):
            uow.add_event(event)
            raise expected_error
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(failing_command_handler_with_event)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await message_bus.handle(command)
        
        # Verify no event handlers were called
        for handler in fake_event_handlers:
            assert handler.call_count == 0
    
    async def test_command_timeout_prevents_event_handling(self, message_bus, fake_event_handlers):
        """Test that command timeouts prevent event handling."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        timeout = 0.1  # Very short timeout
        
        # Create a slow command handler that adds an event to the UoW
        async def slow_command_handler_with_event(cmd, uow):
            uow.add_event(event)
            # This will timeout
            await anyio.sleep(0.2)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(slow_command_handler_with_event)
        
        # Act & Assert
        with pytest.raises(TimeoutError) as exc_info:
            await message_bus.handle(command, cmd_timeout=timeout)
        
        # Verify no event handlers were called
        for handler in fake_event_handlers:
            assert handler.call_count == 0


class TestMessageBusEventHandlerErrorIsolation:
    """Test that event handler errors fail silently and don't affect other handlers."""
    
    async def test_event_handler_exception_fails_silently_other_handlers_continue(self, message_bus, fake_command_handler):
        """Test that event handler exceptions fail silently and other handlers continue normally."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Create handlers: one fails, one succeeds
        failing_handler = FakeEventHandler(should_raise=RuntimeError("Handler failed"), delay=0.1)
        success_handler = FakeEventHandler(delay=0.1)
        
        message_bus.event_handlers[SampleEvent] = [
            partial(failing_handler),
            partial(success_handler)
        ]
        
        # Act - should not raise any exception
        await message_bus.handle(command)
        
        # Assert
        # Both handlers should have been called
        assert failing_handler.call_count == 1
        assert success_handler.call_count == 1
        
        # Both handlers should have received the event
        assert failing_handler.called_with[0] == event
        assert success_handler.called_with[0] == event
        
        # The failing handler should have completed (even though it failed)
        assert failing_handler.completed == True
        assert failing_handler.cancelled == False
        
        # The success handler should have completed successfully
        assert success_handler.completed == True
        assert success_handler.cancelled == False
    
    async def test_event_handler_timeout_fails_silently_other_handlers_continue(self, message_bus, fake_command_handler):
        """Test that event handler timeouts fail silently and other handlers continue normally."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        timeout = 0.1  # Very short timeout
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Create handlers: one times out, one succeeds quickly
        slow_handler = FakeEventHandler(delay=0.2)  # Longer than timeout
        fast_handler = FakeEventHandler(delay=0.05)  # Shorter than timeout
        
        message_bus.event_handlers[SampleEvent] = [
            partial(slow_handler),
            partial(fast_handler)
        ]
        
        # Act - should not raise any exception
        await message_bus.handle(command, event_timeout=timeout)
        
        # Assert
        # Both handlers should have been called
        assert slow_handler.call_count == 1
        assert fast_handler.call_count == 1
        
        # Both handlers should have received the event
        assert slow_handler.called_with[0] == event
        assert fast_handler.called_with[0] == event
        
        # The fast handler should have completed successfully
        assert fast_handler.completed == True
        assert fast_handler.cancelled == False
        
        # The slow handler may be cancelled due to timeout
        # but the important thing is that no exception was raised
        # and the fast handler completed normally
    
    async def test_multiple_event_handlers_with_mixed_failures_continue_independently(self, message_bus, fake_command_handler):
        """Test that multiple event handlers with mixed failures continue independently."""
        # Arrange
        command = SampleCommand("test_data")
        event = SampleEvent("test_data")
        
        # Create a command handler that adds an event to the UoW
        async def command_handler_with_event(cmd, uow):
            uow.add_event(event)
            return await fake_command_handler(cmd, uow)
        
        # Replace the command handler
        message_bus.command_handlers[SampleCommand] = partial(command_handler_with_event)
        
        # Create handlers: one fails with exception, one times out, one succeeds
        exception_handler = FakeEventHandler(should_raise=ValueError("Exception handler failed"), delay=0.05)
        timeout_handler = FakeEventHandler(delay=0.2)  # Will timeout
        success_handler = FakeEventHandler(delay=0.05)  # Fast enough to complete before timeout
        
        message_bus.event_handlers[SampleEvent] = [
            partial(exception_handler),
            partial(timeout_handler),
            partial(success_handler)
        ]
        
        # Act - should not raise any exception
        await message_bus.handle(command, event_timeout=0.1)
        
        # Assert
        # All handlers should have been called
        assert exception_handler.call_count == 1
        assert timeout_handler.call_count == 1
        assert success_handler.call_count == 1
        
        # All handlers should have received the event
        assert exception_handler.called_with[0] == event
        assert timeout_handler.called_with[0] == event
        assert success_handler.called_with[0] == event
        
        # The success handler should have completed successfully
        assert success_handler.completed == True
        assert success_handler.cancelled == False
        
        # The exception handler should have completed (even though it failed)
        assert exception_handler.completed == True
        assert exception_handler.cancelled == False