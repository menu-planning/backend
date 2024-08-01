from typing import Annotated

from src.contexts.food_tracker.shared.domain.commands import AddItemBulk
from src.contexts.food_tracker.shared.domain.entities.item import Item
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def add_item_bulk(cmd: AddItemBulk, uow: UnitOfWork) -> None:
    async with uow:
        receipts_to_discard: Annotated[dict[str, set[str]], "house_id:set(cfe_key)"] = (
            {}
        )
        for icmd in cmd.add_item_cmds:
            for house_id in icmd.house_ids:
                if receipts_to_discard.get(house_id):
                    receipts_to_discard[house_id].add(icmd.cfe_key)
                else:
                    receipts_to_discard[house_id] = set([icmd.cfe_key])
                item = Item.add_item(
                    house_id=house_id,
                    date=icmd.date,
                    description=icmd.description,
                    amount=icmd.amount,
                    is_food=icmd.is_food,
                    price_per_unit=icmd.price_per_unit,
                    barcode=icmd.barcode,
                    cfe_key=icmd.cfe_key,
                    product_id=icmd.product_id,
                )
                await uow.items.add(item)
        for house_id, cfe_keys in receipts_to_discard.items():
            house = await uow.houses.get(house_id)
            for cfe_key in cfe_keys:
                house.move_receipt_from_pending_to_added(cfe_key=cfe_key)
            await uow.houses.persist(house)
        await uow.commit()
