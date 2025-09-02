from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.parent_category.update import (
    UpdateParentCategory,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def update_parent_category(cmd: UpdateParentCategory, uow: UnitOfWork) -> None:
    """Execute the update parent category use case.
    
    Args:
        cmd: Command containing parent category ID and updates to apply.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If parent category with given ID does not exist.
    
    Idempotency:
        Yes. Key: parent_category_id + updates hash. Duplicate calls with same updates are safe.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Updates parent category classification entity properties.
    """
    async with uow:
        classification = await uow.parent_categories.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.parent_categories.persist(classification)
        await uow.commit()
