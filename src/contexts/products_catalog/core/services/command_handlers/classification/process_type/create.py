from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.process_type.create import (
    CreateProcessType,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    ProcessType,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def create_process_type(cmd: CreateProcessType, uow: UnitOfWork) -> None:
    async with uow:
        classification = ProcessType.create_classification(**asdict(cmd, recurse=False))
        await uow.process_types.add(classification)
        await uow.commit()
