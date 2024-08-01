from aio_pika import Channel, Exchange, Queue
from attrs import asdict, define
from src.rabbitmq.aio_pika_classes import AIOPikaData
from src.rabbitmq.aio_pika_manager import AIOPikaManager


@define
class AIOPikaResources:
    exchange: Exchange
    queue: Queue
    dl_exchange: Exchange
    dl_queue: Queue


async def setup_rabbitmq_resources(
    channel: Channel, rmq_manager: AIOPikaManager, data: AIOPikaData
) -> AIOPikaResources:
    exchange = await rmq_manager.declare_exchange(**asdict(data.exchange))
    queue = await rmq_manager.declare_queue(**asdict(data.queue))
    await rmq_manager.bind_queue(queue=queue, **asdict(data.queue_bind))
    dl_exchange = await rmq_manager.declare_exchange(**asdict(data.dl_exchange))
    dl_queue = await rmq_manager.declare_queue(**asdict(data.dl_queue))
    await rmq_manager.bind_queue(queue=dl_queue, **asdict(data.dl_queue_bind))
    return AIOPikaResources(
        exchange=exchange, queue=queue, dl_exchange=dl_exchange, dl_queue=dl_queue
    )
