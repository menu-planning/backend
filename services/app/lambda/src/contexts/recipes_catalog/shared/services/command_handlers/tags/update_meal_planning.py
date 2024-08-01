from src.contexts.recipes_catalog.shared.domain.commands.tags.meal_planning.update import (
    UpdateMealPlanning,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def update_meal_planning(cmd: UpdateMealPlanning, uow: UnitOfWork) -> None:
    async with uow:
        meal_planning = await uow.meal_plannings.get(cmd.id)
        meal_planning.update_properties(**cmd.updates)
        await uow.meal_plannings.persist(meal_planning)
        await uow.commit()
