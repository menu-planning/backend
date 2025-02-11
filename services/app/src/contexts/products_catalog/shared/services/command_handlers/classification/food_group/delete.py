from src.contexts.products_catalog.shared.domain.commands import DeleteFoodGroup
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def delete_food_group(cmd: DeleteFoodGroup, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.food_groups.get(cmd.id)
        classification.delete()
        await uow.food_groups.persist(classification)
        await uow.commit()
