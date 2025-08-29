from src.contexts.recipes_catalog.core.domain.client.events.menu_deleted import (
    MenuDeleted,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def delete_related_meals(evt: MenuDeleted, uow: UnitOfWork):
    meals = await uow.meals.query(filters={"menu_id": evt.menu_id})
    for meal in meals:
        meal._discard()
    await uow.meals.persist_all(meals)
    await uow.commit()
