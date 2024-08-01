from src.contexts.recipes_catalog.shared.domain.commands.tags.category.update import (
    UpdateCategory,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def update_category(cmd: UpdateCategory, uow: UnitOfWork) -> None:
    async with uow:
        category = await uow.categories.get(cmd.id)
        category.update_properties(**cmd.updates)
        await uow.categories.persist(category)
        await uow.commit()
