from src.contexts.recipes_catalog.shared.domain.commands.meal.update_meal import \
    UpdateMeal
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.logging.logger import logger

async def update_meal_handler(cmd: UpdateMeal, uow: UnitOfWork) -> None:
    async with uow:
        meal = await uow.meals.get(cmd.meal_id)
        logger.debug(f"Meal found: {meal}")
        meal.update_properties(**cmd.updates)
        await uow.meals.persist(meal)
        await uow.commit()
