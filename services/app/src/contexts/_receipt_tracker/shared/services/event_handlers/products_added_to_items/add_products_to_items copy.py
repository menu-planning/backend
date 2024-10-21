import json

from aio_pika import DeliveryMode, Message
from src.contexts._receipt_tracker.shared.domain.events import ProductsAddedToItems
from src.contexts._receipt_tracker.shared.rabbitmq_data import (
    products_added_to_items_data,
)
from src.rabbitmq.aio_pika_manager import AIOPikaManager


async def publish_products_added_to_items(
    event: ProductsAddedToItems,
    aio_pika_manager: AIOPikaManager,
) -> None:
    """Publish a message that products were added to items.

    Args:
        event: A :class:`ProductsAddedToItems <..domain.events.ProductsAddedToItems>` instance.
        aio_pika_manager: A :class:`AIOPikaManager <..adapters.aio_pika_manager.AIOPikaManager>` instance.

    Returns:
        None
    """
    async with aio_pika_manager:
        await aio_pika_manager.declare_resources_from_AIOPikaData(
            products_added_to_items_data,
        )
        message = Message(
            delivery_mode=DeliveryMode.PERSISTENT,
            body=json.dumps(
                {
                    "cfe_key": event.cfe_key,
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
            routing_key=products_added_to_items_data.queue_bind.routing_key,
            aio_pika_data=products_added_to_items_data,
        )
