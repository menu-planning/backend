from src.contexts.products_catalog.core.domain.commands.classifications.source.delete import (
    DeleteSource,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def delete_source(cmd: DeleteSource, uow: UnitOfWork) -> None:
    """Execute the delete source use case.
    
    Args:
        cmd: Command containing source ID to delete.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If source with given ID does not exist.
    
    Idempotency:
        Yes. Key: source_id. Duplicate calls are safe after first deletion.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Marks source as deleted, may affect associated products.
    """
    async with uow:
        classification = await uow.sources.get(cmd.id)
        classification.delete()
        await uow.sources.persist(classification)
        await uow.commit()
