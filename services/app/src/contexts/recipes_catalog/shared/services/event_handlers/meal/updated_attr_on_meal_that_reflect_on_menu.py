from src.contexts.recipes_catalog.shared.domain.events.meal.updated_attr_that_reflect_on_menu import (
    UpdatedAttrOnMealThatReflectOnMenu,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import MenuMeal
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def update_menu_meals(
    evt: UpdatedAttrOnMealThatReflectOnMenu, uow: UnitOfWork
):
    meal = await uow.meals.get(evt.meal_id)
    menu = await uow.menus.get(evt.menu_id)
    menu_meals: set[MenuMeal] = menu.get_meals_by_ids(meal.id)
    for m in menu_meals:
        new_menu_meal = m.replace(
            # meal_id=meal.id,
            meal_name=meal.name,
            nutri_facts=meal.nutri_facts,
        )
        menu.update_meal(new_menu_meal)
    await uow.menus.persist(menu)
    await uow.commit()
