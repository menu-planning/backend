from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.process_type.update import (
    UpdateProcessType,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def update_process_type(cmd: UpdateProcessType, uow: UnitOfWork) -> None:
    """Execute the update process type use case.
    
    Args:
        cmd: Command containing process type ID and updates to apply.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If process type with given ID does not exist.
    
    Idempotency:
        Yes. Key: process_type_id + updates hash. Duplicate calls with same updates are safe.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Updates process type classification entity properties.
    """
    async with uow:
        classification = await uow.process_types.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.process_types.persist(classification)
        await uow.commit()
