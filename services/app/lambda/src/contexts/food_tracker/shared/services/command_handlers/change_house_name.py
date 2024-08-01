from src.contexts.food_tracker.shared.domain.commands import ChangeHouseName
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def change_house_name(cmd: ChangeHouseName, uow: UnitOfWork) -> None:
    async with uow:
        house = await uow.houses.get(id=cmd.house_id)
        house.name = cmd.name
        await uow.houses.persist(house)
        await uow.commit()
