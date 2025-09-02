from src.contexts.products_catalog.core.domain.commands.classifications.process_type.delete import (
    DeleteProcessType,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def delete_process_type(cmd: DeleteProcessType, uow: UnitOfWork) -> None:
    """Execute the delete process type use case.
    
    Args:
        cmd: Command containing process type ID to delete.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If process type with given ID does not exist.
    
    Idempotency:
        Yes. Key: process_type_id. Duplicate calls are safe after first deletion.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Marks process type as deleted, may affect associated products.
    """
    async with uow:
        classification = await uow.process_types.get(cmd.id)
        classification.delete()
        await uow.process_types.persist(classification)
        await uow.commit()
