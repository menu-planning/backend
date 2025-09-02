from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.food_group.update import (
    UpdateFoodGroup,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def update_food_group(cmd: UpdateFoodGroup, uow: UnitOfWork) -> None:
    """Execute the update food group use case.
    
    Args:
        cmd: Command containing food group ID and updates to apply.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If food group with given ID does not exist.
    
    Idempotency:
        Yes. Key: food_group_id + updates hash. Duplicate calls with same updates are safe.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Updates food group classification entity properties.
    """
    async with uow:
        classification = await uow.food_groups.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.food_groups.persist(classification)
        await uow.commit()
