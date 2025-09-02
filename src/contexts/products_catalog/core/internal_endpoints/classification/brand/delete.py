from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.classifications.brand.delete import (
    DeleteBrand,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_brand(
    id: str,
) -> None:
    """Execute the delete brand use case.

    Args:
        id: UUID v4 of the brand to mark as discarded.

    Returns:
        None: Command executed successfully.

    Events:
        BrandDeleted: Emitted when brand is successfully marked as discarded.

    Idempotency:
        Yes. Key: brand_id. Duplicate calls have no effect.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, updates brand status in repository.
    """
    cmd = DeleteBrand(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
