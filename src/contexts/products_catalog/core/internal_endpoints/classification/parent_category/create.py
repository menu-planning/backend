from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.parent_category.api_create_parent_category import (
    ApiCreateParentCategory,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_parent_category(
    data: ApiCreateParentCategory,
) -> None:
    """Execute the create parent category use case.

    Args:
        data: Parent category creation data with required fields.

    Returns:
        None: Command executed successfully.

    Events:
        ParentCategoryCreated: Emitted when parent category is successfully created.

    Idempotency:
        No. Duplicate calls create multiple parent categories.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, persists parent category to repository.
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
