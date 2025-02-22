from src.contexts.recipes_catalog.shared.domain.events.menu.menu_meals_changes import (
    MenuMealsChanged,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def update_meals_menus_ids(evt: MenuMealsChanged, uow: UnitOfWork):
    pass
    meals = await uow.meals.query(
        filter={"id": evt.new_meals_ids + evt.removed_meals_ids}
    )
    for meal in meals:
        meal.menu_id = evt.menu_id
    await uow.meals.persist_all()
    await uow.commit()
