from src.contexts.food_tracker.shared.domain.commands import InviteNutritionist
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def invite_nutritionist(cmd: InviteNutritionist, uow: UnitOfWork) -> None:
    async with uow:
        house = await uow.houses.get(cmd.house_id)
        house.invite_nutritionist(cmd.nutritionist_id)
        await uow.houses.persist(house)
        await uow.commit()
