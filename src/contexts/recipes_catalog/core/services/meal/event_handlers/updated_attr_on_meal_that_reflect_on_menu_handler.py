"""Event handler that updates menu meals when a meal change affects a menu."""

from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import (
    MenuMeal,
)
from src.contexts.recipes_catalog.core.domain.meal.events.updated_attr_that_reflect_on_menu import (
    UpdatedAttrOnMealThatReflectOnMenu,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.logging.logger import structlog_logger

logger = structlog_logger(__name__)


async def update_menu_meals(evt: UpdatedAttrOnMealThatReflectOnMenu, uow: UnitOfWork):
    """Recompute and persist `MenuMeal` attributes derived from a `Meal`.

    Args:
        evt: Event describing the meal-level change that affects a menu.
        uow: Unit of work for repository operations.
    """
    meal = await uow.meals.get(evt.meal_id)
    logger.debug(
        "Meal retrieved successfully",
        meal_id=evt.meal_id,
        meal_name=meal.name,
        operation="update_menu_meals",
    )
    menu = await uow.menus.get(evt.menu_id)
    logger.debug(
        "Menu retrieved successfully",
        menu_id=evt.menu_id,
        operation="update_menu_meals",
    )
    menu_meals: set[MenuMeal] = menu.get_meals_by_ids(set({meal.id}))
    logger.debug(
        "Menu meals retrieved successfully",
        menu_meals=menu_meals,
        operation="update_menu_meals",
    )
    for m in menu_meals:
        new_menu_meal = m.replace(
            meal_name=meal.name,
            nutri_facts=meal.nutri_facts,
        )
        menu.update_meal(new_menu_meal)
    logger.debug(
        "Menu meals updated successfully",
        menu_id=evt.menu_id,
        menu_meals=menu._meals,
        operation="update_menu_meals",
    )
    await uow.menus.persist(menu)
    await uow.commit()
