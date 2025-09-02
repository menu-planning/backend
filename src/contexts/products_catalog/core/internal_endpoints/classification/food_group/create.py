from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.food_group.api_create_food_group import (
    ApiCreateFoodGroup,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_food_group(
    data: ApiCreateFoodGroup,
) -> None:
    """Execute the create food group use case.

    Args:
        data: Food group creation data with required fields.

    Returns:
        None: Command executed successfully.

    Events:
        FoodGroupCreated: Emitted when food group is successfully created.

    Idempotency:
        No. Duplicate calls create multiple food groups.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, persists food group to repository.
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
