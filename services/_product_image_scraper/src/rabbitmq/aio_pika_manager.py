from aio_pika import (
    Channel,
    Connection,
    ExchangeType,
    RobustChannel,
    RobustConnection,
    RobustExchange,
    RobustQueue,
)
from aio_pika.abc import AbstractMessage, TimeoutType
from src.rabbitmq.connection import RobustConnectionMaker, aio_pika_connection


class AIOPikaManager:
    def __init__(
        self,
        # data: AIOPikaData,
        # rabbitmq_url: str = rabbitmq_settings.rabbitmq_url,
        connection_maker: RobustConnectionMaker = aio_pika_connection,
    ):
        # self.rabbitmq_url = rabbitmq_url
        # self.data = data
        self.connection_maker = connection_maker
        self.connection: RobustConnection | None = None
        self.channel: RobustChannel | None = None
        self.queue: RobustQueue | None = None
        self.exchange: RobustExchange | None = None

    async def publish(
        self,
        message: AbstractMessage,
        routing_key: str,
        *,
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
    ):
        assert self.queue is not None, "Queue is not declared"
        assert self.channel is not None, "Channel is not opened"
        assert self.connection is not None, "Connection is not opened"
        if self.exchange:
            await self.exchange.publish(
                message,
                routing_key,
                mandatory=mandatory,
                immediate=immediate,
                timeout=timeout,
            )
        else:
            await self.channel.default_exchange.publish(
                message,
                routing_key,
                mandatory=mandatory,
                immediate=immediate,
                timeout=timeout,
            )

    async def connect(self) -> RobustConnection:
        self.connection = await self.connection_maker.get_connection()
        return self.connection

    async def close_channel(self) -> None:
        if self.channel:
            await self.channel.close()

    async def close(self) -> None:
        await self.close_channel()
        if self.connection:
            await self.connection.close()

    # async def open_channel(
    #     self, connection: Connection, *args, **kwargs
    # ) -> RobustChannel:
    #     # connection = await self.connect()
    #     # if self.channel and self.channel.is_initialized and not self.channel.is_closed:
    #     #     return self.channel
    #     self. connection.channel(*args, **kwargs)
    #     return self.channel

    async def declare_queue(
        self, *, channel: Channel, name: str | None = None, **kwargs
    ) -> RobustQueue:
        # assert self.channel is not None, "Channel is not opened"
        self.queue = await channel.declare_queue(name, **kwargs)
        return self.queue

    async def declare_exchange(
        self,
        *,
        channel: Channel,
        name: str | None = None,
        type: ExchangeType | str = ExchangeType.DIRECT,
        **kwargs,
    ) -> RobustExchange:
        if name is None:
            self.exchange = channel.default_exchange
        else:
            self.exchange = await channel.declare_exchange(name, type, **kwargs)
        return self.exchange

    async def bind_queue(
        sefl, queue: RobustQueue, exchange: RobustExchange | str, routing_key: str
    ) -> None:
        await queue.bind(exchange, routing_key)

    async def consume(self, queue: RobustQueue, callback, **kwargs) -> None:
        await queue.consume(callback, **kwargs)
