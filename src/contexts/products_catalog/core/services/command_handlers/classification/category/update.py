from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.category.update import (
    UpdateCategory,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def update_category(cmd: UpdateCategory, uow: UnitOfWork) -> None:
    """Execute the update category use case.
    
    Args:
        cmd: Command containing category ID and updates to apply.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If category with given ID does not exist.
    
    Idempotency:
        Yes. Key: category_id + updates hash. Duplicate calls with same updates are safe.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Updates category classification entity properties.
    """
    async with uow:
        classification = await uow.categories.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.categories.persist(classification)
        await uow.commit()
