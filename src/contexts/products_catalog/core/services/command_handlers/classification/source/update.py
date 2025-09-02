from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.source.update import (
    UpdateSource,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def update_source(cmd: UpdateSource, uow: UnitOfWork) -> None:
    """Execute the update source use case.
    
    Args:
        cmd: Command containing source ID and updates to apply.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If source with given ID does not exist.
    
    Idempotency:
        Yes. Key: source_id + updates hash. Duplicate calls with same updates are safe.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Updates source classification entity properties.
    """
    async with uow:
        classification = await uow.sources.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.sources.persist(classification)
        await uow.commit()
