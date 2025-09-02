from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.source.api_create_source import (
    ApiCreateSource,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_source(
    data: ApiCreateSource,
) -> None:
    """Execute the create source use case.

    Args:
        data: Source creation data with required fields.

    Returns:
        None: Command executed successfully.

    Events:
        SourceCreated: Emitted when source is successfully created.

    Idempotency:
        No. Duplicate calls create multiple sources.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, persists source to repository.
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
