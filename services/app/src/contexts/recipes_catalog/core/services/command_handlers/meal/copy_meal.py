from src.contexts.recipes_catalog.core.domain.commands.meal.copy_meal import CopyMeal
from src.contexts.recipes_catalog.core.domain.entities.meal import Meal
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def copy_meal_handler(cmd: CopyMeal, uow: UnitOfWork):
    async with uow:
        meal_to_be_copied = await uow.meals.get(cmd.meal_id)
        meal = Meal.copy_meal(
            meal=meal_to_be_copied,
            id_of_user_coping_meal=cmd.id_of_user_coping_meal,
            id_of_target_menu=cmd.id_of_target_menu,
        )
        await uow.meals.add(meal)
        await uow.commit()
        await uow.commit()
