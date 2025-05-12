from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
from src.contexts.recipes_catalog.shared.domain.events.meal.meal_deleted import (
    MealDeleted,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def remove_meals_from_menu(evt: MealDeleted, uow: UnitOfWork):
    menu: Menu = await uow.menus.get(evt.menu_id)
    menu.remove_meals(frozenset({evt.meal_id}))
    await uow.menus.persist(menu)
    await uow.commit()
