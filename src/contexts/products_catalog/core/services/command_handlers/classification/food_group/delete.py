from src.contexts.products_catalog.core.domain.commands.classifications.food_group.delete import (
    DeleteFoodGroup,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def delete_food_group(cmd: DeleteFoodGroup, uow: UnitOfWork) -> None:
    """Execute the delete food group use case.
    
    Args:
        cmd: Command containing food group ID to delete.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If food group with given ID does not exist.
    
    Idempotency:
        Yes. Key: food_group_id. Duplicate calls are safe after first deletion.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Marks food group as deleted, may affect associated products.
    """
    async with uow:
        classification = await uow.food_groups.get(cmd.id)
        classification.delete()
        await uow.food_groups.persist(classification)
        await uow.commit()
