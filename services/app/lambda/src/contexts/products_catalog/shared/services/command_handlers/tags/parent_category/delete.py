from src.contexts.products_catalog.shared.domain.commands import DeleteParentCategory
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def delete_parent_category(cmd: DeleteParentCategory, uow: UnitOfWork) -> None:
    async with uow:
        tag = await uow.parent_categories.get(cmd.id)
        tag.delete()
        await uow.parent_categories.persist(tag)
        await uow.commit()
