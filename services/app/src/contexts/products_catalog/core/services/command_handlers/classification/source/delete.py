from src.contexts.products_catalog.core.domain.commands import DeleteSource
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def delete_source(cmd: DeleteSource, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.sources.get(cmd.id)
        classification.delete()
        await uow.sources.persist(classification)
        await uow.commit()
