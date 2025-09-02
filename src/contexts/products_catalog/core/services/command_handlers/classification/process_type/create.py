from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.process_type.create import (
    CreateProcessType,
)
from src.contexts.products_catalog.core.domain.entities.classification.process_type import (
    ProcessType,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def create_process_type(cmd: CreateProcessType, uow: UnitOfWork) -> None:
    """Execute the create process type use case.
    
    Args:
        cmd: Command containing process type data to create.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Events:
        ProcessTypeCreated: Emitted upon successful process type creation.
    
    Idempotency:
        No. Duplicate calls with same name will create separate process types.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Creates new ProcessType classification entity.
    """
    async with uow:
        classification = ProcessType.create_classification(**asdict(cmd, recurse=False))
        await uow.process_types.add(classification)
        await uow.commit()
