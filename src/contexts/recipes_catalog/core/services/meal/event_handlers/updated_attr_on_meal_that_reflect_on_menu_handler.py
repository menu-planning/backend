"""Event handler that updates menu meals when a meal change affects a menu."""
from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import (
    MenuMeal,
)
from src.contexts.recipes_catalog.core.domain.meal.events.updated_attr_that_reflect_on_menu import (
    UpdatedAttrOnMealThatReflectOnMenu,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def update_menu_meals(
    evt: UpdatedAttrOnMealThatReflectOnMenu, uow: UnitOfWork
):
    """Recompute and persist `MenuMeal` attributes derived from a `Meal`.

    Args:
        evt: Event describing the meal-level change that affects a menu.
        uow: Unit of work for repository operations.
    """
    meal = await uow.meals.get(evt.meal_id)
    menu = await uow.menus.get(evt.menu_id)
    menu_meals: set[MenuMeal] = menu.get_meals_by_ids(set({meal.id}))
    for m in menu_meals:
        new_menu_meal = m.replace(
            meal_name=meal.name,
            nutri_facts=meal.nutri_facts,
        )
        menu.update_meal(new_menu_meal)
    await uow.menus.persist(menu)
    await uow.commit()
