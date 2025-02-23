from src.contexts.recipes_catalog.shared.domain.events.menu.menu_meals_changed import (
    MenuMealsChanged,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def update_menu_id_on_meals(evt: MenuMealsChanged, uow: UnitOfWork):
    meals = await uow.meals.query(
        filter={"id": evt.new_meals_ids.union(evt.removed_meals_ids)}
    )
    for meal in meals:
        if meal.id in evt.new_meals_ids:
            meal.menu_id = evt.menu_id
        if meal.id in evt.removed_meals_ids:
            meal.menu_id = None
    await uow.meals.persist_all()
    await uow.commit()
