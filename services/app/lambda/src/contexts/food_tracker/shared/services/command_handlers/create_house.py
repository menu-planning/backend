from src.contexts.food_tracker.shared.domain.commands import CreateHouse
from src.contexts.food_tracker.shared.domain.entities.house import House
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def create_house(cmd: CreateHouse, uow: UnitOfWork) -> None:
    async with uow:
        house = House.create_house(owner_id=cmd.owner_id, name=cmd.name)
        await uow.houses.add(house)
        await uow.commit()
