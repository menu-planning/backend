import aio_pika
import pytest

from src.rabbitmq.connection import aio_pika_connection


@pytest.fixture
async def connection() -> aio_pika.Connection:
    conn = await aio_pika_connection.get_connection()
    async with conn:
        yield conn


@pytest.fixture
async def channel(
    connection: aio_pika.Connection,
) -> aio_pika.Channel:
    async with connection.channel() as ch:
        yield ch
