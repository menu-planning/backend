from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.category.api_create_category import (
    ApiCreateCategory,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_category(
    data: ApiCreateCategory,
) -> None:
    """Execute the create category use case.

    Args:
        data: Category creation data with required fields.

    Returns:
        None: Command executed successfully.

    Events:
        CategoryCreated: Emitted when category is successfully created.

    Idempotency:
        No. Duplicate calls create multiple categories.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, persists category to repository.
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
