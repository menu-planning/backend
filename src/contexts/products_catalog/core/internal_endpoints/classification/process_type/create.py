from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.process_type.api_create_process_type import (
    ApiCreateProcessType,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_process_type(
    data: ApiCreateProcessType,
) -> None:
    """Execute the create process type use case.

    Args:
        data: Process type creation data with required fields.

    Returns:
        None: Command executed successfully.

    Events:
        ProcessTypeCreated: Emitted when process type is successfully created.

    Idempotency:
        No. Duplicate calls create multiple process types.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, persists process type to repository.
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
