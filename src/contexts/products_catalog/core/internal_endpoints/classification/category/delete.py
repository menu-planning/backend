from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.classifications.category.delete import (
    DeleteCategory,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_category(
    id: str,
) -> None:
    """Execute the delete category use case.

    Args:
        id: UUID v4 of the category to mark as discarded.

    Returns:
        None: Command executed successfully.

    Events:
        CategoryDeleted: Emitted when category is successfully marked as discarded.

    Idempotency:
        Yes. Key: category_id. Duplicate calls have no effect.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, updates category status in repository.
    """
    cmd = DeleteCategory(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
