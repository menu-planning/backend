from typing import Tuple

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
    channel: Channel,
    rmq_manager: AIOPikaManager,
    data: AIOPikaData,
    setup_dl: bool = True,
) -> Tuple[AIOPikaResources, ...]:
    await rmq_manager.declare_exchange(**asdict(data.exchange))
    queue = await rmq_manager.declare_queue(**asdict(data.queue))
    await rmq_manager.bind_queue(queue=queue, **asdict(data.queue_bind))
    if setup_dl:
        dl_rmq_manager = AIOPikaManager()
        await dl_rmq_manager.connect()
        await dl_rmq_manager.declare_exchange(**asdict(data.dl_exchange))
        dl_queue = await dl_rmq_manager.declare_queue(**asdict(data.dl_queue))
        await dl_rmq_manager.bind_queue(queue=dl_queue, **asdict(data.dl_queue_bind))
        return rmq_manager, dl_rmq_manager
    # return AIOPikaResources(
    #     exchange=exchange, queue=queue, dl_exchange=dl_exchange, dl_queue=dl_queue
    # )
