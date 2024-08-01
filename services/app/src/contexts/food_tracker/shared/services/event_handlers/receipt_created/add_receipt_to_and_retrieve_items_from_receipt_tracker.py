from attrs import asdict
from src.contexts.food_tracker.shared.adapters.internal_providers.receipt_tracker.api import (
    ReceiptTrackerProvider,
)
from src.contexts.food_tracker.shared.domain.commands.add_item_bulk import AddItemBulk
from src.contexts.food_tracker.shared.domain.entities.item import Item
from src.contexts.food_tracker.shared.domain.events.events import ReceiptCreated
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def add_receipt_to_and_retrieve_items_from_receipt_tracker(
    event: ReceiptCreated,
    uow: UnitOfWork,
) -> None:
    """Add the receipt to a house on the receipt tracker module. If receipt
    already exists for .

    Args:
        event: :class`ReceiptCreated <..domain.events.ReceiptCreated>` instance.
        uow: :class`UnitOfWork <..service.async_uow.UnitOfWork.` instance.

    Returns:
        None
    """
    await ReceiptTrackerProvider.add(
        house_id=event.house_id,
        cfe_key=event.cfe_key,
        qrcode=event.qrcode,
    )
    add_item_bulk_cmd: AddItemBulk
    (
        _,
        add_item_bulk_cmd,
    ) = await ReceiptTrackerProvider.get_receipt_and_add_item_bulk_for_house(
        cfe_key=event.cfe_key, house_ids=[event.house_id]
    )
    if add_item_bulk_cmd.add_item_cmds:
        async with uow:
            for add_item_cmd in add_item_bulk_cmd.add_item_cmds:
                kwargs = asdict(add_item_cmd)
                kwargs.update({"house_id": event.house_id})
                item = Item.add_item(**kwargs)
                await uow.items.add(item)
            house = await uow.houses.get(event.house_id)
            house.move_receipt_from_pending_to_added(cfe_key=event.cfe_key)
            await uow.houses.persist(house)
            await uow.commit()
