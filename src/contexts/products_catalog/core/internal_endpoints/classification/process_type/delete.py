from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.classifications.process_type.delete import (
    DeleteProcessType,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_process_type(
    id: str,
) -> None:
    """Execute the delete process type use case.

    Args:
        id: UUID v4 of the process type to mark as discarded.

    Returns:
        None: Command executed successfully.

    Events:
        ProcessTypeDeleted: Emitted when process type is successfully marked as discarded.

    Idempotency:
        Yes. Key: process_type_id. Duplicate calls have no effect.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, updates process type status in repository.
    """
    cmd = DeleteProcessType(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
