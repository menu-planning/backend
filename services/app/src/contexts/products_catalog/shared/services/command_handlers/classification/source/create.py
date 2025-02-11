from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.classifications.source.create import (
    CreateSource,
)
from src.contexts.products_catalog.shared.domain.entities.classification import Source
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_source(cmd: CreateSource, uow: UnitOfWork) -> None:
    async with uow:
        classification = Source.create_classification(**asdict(cmd, recurse=False))
        await uow.sources.add(classification)
        await uow.commit()
