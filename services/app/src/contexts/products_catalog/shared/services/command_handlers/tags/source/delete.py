from src.contexts.products_catalog.shared.domain.commands import DeleteSource
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def delete_source(cmd: DeleteSource, uow: UnitOfWork) -> None:
    async with uow:
        tag = await uow.sources.get(cmd.id)
        tag.delete()
        await uow.sources.persist(tag)
        await uow.commit()
