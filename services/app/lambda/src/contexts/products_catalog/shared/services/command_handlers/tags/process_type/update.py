from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.tags.process_type.update import (
    UpdateProcessType,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def update_process_type(cmd: UpdateProcessType, uow: UnitOfWork) -> None:
    async with uow:
        tag = await uow.process_types.get(cmd.id)
        tag.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.process_types.persist(tag)
        await uow.commit()
