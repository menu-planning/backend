import json

from aio_pika import Message
from attrs import asdict
from src.contexts.food_tracker.shared.adapters.internal_providers.products_catalog.api import (
    ProductsCatalogProvider,
)
from src.contexts.food_tracker.shared.domain.events.events import (
    ItemAdded,
    ItemIsFoodChanged,
    ProductNotFound,
    ReceiptCreated,
    WrongProductAllocated,
)
from src.contexts.food_tracker.shared.rabbitmq_data import email_admin_new_event_data
from src.contexts.food_tracker.shared.services.uow import UnitOfWork
from src.rabbitmq.aio_pika_manager import AIOPikaManager


async def notify_admin_new_receipt(
    event: ReceiptCreated,
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


# ItemAdded


async def update_item_product(
    event: ItemAdded,
    uow: UnitOfWork,
) -> None:
    """Update the item's product.

    Args:
        event: :class`ItemAdded <..domain.events.ItemAdded>` instance.
        uow: :class`UnitOfWork <..service.async_uow.UnitOfWork.` instance.

    Returns:
        None
    """
    async with uow:
        item = await uow.items.get(event.item_id)
        if item.product_id is not None:
            return
        if item.is_barcode_unique:
            products_data = await ProductsCatalogProvider.query(
                filter={"barcode": item.barcode}
            )
            if products_data:
                product = products_data[0]
                if product.get("is_food") is False:
                    item.delete()
                else:
                    item.is_food = product.get("is_food")
                    item.product_id = product.get("id")
            else:
                item.product_id = None
        else:
            top_similar_names = await ProductsCatalogProvider.search_by_name(
                item.description
            )
            if top_similar_names:
                top_3 = top_similar_names[:3]
                products_data = await ProductsCatalogProvider.query(
                    filter={"name": top_3}
                )
                ordered_products_data = []
                for name in top_3:
                    for product in products_data:
                        if product.get("name") == name:
                            ordered_products_data.append(product)
                            break
                if not products_data:
                    return
                item.is_food = ordered_products_data[0].get("is_food")
                item.product_id = ordered_products_data[0].get("id")
                item.ids_of_products_with_similar_names = [
                    i.get("id") for i in ordered_products_data
                ]
            else:
                item.product_id = None
        # print(item)
        await uow.items.persist(item)
        await uow.commit()


# WrongProductAlocated


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


# ItemIsFoodChanged


async def add_house_input_and_create_product_if_needed(
    event: ItemIsFoodChanged,
    uow: UnitOfWork,
) -> None:
    async with uow:
        item = await uow.items.get(event.item_id)
    if item.is_barcode_unique:
        await ProductsCatalogProvider.add_house_input_and_create_product_if_needed(
            barcode=event.barcode,
            house_id=event.house_id,
            is_food=event.is_food,
        )


# ProductNotFound


async def notify_admin_product_not_found(
    event: ProductNotFound,
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


# ItemUpdated


# MemberInvited


# NutritionistInvited
