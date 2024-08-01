from src.contexts.food_tracker.shared.domain.commands import DiscardHouses
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def discard_houses(cmd: DiscardHouses, uow: UnitOfWork) -> None:
    async with uow:
        for house_id in cmd.house_ids:
            house = await uow.houses.get(id=house_id)
            house.delete()
            await uow.houses.persist(house)
        await uow.commit()
