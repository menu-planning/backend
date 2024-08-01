import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import anyio
import pytest
from aio_pika import Channel, ExchangeType, Message
from aio_pika.abc import AbstractIncomingMessage
from aio_pika.exceptions import ChannelClosed
from attrs import define, field

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


@define
class AIOPikaData:
    queue_name: str = field(factory=lambda: uuid.uuid4().hex)
    exchange_name: str = field(init=False)
    routing_key: str = field(init=False)
    dlx_routing_key: str = field(init=False)
    dlx_queue_name: str = field(init=False)
    dlx_exchange_name: str = field(init=False)

    def __attrs_post_init__(self):
        self.exchange_name = self.queue_name
        self.routing_key = f"{self.queue_name}_routing_key"
        self.dlx_routing_key = f"{self.queue_name}_dlx_routing_key"
        self.dlx_queue_name = f"{self.queue_name}_dlx"
        self.dlx_exchange_name = "dlx"


async def setup_queues(channel: Channel, queue_name: str = "", ttl: int = 10000):
    data = AIOPikaData(queue_name)
    try:
        await channel.queue_delete(data.queue_name)
        await channel.queue_delete(data.dlx_queue_name)
    except ChannelClosed:
        pass
    finally:
        exchange = await channel.declare_exchange(
            data.exchange_name,
            ExchangeType.DIRECT,
        )
        dlx_exchange = await channel.declare_exchange(
            data.dlx_exchange_name,
            ExchangeType.DIRECT,
        )
        queue = await channel.declare_queue(
            data.queue_name,
            arguments={
                "x-message-ttl": ttl,
                "x-dead-letter-exchange": data.dlx_exchange_name,
                "x-dead-letter-routing-key": data.dlx_routing_key,
            },
        )
        dlx_queue = await channel.declare_queue(
            data.dlx_queue_name,
            auto_delete=True,
        )
        await dlx_queue.bind(dlx_exchange, data.dlx_routing_key)
        await queue.bind(exchange, data.routing_key)
    return data


async def cleanup_queues(channel: Channel, data: AIOPikaData):
    try:
        exchange = await channel.get_exchange(data.queue_name)
        queue = await channel.get_queue(data.queue_name)
        await queue.unbind(exchange, data.routing_key)
        await channel.queue_delete(data.queue_name)
        await channel.exchange_delete(data.exchange_name)
        dlx_exchange = await channel.get_exchange(data.dlx_exchange_name)
        dlx_queue = await channel.get_queue(data.dlx_queue_name)
        await dlx_queue.unbind(dlx_exchange, data.dlx_routing_key)
        await channel.queue_delete(data.dlx_queue_name)
        await channel.exchange_delete(data.dlx_exchange_name)
    except ChannelClosed:
        pass


async def publish_messages(
    channel: Channel,
    data: AIOPikaData,
    number_of_messages: int = 1,
    attempts: int = 0,
    ttl: int = 600,
):
    exchange = await channel.get_exchange(data.exchange_name)
    queue = await channel.get_queue(data.queue_name)

    if attempts == 0:
        assert queue.declaration_result.message_count == 0

    emails = []
    for _ in range(number_of_messages):
        email = f"{uuid.uuid4().hex[:6]}@example.com"
        body = json.dumps({"email": email, "timestamp": datetime.now().isoformat()})
        emails.append(email)
        await exchange.publish(
            Message(
                body=json.dumps(
                    {"email": email, "timestamp": datetime.now().isoformat()}
                ).encode(),
                content_type="application/json",
                headers={
                    "x-message-ttl": ttl,
                    "x-dead-letter-exchange": "dlx",
                    "attempts": attempts,
                },
            ),
            routing_key=data.routing_key,
        )
    if attempts == 0:
        queue = await channel.get_queue(data.queue_name)
        assert queue.declaration_result.message_count == number_of_messages


async def test_that_consume_on_valid_message_are_consumed_from_the_queue(
    channel: Channel,
):
    number_of_messages = 1000
    timeout = 5
    queue_name = "test_valid_message"

    data = await setup_queues(channel, queue_name)
    await publish_messages(channel, data, number_of_messages)

    mock = AsyncMock()

    async def message_callback(message: AbstractIncomingMessage) -> str:
        await message.ack()
        await mock()
        return message.body.decode()

    queue = await channel.get_queue(data.queue_name)
    await queue.consume(message_callback)

    with anyio.move_on_after(timeout):
        while True:
            await anyio.sleep(0)
            if mock.await_count == number_of_messages:
                break
    assert mock.await_count == number_of_messages

    queue = await channel.get_queue(data.queue_name)
    with anyio.move_on_after(timeout):
        while True:
            await anyio.sleep(0)
            if queue.declaration_result.message_count == 0:
                break
    assert queue.declaration_result.message_count == 0
    await cleanup_queues(channel, data)


async def test_that_consume_on_invalid_message_does_moves_message_to_dead_letter_queue(
    channel: Channel,
):
    number_of_messages = 1000
    timeout = 5
    queue_name = "test_invalid_message"

    data = await setup_queues(channel, queue_name)
    await publish_messages(channel, data, number_of_messages)

    mock = AsyncMock()

    async def message_callback(message: AbstractIncomingMessage) -> str:
        await message.reject()
        await mock()

    queue = await channel.get_queue(data.queue_name)
    await queue.consume(message_callback)

    with anyio.move_on_after(timeout):
        while True:
            await anyio.sleep(0)
            if mock.await_count == number_of_messages:
                break

    assert mock.await_count == number_of_messages

    queue = await channel.get_queue(data.queue_name)
    assert queue.declaration_result.message_count == 0

    dlx_queue = await channel.get_queue(data.dlx_queue_name)
    assert dlx_queue.declaration_result.message_count == number_of_messages

    await cleanup_queues(channel, data)


async def test_that_consume_on_failure_message_does_reschedule_the_message(
    channel: Channel,
):
    number_of_messages = 1000
    timeout = 10
    queue_name = "test_failure_message"

    data = await setup_queues(channel, queue_name)
    await publish_messages(channel, data, number_of_messages)

    mock = AsyncMock()

    async def message_callback(message: AbstractIncomingMessage) -> str:
        await mock()
        if message.redelivered:
            await message.ack()
        else:
            await message.reject(requeue=True)

    queue = await channel.get_queue(data.queue_name)
    await queue.consume(message_callback)

    with anyio.move_on_after(timeout):
        while True:
            await anyio.sleep(0)
            if mock.await_count == number_of_messages * 2:
                break

    assert mock.await_count == number_of_messages * 2

    queue = await channel.get_queue(data.queue_name)
    assert queue.declaration_result.message_count == 0

    dlx_queue = await channel.get_queue(data.dlx_queue_name)
    assert dlx_queue.declaration_result.message_count == 0
    await cleanup_queues(channel, data)


async def test_that_consume_on_failure_message_does_limit_retry(
    channel: Channel,
):
    number_of_messages = 5
    timeout = 5
    retry_attempts = 2
    queue_name = "test_retry_message"

    data = await setup_queues(channel, queue_name)
    await publish_messages(channel, data, number_of_messages)

    mock = AsyncMock()

    async def message_callback(message: AbstractIncomingMessage) -> str:
        await mock()
        attempt = message.headers["attempts"]
        if message.headers["attempts"] == retry_attempts:
            await message.reject()
        else:
            attempt += 1
            await message.ack()
            await publish_messages(channel, data, attempts=attempt)

    queue = await channel.get_queue(data.queue_name)
    await queue.consume(message_callback)

    with anyio.move_on_after(timeout):
        while True:
            await anyio.sleep(0)
            if mock.await_count == (number_of_messages * (retry_attempts + 1)):
                break

    assert mock.await_count == (number_of_messages * (retry_attempts + 1))

    queue = await channel.get_queue(data.queue_name)
    assert queue.declaration_result.message_count == 0

    await anyio.sleep(1)
    dlx_queue = await channel.get_queue(data.dlx_queue_name)
    assert dlx_queue.declaration_result.message_count == number_of_messages
    await cleanup_queues(channel, data)
