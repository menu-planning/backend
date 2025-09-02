from src.contexts.products_catalog.core.domain.commands.classifications.category.delete import (
    DeleteCategory,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def delete_category(cmd: DeleteCategory, uow: UnitOfWork) -> None:
    """Execute the delete category use case.
    
    Args:
        cmd: Command containing category ID to delete.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If category with given ID does not exist.
    
    Idempotency:
        Yes. Key: category_id. Duplicate calls are safe after first deletion.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Marks category as deleted, may affect associated products.
    """
    async with uow:
        classification = await uow.categories.get(cmd.id)
        classification.delete()
        await uow.categories.persist(classification)
        await uow.commit()
