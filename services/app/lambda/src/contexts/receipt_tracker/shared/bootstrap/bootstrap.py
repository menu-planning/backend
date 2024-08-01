from collections.abc import Coroutine
from functools import partial

from src.contexts.receipt_tracker.shared.domain import commands, events
from src.contexts.receipt_tracker.shared.services import (
    command_handlers as cmd_handlers,
)
from src.contexts.receipt_tracker.shared.services.event_handlers.receipt_added import (
    publish_scrape_receipt as evt_handlers,
)
from src.contexts.receipt_tracker.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager


def bootstrap(
    uow: UnitOfWork,
    aio_pika_manager: AIOPikaManager,
) -> MessageBus:
    injected_event_handlers: dict[type[events.Event], list[Coroutine]] = {
        events.ReceiptAdded: [
            partial(
                evt_handlers.publish_scrape_receipt, aio_pika_manager=aio_pika_manager
            )
        ],
        events.ItemsAddedToReceipt: [
            partial(evt_handlers.add_products_to_items, uow=uow)
        ],
        events.ProductsAddedToItems: [
            partial(
                evt_handlers.publish_products_added_to_items,
                aio_pika_manager=aio_pika_manager,
            )
        ],
    }

    injected_command_handlers: dict[type[commands.Command], Coroutine] = {
        commands.AddReceipt: partial(cmd_handlers.add_receipt, uow=uow),
        commands.CreateSellerAndUpdateWithScrapedData: partial(
            cmd_handlers.create_seller_and_update_receipt_with_scraped_data, uow=uow
        ),
        commands.UpdateProducts: partial(cmd_handlers.update_products, uow=uow),
    }
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
