from src.contexts.food_tracker.shared.domain.commands import RemoveNutritionist
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def remove_nutritionist(cmd: RemoveNutritionist, uow: UnitOfWork) -> None:
    async with uow:
        house = await uow.houses.get(cmd.house_id)
        house.remove_nutritionist(cmd.nutritionist_id)
        await uow.houses.persist(house)
        await uow.commit()
