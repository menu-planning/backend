from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.classifications.process_type.create import (
    CreateProcessType,
)
from src.contexts.products_catalog.shared.domain.entities.classification import (
    ProcessType,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_process_type(cmd: CreateProcessType, uow: UnitOfWork) -> None:
    async with uow:
        classification = ProcessType.create_classification(**asdict(cmd, recurse=False))
        await uow.process_types.add(classification)
        await uow.commit()
