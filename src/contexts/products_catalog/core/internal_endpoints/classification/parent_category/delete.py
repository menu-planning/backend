from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.classifications.parent_category.delete import (
    DeleteParentCategory,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_parent_category(
    id: str,
) -> None:
    """Execute the delete parent category use case.

    Args:
        id: UUID v4 of the parent category to mark as discarded.

    Returns:
        None: Command executed successfully.

    Events:
        ParentCategoryDeleted: Emitted when parent category is successfully marked as discarded.

    Idempotency:
        Yes. Key: parent_category_id. Duplicate calls have no effect.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, updates parent category status in repository.
    """
    cmd = DeleteParentCategory(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
