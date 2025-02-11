import json
from functools import partial

from aio_pika.abc import AbstractIncomingMessage
from anyio import Semaphore, move_on_after, run, sleep_forever
from src.contexts.products_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.products_catalog.shared.config import settings
from src.contexts.products_catalog.shared.domain.commands.products.update import (
    UpdateProduct,
)
from src.contexts.products_catalog.shared.rabbitmq_data import (
    scrape_product_image_result_data,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger
from src.rabbitmq.aio_pika_manager import AIOPikaManager


async def update_product_image_with_scraped_data(
    message: AbstractIncomingMessage,
    semaphore: Semaphore,
) -> None:
    """
    Update product image url acording to scraper result.

    Args:
        message: A :class:`AbstractIncomingMessage <aio_pika.abc.AbstractIncomingMessage>`
            instance.
        semaphore: A :class:`Semaphore <anyio.Semaphore>` instance.

    Returns:
        None
    """
    async with semaphore:
        with move_on_after(settings.work_timeout) as scope:
            try:
                message = json.loads(message.body)
                product_id = message["product_id"]
                image_url = message["image_url"]
                cmd = UpdateProduct(
                    product_id=product_id, updates={"image_url": image_url}
                )
                await message.ack()
            except Exception as e:
                logger.error(e)
                await message.reject()
            else:
                try:
                    bus: MessageBus = fastapi_bootstrap(
                        get_uow(), get_aio_pika_manager()
                    )
                    await bus.handle(cmd)
                except Exception:
                    logger.error(e)
                    await message.reject()
        if scope.cancel_called:
            logger.error(e)
            await message.reject()


async def main() -> None:
    """
    Consume messages from rabbitmq and update product image url acording to scraper result.
    """
    semaphore = Semaphore(settings.max_concurrency)
    async with AIOPikaManager() as consumer:
        await consumer.declare_resources_from_AIOPikaData(
            scrape_product_image_result_data
        )
        queue = await consumer.get_queue_from_AIOPikaData(
            scrape_product_image_result_data
        )
        await consumer.consume(
            queue,
            partial(update_product_image_with_scraped_data, semaphore=semaphore),
        )
        # prevent the script from finishing
        await sleep_forever()


if __name__ == "__main__":
    run(main)
