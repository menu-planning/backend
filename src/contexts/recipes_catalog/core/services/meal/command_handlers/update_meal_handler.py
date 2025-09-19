from src.contexts.recipes_catalog.core.domain.meal.commands.update_meal import (
    UpdateMeal,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.logging.logger import get_logger


async def update_meal_handler(cmd: UpdateMeal, uow: UnitOfWork) -> None:
    """Handle meal update command with structured logging.

    Args:
        cmd: UpdateMeal command containing meal_id and updates
        uow: Unit of work for transaction management
    """
    logger = get_logger("meal.update_handler")

    logger.info(
        "Starting meal update",
        meal_id=cmd.meal_id,
        update_fields=list(cmd.updates.keys()),
        operation="update_meal"
    )

    async with uow:
        meal = await uow.meals.get(cmd.meal_id)

        if not meal:
            logger.error(
                "Meal not found for update",
                meal_id=cmd.meal_id,
                operation="update_meal"
            )
            raise ValueError(f"Meal with id {cmd.meal_id} not found")

        logger.debug(
            "Meal retrieved successfully",
            meal_id=cmd.meal_id,
            meal_name=getattr(meal, 'name', 'unknown'),
            recipe_count=len(meal.recipes),
            operation="update_meal"
        )

        meal.update_properties(**cmd.updates)
        await uow.meals.persist(meal)
        await uow.commit()

        logger.info(
            "Meal updated successfully",
            meal_id=cmd.meal_id,
            updated_fields=list(cmd.updates.keys()),
            operation="update_meal"
        )
