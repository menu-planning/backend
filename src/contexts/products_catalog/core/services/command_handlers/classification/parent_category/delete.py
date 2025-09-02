from src.contexts.products_catalog.core.domain.commands.classifications.parent_category.delete import (
    DeleteParentCategory,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def delete_parent_category(cmd: DeleteParentCategory, uow: UnitOfWork) -> None:
    """Execute the delete parent category use case.
    
    Args:
        cmd: Command containing parent category ID to delete.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If parent category with given ID does not exist.
    
    Idempotency:
        Yes. Key: parent_category_id. Duplicate calls are safe after first deletion.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Marks parent category as deleted, may affect associated products.
    """
    async with uow:
        classification = await uow.parent_categories.get(cmd.id)
        classification.delete()
        await uow.parent_categories.persist(classification)
        await uow.commit()
