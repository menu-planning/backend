from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.source.create import (
    CreateSource,
)
from src.contexts.products_catalog.core.domain.entities.classification.source import (
    Source,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def create_source(cmd: CreateSource, uow: UnitOfWork) -> None:
    """Execute the create source use case.
    
    Args:
        cmd: Command containing source data to create.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Events:
        SourceCreated: Emitted upon successful source creation.
    
    Idempotency:
        No. Duplicate calls with same name will create separate sources.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Creates new Source classification entity.
    """
    async with uow:
        classification = Source.create_classification(**asdict(cmd, recurse=False))
        await uow.sources.add(classification)
        await uow.commit()
