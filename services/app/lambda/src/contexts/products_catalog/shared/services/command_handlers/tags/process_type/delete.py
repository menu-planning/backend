from src.contexts.products_catalog.shared.domain.commands import DeleteProcessType
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def delete_process_type(cmd: DeleteProcessType, uow: UnitOfWork) -> None:
    async with uow:
        tag = await uow.process_types.get(cmd.id)
        tag.delete()
        await uow.process_types.persist(tag)
        await uow.commit()
