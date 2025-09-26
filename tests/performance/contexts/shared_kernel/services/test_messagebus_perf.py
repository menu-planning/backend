"""Performance tests for MessageBus service throughput.

Tests the central message dispatching service performance under various
load conditions to ensure it meets throughput and latency requirements.
"""

from __future__ import annotations

import asyncio
import time
from functools import partial
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import anyio
import pytest
from src.contexts.seedwork.domain.commands.command import Command
from src.contexts.seedwork.domain.event import Event
from src.contexts.seedwork.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus

pytestmark = pytest.mark.anyio


class AsyncBenchmarkTimer:
    """Context manager for measuring async operation performance with warmup and sampling."""

    def __init__(self, max_ms: float, samples: int = 30, warmup: int = 5):
        """Initialize benchmark timer.

        Args:
            max_ms: Maximum allowed milliseconds for P95 threshold.
            samples: Number of samples to collect for measurement.
            warmup: Number of warmup iterations before measurement.
        """
        self.max_ms = max_ms
        self.samples = samples
        self.warmup = warmup
        self.times: list[float] = []

    def __enter__(self):
        """Enter context and start timing."""
        self.times = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and validate performance threshold."""
        if exc_type is not None:
            return False

        if len(self.times) < self.samples:
            pytest.fail(f"Expected {self.samples} samples, got {len(self.times)}")

        # Calculate P95
        sorted_times = sorted(self.times)
        p95_index = int(0.95 * len(sorted_times))
        p95_time = sorted_times[p95_index]

        if p95_time > self.max_ms:
            pytest.fail(
                f"P95 time {p95_time:.2f}ms exceeds threshold {self.max_ms}ms. "
                f"Times: {sorted_times[:5]}...{sorted_times[-5:]}"
            )

    async def measure(self, operation):
        """Measure a single operation and record its execution time."""
        start_time = time.perf_counter()
        if callable(operation):
            result = operation()
            if asyncio.iscoroutine(result):
                await result
        else:
            await operation()
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000
        self.times.append(duration_ms)


class SampleCommand(Command):
    """Sample command for message bus performance testing."""

    def __init__(self, data: str = "test"):
        self.data = data


class SampleEvent(Event):
    """Sample event for message bus performance testing."""

    def __init__(self, data: str = "test"):
        self.data = data


class FakeUnitOfWork(UnitOfWork):
    """Fake UnitOfWork for performance testing message bus behavior."""

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
    """Fake handler for performance testing message processing."""

    def __init__(self, delay: float = 0.0):
        self.delay = delay
        self.called_with: list[Any] = []
        self.call_count = 0
        self.completed = False

    async def __call__(self, message: Command | Event):
        """Execute the handler with optional delay."""
        self.called_with.append(message)
        self.call_count += 1

        if self.delay > 0:
            await anyio.sleep(self.delay)

        self.completed = True


@pytest.fixture
def async_benchmark_timer():
    """Provide async benchmark timer for performance measurements."""
    return AsyncBenchmarkTimer


@pytest.fixture
def fake_uow():
    """Provide a fake UnitOfWork for performance testing."""
    return FakeUnitOfWork()


@pytest.fixture
def fake_command_handler():
    """Provide a fast fake command handler."""
    return FakeHandler(delay=0.001)  # 1ms delay to simulate work


@pytest.fixture
def fake_event_handlers():
    """Provide fast fake event handlers."""
    return [FakeHandler(delay=0.001), FakeHandler(delay=0.001)]


@pytest.fixture
def message_bus(fake_uow, fake_command_handler, fake_event_handlers):
    """Provide a MessageBus instance with fake dependencies."""
    command_handlers: dict[type[Command], partial] = {
        SampleCommand: partial(fake_command_handler)
    }
    event_handlers: dict[type[Event], list[partial]] = {
        SampleEvent: [partial(handler) for handler in fake_event_handlers]
    }

    return MessageBus(
        uow=fake_uow, command_handlers=command_handlers, event_handlers=event_handlers
    )


@pytest.fixture
def seed_data():
    """Provide seed data for performance testing."""
    return {
        "commands": [SampleCommand(f"cmd_{i}") for i in range(100)],
        "events": [SampleEvent(f"event_{i}") for i in range(100)],
    }


@pytest.mark.slow
@pytest.mark.anyio
async def test_messagebus_throughput(async_benchmark_timer, message_bus, seed_data):
    """Test that message bus meets message processing throughput requirements.

    SLO: P95 < 50ms for single command processing with events.
    Throughput: > 100 commands/second under normal load.
    """
    # Warm up caches and connection pools
    for _ in range(5):
        command = SampleCommand("warmup")
        message_bus.uow.add_event(SampleEvent("warmup_event"))
        await message_bus.handle(command)

    with async_benchmark_timer(max_ms=50.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            # Create a command that generates an event
            command = SampleCommand("perf_test")
            event = SampleEvent("perf_event")

            # Store the original handler before replacing
            original_handler = message_bus.command_handlers[SampleCommand]
            original_handler_func = original_handler.func

            # Add event to be collected after command processing
            def command_handler_with_event(cmd, evt=event):
                message_bus.uow.add_event(evt)
                # Use the original handler function directly
                return original_handler_func(cmd)

            # Replace the command handler temporarily
            message_bus.command_handlers[SampleCommand] = partial(
                command_handler_with_event
            )

            try:
                await timer.measure(lambda cmd=command: message_bus.handle(cmd))
            finally:
                # Restore original handler
                message_bus.command_handlers[SampleCommand] = original_handler


@pytest.mark.slow
@pytest.mark.anyio
async def test_messagebus_bulk_throughput(
    async_benchmark_timer, message_bus, seed_data
):
    """Test message bus bulk processing throughput.

    SLO: P95 < 200ms for processing 10 commands with events.
    Throughput: > 50 command batches/second.
    """
    # Warm up
    for _ in range(3):
        for command in seed_data["commands"][:5]:
            message_bus.uow.add_event(SampleEvent("warmup"))
            await message_bus.handle(command)

    with async_benchmark_timer(max_ms=200.0, samples=20, warmup=3) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: _bulk_command_processing(
                    message_bus, seed_data["commands"][:10]
                )
            )


async def _bulk_command_processing(
    message_bus: MessageBus, commands: list[SampleCommand]
):
    """Process multiple commands in sequence for bulk throughput testing."""
    for command in commands:
        # Store the original handler before replacing
        original_handler = message_bus.command_handlers[SampleCommand]
        original_handler_func = original_handler.func

        # Add event to be collected after command processing
        event = SampleEvent(f"bulk_event_{command.data}")

        def command_handler_with_event(cmd, evt=event):
            message_bus.uow_factory.add_event(evt)
            # Use the original handler function directly
            return original_handler_func(cmd)

        # Replace the command handler temporarily
        message_bus.command_handlers[SampleCommand] = partial(
            command_handler_with_event
        )

        try:
            await message_bus.handle(command)
        finally:
            # Restore original handler
            message_bus.command_handlers[SampleCommand] = original_handler


@pytest.mark.slow
@pytest.mark.anyio
async def test_messagebus_concurrent_throughput(
    async_benchmark_timer, message_bus, seed_data
):
    """Test message bus concurrent processing throughput.

    SLO: P95 < 100ms for processing 5 concurrent commands.
    Throughput: > 50 concurrent command groups/second.
    """
    # Warm up
    for _ in range(3):
        tasks = []
        for command in seed_data["commands"][:3]:
            message_bus.uow.add_event(SampleEvent("warmup"))
            tasks.append(message_bus.handle(command))
        await asyncio.gather(*tasks)

    with async_benchmark_timer(max_ms=100.0, samples=15, warmup=3) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: _concurrent_command_processing(
                    message_bus, seed_data["commands"][:5]
                )
            )


async def _concurrent_command_processing(
    message_bus: MessageBus, commands: list[SampleCommand]
):
    """Process multiple commands concurrently for concurrent throughput testing."""

    async def process_command(command: SampleCommand):
        # Store the original handler before replacing
        original_handler = message_bus.command_handlers[SampleCommand]
        original_handler_func = original_handler.func

        # Add event to be collected after command processing
        event = SampleEvent(f"concurrent_event_{command.data}")

        def command_handler_with_event(cmd, evt=event):
            message_bus.uow_factory.add_event(evt)
            # Use the original handler function directly
            return original_handler_func(cmd)

        # Replace the command handler temporarily
        message_bus.command_handlers[SampleCommand] = partial(
            command_handler_with_event
        )

        try:
            await message_bus.handle(command)
        finally:
            # Restore original handler
            message_bus.command_handlers[SampleCommand] = original_handler

    # Process all commands concurrently
    tasks = [process_command(command) for command in commands]
    await asyncio.gather(*tasks)


@pytest.mark.slow
@pytest.mark.anyio
async def test_messagebus_event_processing_throughput(
    async_benchmark_timer, message_bus, seed_data
):
    """Test message bus event processing throughput.

    SLO: P95 < 30ms for processing single event with multiple handlers.
    Throughput: > 200 event processing operations/second.
    """
    # Warm up event processing
    for _ in range(5):
        command = SampleCommand("warmup")
        message_bus.uow.add_event(SampleEvent("warmup_event"))
        await message_bus.handle(command)

    with async_benchmark_timer(max_ms=30.0, samples=40, warmup=5) as timer:
        for _ in range(timer.samples):
            # Create a command that generates an event
            command = SampleCommand("event_perf_test")
            event = SampleEvent("event_perf_event")

            # Store the original handler before replacing
            original_handler = message_bus.command_handlers[SampleCommand]
            original_handler_func = original_handler.func

            # Add event to be collected after command processing
            def command_handler_with_event(cmd, evt=event):
                message_bus.uow.add_event(evt)
                # Use the original handler function directly
                return original_handler_func(cmd)

            # Replace the command handler temporarily
            message_bus.command_handlers[SampleCommand] = partial(
                command_handler_with_event
            )

            try:
                await timer.measure(lambda cmd=command: message_bus.handle(cmd))
            finally:
                # Restore original handler
                message_bus.command_handlers[SampleCommand] = original_handler
