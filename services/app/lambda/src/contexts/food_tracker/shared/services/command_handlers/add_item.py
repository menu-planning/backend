from src.contexts.food_tracker.shared.domain.commands import AddItem
from src.contexts.food_tracker.shared.domain.entities.item import Item
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def add_item(cmd: AddItem, uow: UnitOfWork) -> None:
    async with uow:
        for house_id in cmd.house_ids:
            item = Item.add_item(
                house_id=house_id,
                date=cmd.date,
                description=cmd.description,
                amount=cmd.amount,
                is_food=cmd.is_food,
                price_per_unit=cmd.price_per_unit,
                barcode=cmd.barcode,
                cfe_key=cmd.cfe_key,
                product_id=cmd.product_id,
            )
            await uow.items.add(item)
        await uow.commit()
