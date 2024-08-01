from src.contexts.food_tracker.shared.domain.commands import DiscardItems
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def discard_items(cmd: DiscardItems, uow: UnitOfWork) -> None:
    async with uow:
        for item in cmd.item_ids:
            item = await uow.items.get(cmd.item_ids)
            item.delete()
            await uow.items.persist(item)
        await uow.commit()
