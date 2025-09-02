from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.classifications.food_group.delete import (
    DeleteFoodGroup,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_food_group(
    id: str,
) -> None:
    """Execute the delete food group use case.

    Args:
        id: UUID v4 of the food group to mark as discarded.

    Returns:
        None: Command executed successfully.

    Events:
        FoodGroupDeleted: Emitted when food group is successfully marked as discarded.

    Idempotency:
        Yes. Key: food_group_id. Duplicate calls have no effect.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, updates food group status in repository.
    """
    cmd = DeleteFoodGroup(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
