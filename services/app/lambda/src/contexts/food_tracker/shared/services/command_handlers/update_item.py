from src.contexts.food_tracker.shared.domain.commands import UpdateItem
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def update_item(cmd: UpdateItem, uow: UnitOfWork) -> None:
    async with uow:
        item = await uow.items.get(cmd.item_id)
        item.update_properties(**cmd.updates)
        await uow.items.persist(item)
        await uow.commit()
