import json

from aio_pika import DeliveryMode, Message
from src.contexts.products_catalog.shared.domain.events import FoodProductCreated
from src.contexts.products_catalog.shared.rabbitmq_data import (
    email_admin_new_product_data,
    scrape_product_image_data,
)
from src.rabbitmq.aio_pika_manager import AIOPikaManager


async def publish_scrape_image_for_new_product(
    event: FoodProductCreated,
    aio_pika_manager: AIOPikaManager,
) -> None:
    if event.barcode is None:
        return
    async with aio_pika_manager:
        await aio_pika_manager.declare_resources_from_AIOPikaData(
            scrape_product_image_data
        )
        message = Message(
            delivery_mode=DeliveryMode.PERSISTENT,
            body=json.dumps(
                {
                    "product_id": event.product_id,
                    "barcode": event.barcode,
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
            routing_key=scrape_product_image_data.queue_bind.routing_key,
            aio_pika_data=scrape_product_image_data,
        )


async def publish_email_admin_of_new_food_product(
    event: FoodProductCreated,
    aio_pika_manager: AIOPikaManager,
) -> None:
    if event.barcode is None or event.data_source != "auto":
        return
    async with aio_pika_manager:
        await aio_pika_manager.declare_resources_from_AIOPikaData(
            email_admin_new_product_data
        )
        message = Message(
            body=json.dumps(
                {
                    "source": event.data_source,
                    "product_id": event.product_id,
                    "barcode": event.barcode,
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
            routing_key=email_admin_new_product_data.queue_bind.routing_key,
            aio_pika_data=email_admin_new_product_data,
        )
