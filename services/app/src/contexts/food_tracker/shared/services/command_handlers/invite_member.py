from src.contexts.food_tracker.shared.domain.commands import InviteMember
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def invite_member(cmd: InviteMember, uow: UnitOfWork) -> None:
    async with uow:
        house = await uow.houses.get(cmd.house_id)
        house.invite_member(cmd.member_id)
        await uow.houses.persist(house)
        await uow.commit()
