from src.contexts.recipes_catalog.shared.domain.events.meals.meal_deleted import (
    MealDeleted,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_menu_meal(evt: MealDeleted, uow: UnitOfWork):
    pass
    menu = await uow.menus.get(evt.menu_id)
    menu.delete_meal(evt.meal_id)
    await uow.menus.persist(menu)
    await uow.commit()
