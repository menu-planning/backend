from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.classifications.source.update import (
    UpdateSource,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def update_source(cmd: UpdateSource, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.sources.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.sources.persist(classification)
        await uow.commit()
