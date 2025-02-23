from src.contexts.recipes_catalog.shared.domain.events.menu.menu_deleted import (
    MenuDeleted,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_related_meals(evt: MenuDeleted, uow: UnitOfWork):
    meals = await uow.meals.query(filter={"menu_id": evt.menu_id})
    for meal in meals:
        meal._discard()
    await uow.meals.persist_all()
    await uow.commit()
