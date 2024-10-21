import json
from datetime import datetime
from functools import partial

import anyio
from aio_pika.abc import AbstractIncomingMessage
from src.contexts._receipt_tracker.shared.adapters.api_schemas.value_objects.item import (
    ApiItem,
)
from src.contexts._receipt_tracker.shared.adapters.api_schemas.value_objects.seller import (
    ApiSeller,
)
from src.contexts._receipt_tracker.shared.bootstrap.container import Container
from src.contexts._receipt_tracker.shared.config import settings
from src.contexts._receipt_tracker.shared.domain.commands import (
    CreateSellerAndUpdateWithScrapedData,
)
from src.contexts._receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts._receipt_tracker.shared.domain.value_objects.seller import Seller
from src.contexts._receipt_tracker.shared.rabbitmq_data import (
    scrape_receipt_result_data,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger
from src.rabbitmq.aio_pika_manager import AIOPikaManager

TIMEOUT = 35


async def create_seller_and_update_receipt_with_scraped_data(
    message: AbstractIncomingMessage,
    semaphore: anyio.Semaphore,
) -> None:
    """
    Update receipt data and create seller acording to scraper result.

    Args:
        message: A :class:`AbstractIncomingMessage <aio_pika.abc.AbstractIncomingMessage>`
            instance.
        semaphore: A :class:`Semaphore <anyio.Semaphore>` instance.

    Returns:
        None
    """
    async with semaphore:
        with anyio.move_on_after(TIMEOUT) as scope:
            message = json.loads(message.body)
            cfe_key = message["cfe_key"]
            date = message["date"]
            seller = message["seller"]
            items = message["items"]
            try:
                seller = ApiSeller(**seller)
                items = [ApiItem(**item) for item in items]
                cmd = CreateSellerAndUpdateWithScrapedData(
                    cfe_key=cfe_key,
                    date=datetime.fromisoformat(date),
                    seller=Seller(**seller.model_dump()),
                    items=[Item(**item.model_dump()) for item in items],
                )
                message.ack()
            except Exception as e:
                logger.error(e)
                message.reject()
            else:
                try:
                    bus: MessageBus = Container().bootstrap()
                    await bus.handle(cmd, timeout=TIMEOUT - 1)
                except Exception:
                    logger.error(e)
                    await message.reject()
        if scope.cancel_called:
            logger.error(e)
            await message.reject()


async def main() -> None:
    """
    Consume messages from rabbitmq and update receipt data and create seller acording to
    scraper result.
    """
    semaphore = anyio.Semaphore(settings.max_concurrency)
    async with AIOPikaManager() as consumer:
        await consumer.declare_resources_from_AIOPikaData(scrape_receipt_result_data)
        queue = await consumer.get_queue_from_AIOPikaData(scrape_receipt_result_data)
        await consumer.consume(
            queue,
            partial(
                create_seller_and_update_receipt_with_scraped_data, semaphore=semaphore
            ),
        )
        # prevent the script from finishing
        await anyio.sleep_forever()


if __name__ == "__main__":
    anyio.run(main)
