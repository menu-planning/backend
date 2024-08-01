import signal

from aio_pika import RobustChannel, RobustExchange, RobustQueue
from aio_pika.abc import AbstractMessage, TimeoutType
from anyio import CancelScope, open_signal_receiver
from attrs import asdict
from src.logger import logger
from src.rabbitmq.aio_pika_classes import AIOPikaData
from src.rabbitmq.connection import RobustConnectionMaker, aio_pika_connection


class AIOPikaManager:
    def __init__(self, connection_maker: RobustConnectionMaker = aio_pika_connection):
        self.connection_maker = connection_maker
        self.channels: dict[str, RobustChannel] = {}

    async def close_connection(self, signal: signal.Signals = None):
        if self.connection_maker._connection:
            await self.connection_maker.close_connection()

    async def signal_handler(self, scope: CancelScope):
        with open_signal_receiver(signal.SIGINT, signal.SIGTERM) as signals:
            async for signum in signals:
                logger.info(f"Received exit signal number {signum}...")
                if signum == signal.SIGINT:
                    logger.info(
                        f"Ctrl+C pressed! Received exit signal number {signum}..."
                    )
                else:
                    logger.info(f"Terminated! Received exit signal number {signum}...")
                await self.close_connection()
                scope.cancel()
                return

    async def publish_from_AIOPikaData(
        self,
        message: AbstractMessage,
        routing_key: str,
        *,
        aio_pika_data: RobustExchange,
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
    ):
        exchange = await self.get_exchange_from_AIOPikaData(aio_pika_data)
        await exchange.publish(
            message,
            routing_key,
            mandatory=mandatory,
            immediate=immediate,
            timeout=timeout,
        )

    async def consume(self, queue: RobustQueue, callback, **kwargs) -> None:
        await queue.consume(callback, **kwargs)

    async def _get_channel_from_AIOPikaData(
        self, aio_pika_data: AIOPikaData, get_dl: bool = False
    ) -> RobustChannel:
        queue_name = aio_pika_data.dl_queue.name if get_dl else aio_pika_data.queue.name
        set_qos = None if get_dl else aio_pika_data.set_qos
        if queue_name not in self.channels:
            connection = await self.connection_maker.get_connection()
            channel = await connection.channel()
            if set_qos:
                await channel.set_qos(**asdict(set_qos, recurse=False))
            self.channels[queue_name] = channel
        else:
            channel = self.channels[queue_name]
        return channel

    async def get_channel_from_AIOPikaData(
        self, aio_pika_data: AIOPikaData
    ) -> RobustChannel:
        return await self._get_channel_from_AIOPikaData(aio_pika_data)

    async def get_dl_channel_from_AIOPikaData(
        self, aio_pika_data: AIOPikaData
    ) -> RobustChannel:
        return await self._get_channel_from_AIOPikaData(aio_pika_data, get_dl=True)

    async def _get_exchange_from_AIOPikaData(
        self, aio_pika_data: AIOPikaData, get_dl: bool = False
    ) -> RobustExchange:
        exchange_data = aio_pika_data.dl_exchange if get_dl else aio_pika_data.exchange
        if get_dl:
            channel = await self.get_dl_channel_from_AIOPikaData(aio_pika_data)
        else:
            channel = await self.get_channel_from_AIOPikaData(aio_pika_data)
        return await channel.declare_exchange(**asdict(exchange_data, recurse=False))

    async def get_exchange_from_AIOPikaData(
        self, aio_pika_data: AIOPikaData
    ) -> RobustExchange:
        return await self._get_exchange_from_AIOPikaData(aio_pika_data)

    async def get_dl_exchange_from_AIOPikaData(
        self, aio_pika_data: AIOPikaData
    ) -> RobustExchange:
        return await self._get_exchange_from_AIOPikaData(aio_pika_data, get_dl=True)

    async def _get_queue_from_AIOPikaData(
        self, aio_pika_data: AIOPikaData, get_dl: bool = False
    ) -> RobustQueue | None:
        if get_dl:
            channel = await self.get_dl_channel_from_AIOPikaData(aio_pika_data)
            queue_data = aio_pika_data.dl_queue
        else:
            channel = await self.get_channel_from_AIOPikaData(aio_pika_data)
            queue_data = aio_pika_data.queue
        return await channel.declare_queue(**asdict(queue_data, recurse=False))

    async def get_queue_from_AIOPikaData(
        self, aio_pika_data: AIOPikaData
    ) -> RobustQueue | None:
        return await self._get_queue_from_AIOPikaData(aio_pika_data)

    async def get_dl_queue_from_AIOPikaData(
        self, aio_pika_data: AIOPikaData
    ) -> RobustQueue | None:
        return await self._get_queue_from_AIOPikaData(aio_pika_data, get_dl=True)

    async def _bind_queue_from_AIOPikaData(
        self, aio_pika_data: AIOPikaData, get_dl: bool = False
    ) -> None:
        if get_dl:
            queue = await self.get_dl_queue_from_AIOPikaData(aio_pika_data)
            exchange = await self.get_dl_exchange_from_AIOPikaData(aio_pika_data)
            rounting_key = aio_pika_data.dl_queue_bind.routing_key
        else:
            queue = await self.get_queue_from_AIOPikaData(aio_pika_data)
            exchange = await self.get_exchange_from_AIOPikaData(aio_pika_data)
            rounting_key = aio_pika_data.queue_bind.routing_key
        if queue:
            await queue.bind(exchange, rounting_key)

    async def bind_queue_from_AIOPikaData(self, aio_pika_data: AIOPikaData) -> None:
        await self._bind_queue_from_AIOPikaData(aio_pika_data)

    async def bind_dl_queue_from_AIOPikaData(self, aio_pika_data: AIOPikaData) -> None:
        await self._bind_queue_from_AIOPikaData(aio_pika_data, get_dl=True)

    async def declare_resources_from_AIOPikaData(
        self,
        aio_pika_data: AIOPikaData,
        setup_dl: bool = True,
    ) -> None:
        await self.bind_queue_from_AIOPikaData(aio_pika_data)
        if setup_dl:
            await self.declare_dl_resources_from_AIOPikaData(aio_pika_data)

    async def declare_dl_resources_from_AIOPikaData(
        self,
        aio_pika_data: AIOPikaData,
    ) -> None:
        await self.bind_dl_queue_from_AIOPikaData(aio_pika_data)
