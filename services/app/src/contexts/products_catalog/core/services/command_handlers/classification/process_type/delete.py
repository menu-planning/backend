from src.contexts.products_catalog.core.domain.commands import DeleteProcessType
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def delete_process_type(cmd: DeleteProcessType, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.process_types.get(cmd.id)
        classification.delete()
        await uow.process_types.persist(classification)
        await uow.commit()
