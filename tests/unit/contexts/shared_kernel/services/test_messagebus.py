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


class FakeHandler:
    """Fake handler for testing message processing."""
    
    def __init__(self, should_raise: Exception | None = None, delay: float = 0.0):
        self.should_raise = should_raise
        self.delay = delay
        self.called_with: list[Any] = []
        self.call_count = 0
    
    async def __call__(self, message: Command | Event):
        """Execute the handler with optional delay and exception."""
        self.called_with.append(message)
        self.call_count += 1
        
        if self.delay > 0:
            await anyio.sleep(self.delay)
        
        if self.should_raise:
            raise self.should_raise


@pytest.fixture
def fake_uow():
    """Provide a fake UnitOfWork for testing."""
    return FakeUnitOfWork()


@pytest.fixture
def fake_command_handler():
    """Provide a fake command handler."""
    return FakeHandler()


@pytest.fixture
def fake_event_handlers():
    """Provide fake event handlers."""
    return [FakeHandler(), FakeHandler()]


@pytest.fixture
def message_bus(fake_uow, fake_command_handler, fake_event_handlers):
    """Provide a MessageBus instance with fake dependencies."""
    command_handlers: dict[type[Command], partial] = {SampleCommand: partial(fake_command_handler)}
    event_handlers: dict[type[Event], list[partial]] = {SampleEvent: [partial(handler) for handler in fake_event_handlers]}
    
    return MessageBus(
        uow=fake_uow,
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
        assert fake_command_handler.called_with[0] == command
    
    async def test_handles_event_successfully(self, message_bus, fake_event_handlers):
        """Test that events are processed successfully by all handlers."""
        # Arrange
        event = SampleEvent("test_data")
        
        # Act
        await message_bus.handle(event)
        
        # Assert
        for handler in fake_event_handlers:
            assert handler.call_count == 1
            assert handler.called_with[0] == event
    
    async def test_processes_new_events_from_command(self, message_bus, fake_command_handler, fake_event_handlers):
        """Test that new events emitted during command processing are handled."""
        # Arrange
        command = SampleCommand("test_data")
        new_event = SampleEvent("new_event_data")
        
        # Add event to be collected after command processing
        def command_handler_with_event(cmd):
            message_bus.uow.add_event(new_event)
            return fake_command_handler(cmd)
        
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
        await message_bus.handle(command, timeout=custom_timeout)
        
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
        failing_handler = FakeHandler(should_raise=expected_error)
        message_bus.command_handlers[SampleCommand] = partial(failing_handler)
        
        # Act & Assert
        # AnyIO task groups wrap exceptions in ExceptionGroup
        with pytest.raises(ExceptionGroup) as exc_info:
            await message_bus.handle(command)
        
        # Verify the original exception is in the exception group
        assert len(exc_info.value.exceptions) == 1
        assert isinstance(exc_info.value.exceptions[0], ValueError)
        assert str(exc_info.value.exceptions[0]) == "Command failed"
    
    async def test_handles_event_handler_errors_without_propagation(self, message_bus, fake_event_handlers):
        """Test that event handler errors don't stop other handlers."""
        # Arrange
        event = SampleEvent("test_data")
        expected_error = RuntimeError("Event handler failed")
        
        # Make one handler fail
        fake_event_handlers[0].should_raise = expected_error
        
        # Act
        await message_bus.handle(event)
        
        # Assert
        # First handler should have been called (and failed)
        assert fake_event_handlers[0].call_count == 1
        # Second handler should still have been called
        assert fake_event_handlers[1].call_count == 1
    
    async def test_multiple_event_handlers_with_mixed_success_failure(self, message_bus):
        """Test that multiple event handlers work independently - some succeed, some fail."""
        # Arrange
        event = SampleEvent("test_data")
        
        # Create three handlers: one succeeds, one fails, one succeeds
        success_handler1 = FakeHandler()
        failing_handler = FakeHandler(should_raise=ValueError("Handler failed"))
        success_handler2 = FakeHandler()
        
        message_bus.event_handlers[SampleEvent] = [
            partial(success_handler1),
            partial(failing_handler),
            partial(success_handler2)
        ]
        
        # Act - should not raise an exception despite one handler failing
        await message_bus.handle(event)
        
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
        invalid_message = "not a command or event"
        
        # Act & Assert
        with pytest.raises(TypeError, match="not a Command or Event"):
            await message_bus.handle(invalid_message)
    
    async def test_raises_timeout_error_for_command_timeout(self, message_bus):
        """Test that command timeouts raise TimeoutError."""
        # Arrange
        command = SampleCommand("test_data")
        timeout = 0.1  # Very short timeout
        
        # Create a slow command handler
        slow_handler = FakeHandler(delay=0.2)  # Longer than timeout
        message_bus.command_handlers[SampleCommand] = partial(slow_handler)
        
        # Act & Assert
        with pytest.raises(TimeoutError, match="Timeout handling command"):
            await message_bus.handle(command, timeout=timeout)
    
    async def test_event_timeout_does_not_raise_error(self, message_bus, fake_event_handlers):
        """Test that event timeouts don't raise errors but handlers may be cancelled."""
        # Arrange
        event = SampleEvent("test_data")
        timeout = 0.1  # Very short timeout
        
        # Create slow event handlers
        slow_handler1 = FakeHandler(delay=0.2)  # Longer than timeout
        slow_handler2 = FakeHandler(delay=0.05)  # Shorter than timeout
        
        message_bus.event_handlers[SampleEvent] = [
            partial(slow_handler1),
            partial(slow_handler2)
        ]
        
        # Act - should not raise an exception
        await message_bus.handle(event, timeout=timeout)
        
        # Assert
        # The fast handler should have completed
        assert slow_handler2.call_count == 1
        # The slow handler may or may not have completed depending on timing
        # but the important thing is that no exception was raised
    
    async def test_events_fail_silently(self, message_bus):
        """Test that events fail silently - no exceptions are raised even when all handlers fail."""
        # Arrange
        event = SampleEvent("test_data")
        
        # Create handlers that all fail
        failing_handler1 = FakeHandler(should_raise=RuntimeError("Handler 1 failed"))
        failing_handler2 = FakeHandler(should_raise=ValueError("Handler 2 failed"))
        
        message_bus.event_handlers[SampleEvent] = [
            partial(failing_handler1),
            partial(failing_handler2)
        ]
        
        # Act - should not raise any exception despite all handlers failing
        await message_bus.handle(event)
        
        # Assert
        # Both handlers should have been called
        assert failing_handler1.call_count == 1
        assert failing_handler2.call_count == 1
        
        # Both handlers should have received the event
        assert failing_handler1.called_with[0] == event
        assert failing_handler2.called_with[0] == event


class TestMessageBusHandleAsyncBehavior:
    """Test async behavior and concurrency scenarios."""
    
    async def test_handles_concurrent_event_handlers(self, message_bus, fake_event_handlers):
        """Test that multiple event handlers run concurrently."""
        # Arrange
        event = SampleEvent("test_data")
        
        # Make handlers take some time to complete
        fake_event_handlers[0].delay = 0.1
        fake_event_handlers[1].delay = 0.1
        
        # Act
        import time
        start_time = time.time()
        await message_bus.handle(event)
        end_time = time.time()
        
        # Assert
        # Both handlers should have been called
        for handler in fake_event_handlers:
            assert handler.call_count == 1
        
        # Should complete in roughly 0.1s (concurrent) not 0.2s (sequential)
        assert end_time - start_time < 0.15
    
    async def test_handles_concurrent_new_events(self, message_bus, fake_command_handler, fake_event_handlers):
        """Test that multiple new events from command processing are handled concurrently."""
        # Arrange
        command = SampleCommand("test_data")
        event1 = SampleEvent("event1")
        event2 = SampleEvent("event2")
        
        def command_handler_with_events(cmd):
            message_bus.uow.add_event(event1)
            message_bus.uow.add_event(event2)
            return fake_command_handler(cmd)
        
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
        assert end_time - start_time < 0.25
    
    async def test_handles_mixed_command_and_event_processing(self, message_bus, fake_command_handler, fake_event_handlers):
        """Test processing both commands and events in sequence."""
        # Arrange
        command = SampleCommand("command_data")
        event = SampleEvent("event_data")
        
        # Act
        await message_bus.handle(command)
        await message_bus.handle(event)
        
        # Assert
        assert fake_command_handler.call_count == 1
        assert fake_command_handler.called_with[0] == command
        
        for handler in fake_event_handlers:
            assert handler.call_count == 1
            assert handler.called_with[0] == event
    
    async def test_handles_event_processing_with_uow_events(self, message_bus, fake_command_handler, fake_event_handlers):
        """Test that events added to UoW during event processing are not automatically processed."""
        # Arrange
        initial_event = SampleEvent("initial")
        nested_event = SampleEvent("nested")
        
        def event_handler_with_uow_event(evt):
            if evt.data == "initial":
                # Add event to UoW, but it won't be processed since events fail silently
                message_bus.uow.add_event(nested_event)
            return fake_event_handlers[0](evt)
        
        # Replace first event handler
        message_bus.event_handlers[SampleEvent] = [
            partial(event_handler_with_uow_event),
            partial(fake_event_handlers[1])
        ]
        
        # Act
        await message_bus.handle(initial_event)
        
        # Assert
        # Only the initial event should have been processed by both handlers
        # The nested event added to UoW is not processed since events fail silently
        assert fake_event_handlers[0].call_count == 1  # only initial
        assert fake_event_handlers[1].call_count == 1  # only initial
        
        # Verify only the initial event was processed
        assert fake_event_handlers[0].called_with[0] == initial_event
        assert fake_event_handlers[1].called_with[0] == initial_event
        
        # Verify the nested event was added to UoW but not processed
        assert len(message_bus.uow._events) == 1
        assert message_bus.uow._events[0] == nested_event