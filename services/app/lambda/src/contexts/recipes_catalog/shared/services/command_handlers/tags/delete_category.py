from src.contexts.recipes_catalog.shared.domain.commands import DeleteCategory
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_category(cmd: DeleteCategory, uow: UnitOfWork) -> None:
    async with uow:
        tag = await uow.categories.get(cmd.id)
        tag.delete()
        await uow.categories.persist(tag)
        await uow.commit()
