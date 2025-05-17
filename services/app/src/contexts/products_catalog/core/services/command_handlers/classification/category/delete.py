from src.contexts.products_catalog.core.domain.commands import DeleteCategory
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def delete_category(cmd: DeleteCategory, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.categories.get(cmd.id)
        classification.delete()
        await uow.categories.persist(classification)
        await uow.commit()
