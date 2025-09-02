from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.brand.api_create_brand import (
    ApiCreateBrand,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_brand(
    data: ApiCreateBrand,
) -> None:
    """Execute the create brand use case.

    Args:
        data: Brand creation data with required fields.

    Returns:
        None: Command executed successfully.

    Events:
        BrandCreated: Emitted when brand is successfully created.

    Idempotency:
        No. Duplicate calls create multiple brands.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, persists brand to repository.
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
