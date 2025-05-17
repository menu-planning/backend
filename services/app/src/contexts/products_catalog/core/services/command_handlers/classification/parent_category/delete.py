from src.contexts.products_catalog.core.domain.commands import DeleteParentCategory
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def delete_parent_category(cmd: DeleteParentCategory, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.parent_categories.get(cmd.id)
        classification.delete()
        await uow.parent_categories.persist(classification)
        await uow.commit()
