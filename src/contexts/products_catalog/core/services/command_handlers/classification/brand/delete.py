from src.contexts.products_catalog.core.domain.commands.classifications.brand.delete import (
    DeleteBrand,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def delete_brand(cmd: DeleteBrand, uow: UnitOfWork) -> None:
    """Execute the delete brand use case.
    
    Args:
        cmd: Command containing brand ID to delete.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If brand with given ID does not exist.
    
    Idempotency:
        Yes. Key: brand_id. Duplicate calls are safe after first deletion.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Marks brand as deleted, may affect associated products.
    """
    async with uow:
        classification = await uow.brands.get(cmd.id)
        classification.delete()
        await uow.brands.persist(classification)
        await uow.commit()
