from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands import CreateSource
from src.contexts.products_catalog.shared.domain.entities.tags import Source
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_source(cmd: CreateSource, uow: UnitOfWork) -> None:
    async with uow:
        tag = Source.create_tag(**asdict(cmd, recurse=False))
        await uow.sources.add(tag)
        await uow.commit()
