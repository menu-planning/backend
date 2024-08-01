from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.tags.source.update import (
    UpdateSource,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def update_source(cmd: UpdateSource, uow: UnitOfWork) -> None:
    async with uow:
        tag = await uow.sources.get(cmd.id)
        tag.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.sources.persist(tag)
        await uow.commit()
