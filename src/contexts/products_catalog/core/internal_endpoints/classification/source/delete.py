from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.classifications.source.delete import (
    DeleteSource,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_source(
    id: str,
) -> None:
    """Execute the delete source use case.

    Args:
        id: UUID v4 of the source to mark as discarded.

    Returns:
        None: Command executed successfully.

    Events:
        SourceDeleted: Emitted when source is successfully marked as discarded.

    Idempotency:
        Yes. Key: source_id. Duplicate calls have no effect.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, updates source status in repository.
    """
    cmd = DeleteSource(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
