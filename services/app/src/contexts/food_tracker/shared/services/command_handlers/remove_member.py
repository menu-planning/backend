from src.contexts.food_tracker.shared.domain.commands import RemoveMember
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def remove_member(cmd: RemoveMember, uow: UnitOfWork) -> None:
    async with uow:
        house = await uow.houses.get(cmd.house_id)
        house.remove_member(cmd.member_id)
        await uow.houses.persist(house)
        await uow.commit()
