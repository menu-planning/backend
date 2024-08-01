import json

from aio_pika import Message
from attrs import asdict
from src.contexts.food_tracker.shared.domain.events.events import WrongProductAllocated
from src.contexts.food_tracker.shared.rabbitmq_data import email_admin_new_event_data
from src.rabbitmq.aio_pika_manager import AIOPikaManager


async def notify_admin_wrong_product_allocated(
    event: WrongProductAllocated,
    aio_pika_manager: AIOPikaManager,
) -> None:
    async with aio_pika_manager:
        await aio_pika_manager.declare_resources_from_AIOPikaData(
            email_admin_new_event_data
        )
        message = Message(
            body=json.dumps(
                {
                    "event": {"event_name": event.__class__.__name__} | asdict(event),
                }
            ).encode(),
            content_type="application/json",
            # headers={
            #     # "x-message-ttl": <int>,
            #     # "x-max-length": <int>,
            #     "x-dead-letter-exchange": "dlx",
            # },
        )
        await aio_pika_manager.publish_from_AIOPikaData(
            message=message,
            routing_key=email_admin_new_event_data.queue_bind.routing_key,
            aio_pika_data=email_admin_new_event_data,
        )
