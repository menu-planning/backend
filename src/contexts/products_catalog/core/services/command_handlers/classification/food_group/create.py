from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.food_group.create import (
    CreateFoodGroup,
)
from src.contexts.products_catalog.core.domain.entities.classification.food_group import (
    FoodGroup,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def create_food_group(cmd: CreateFoodGroup, uow: UnitOfWork) -> None:
    """Execute the create food group use case.
    
    Args:
        cmd: Command containing food group data to create.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Events:
        FoodGroupCreated: Emitted upon successful food group creation.
    
    Idempotency:
        No. Duplicate calls with same name will create separate food groups.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Creates new FoodGroup classification entity.
    """
    async with uow:
        classification = FoodGroup.create_classification(**asdict(cmd, recurse=False))
        await uow.food_groups.add(classification)
        await uow.commit()
