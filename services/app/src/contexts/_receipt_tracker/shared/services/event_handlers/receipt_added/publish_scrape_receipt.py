import json

from aio_pika import DeliveryMode, Message
from src.contexts._receipt_tracker.shared.adapters.internal_providers.products_catalog.api import (
    ProductsCatalogProvider,
)
from src.contexts._receipt_tracker.shared.domain.events import (
    ItemsAddedToReceipt,
    ProductsAddedToItems,
    ReceiptAdded,
)
from src.contexts._receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts._receipt_tracker.shared.rabbitmq_data import (
    products_added_to_items_data,
    scrape_receipt_data,
)
from src.contexts._receipt_tracker.shared.services.uow import UnitOfWork
from src.rabbitmq.aio_pika_manager import AIOPikaManager


async def publish_scrape_receipt(
    event: ReceiptAdded,
    aio_pika_manager: AIOPikaManager,
) -> None:
    """Publish a message to scrape a receipt.

    Args:
        event: A :class:`NewReceiptAdded <..domain.events.NewReceiptAdded>` instance.
        aio_pika_manager: A :class:`AIOPikaManager <..adapters.aio_pika_manager.AIOPikaManager>` instance.

    Returns:
        None
    """
    async with aio_pika_manager:
        await aio_pika_manager.declare_resources_from_AIOPikaData(
            scrape_receipt_data,
        )
        message = Message(
            delivery_mode=DeliveryMode.PERSISTENT,
            body=json.dumps(
                {
                    "cfe_key": event.cfe_key,
                    "qrcode": event.qrcode,
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
            routing_key=scrape_receipt_data.queue_bind.routing_key,
            aio_pika_data=scrape_receipt_data,
        )


async def add_products_to_items(
    event: ItemsAddedToReceipt,
    uow: UnitOfWork,
    # products_catalog_provider: ProductsCatalogProvider,
) -> None:
    """Add products to items in receipt.

    Args:
        event: :class`ItemsAddedToReceipt <..domain.events.ItemsAddedToReceipt>` instance.

    Returns:
        None
    """
    async with uow:
        products_to_add = {}
        receipt = await uow.receipts.get(event.cfe_key)
        for item in receipt.items:
            if Item.unique_barcode(item.barcode):
                products = await ProductsCatalogProvider.query(
                    filter={"barcode": item.barcode}
                )
            else:
                top_similar_names = await ProductsCatalogProvider.search_by_name(
                    item.description
                )
                if top_similar_names:
                    top_3 = top_similar_names[:3]
                    products = await ProductsCatalogProvider.query(
                        filter={"name": top_3[0]}
                    )
            if products:
                products_to_add[item.barcode] = products[0]
        receipt.add_products_to_items(products_to_add)
        await uow.receipts.persist(receipt)
        await uow.commit()


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
