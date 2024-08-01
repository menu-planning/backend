import json
from functools import partial

from aio_pika.abc import AbstractIncomingMessage
from anyio import Semaphore, create_task_group, move_on_after, run, sleep_forever
from src.contexts.food_tracker.shared.adapters.internal_providers.receipt_tracker.api import (
    ReceiptTrackerProvider,
)
from src.contexts.food_tracker.shared.bootstrap.container import Container
from src.contexts.food_tracker.shared.config import settings
from src.contexts.food_tracker.shared.rabbitmq_data import products_added_to_items_data
from src.contexts.food_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.logging.logger import logger
from src.rabbitmq.aio_pika_manager import AIOPikaManager


async def add_item_bulk_callback(
    message: AbstractIncomingMessage,
    semaphore: Semaphore,
) -> None:
    """
    Add items from receipt tracker.
    """
    async with semaphore:
        bus = Container().bootstrap()
        with move_on_after(settings.work_timeout) as scope:
            try:
                message = json.loads(message.body)
                cfe_key = message["cfe_key"]
                uow: UnitOfWork
                async with bus.uow as uow:
                    houses = await uow.houses.query(filter={"cfe_key": cfe_key})
                (
                    _,
                    add_item_bulk_cmd,
                ) = await ReceiptTrackerProvider.get_receipt_and_add_item_bulk_for_house(
                    cfe_key=cfe_key, house_ids=[house.id for house in houses]
                )
                await message.ack()
                await bus.handle(add_item_bulk_cmd)
            except Exception as e:
                logger.error(e)
                await message.reject()
                raise BadRequestException(
                    f"Invalid add item bulk message or inexistent receipt. Message={message}"
                ) from e
        if scope.cancel_called:
            logger.error(f"Request processing time excedeed limit. Message={message}")
            await message.nack(requeue=True)
            # await message.reject()


async def main() -> None:
    semaphore = Semaphore(settings.max_concurrency)
    async with AIOPikaManager() as consumer_manager:
        await consumer_manager.declare_resources_from_AIOPikaData(
            products_added_to_items_data
        )
        queue = await consumer_manager.get_queue_from_AIOPikaData(
            products_added_to_items_data
        )

        async with create_task_group() as tg:
            tg.start_soon(
                consumer_manager.signal_handler,
                tg.cancel_scope,
            )
            tg.start_soon(
                consumer_manager.consume,
                queue,
                partial(add_item_bulk_callback, semaphore=semaphore),
            )
            # prevent the script from finishing
            await sleep_forever()


if __name__ == "__main__":
    logger.info("Starting food_tracker consumer")
    run(main)
    logger.info("Stopping food_tracker consumer")
