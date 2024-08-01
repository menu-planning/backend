from src.contexts.recipes_catalog.shared.domain.commands import DeleteMealPlanning
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_meal_planning(cmd: DeleteMealPlanning, uow: UnitOfWork) -> None:
    async with uow:
        tag = await uow.meal_plannings.get(cmd.id)
        tag.delete()
        await uow.meal_plannings.persist(tag)
        await uow.commit()
