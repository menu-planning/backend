import json

from aio_pika import DeliveryMode, Message
from src.contexts.products_catalog.shared.domain.commands.products.add_image import (
    AddProductImage,
)
from src.contexts.products_catalog.shared.rabbitmq_data import scrape_product_image_data
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.rabbitmq.aio_pika_manager import AIOPikaManager


async def publish_save_product_image(
    cmd: AddProductImage,
    uow: UnitOfWork,
    aio_pika_manager: AIOPikaManager,
) -> None:
    async with uow:
        await uow.products.get(cmd.product_id)
    async with aio_pika_manager:
        await aio_pika_manager.declare_resources_from_AIOPikaData(
            scrape_product_image_data
        )
        message = Message(
            delivery_mode=DeliveryMode.PERSISTENT,
            body=json.dumps(
                {
                    "product_id": cmd.product_id,
                    "image_url": cmd.image_url,
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
