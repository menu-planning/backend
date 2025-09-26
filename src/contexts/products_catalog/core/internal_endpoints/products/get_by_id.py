import json
from typing import Any

from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def get(id: str) -> Any:
    """Execute the get product by ID query use case.

    Args:
        id: UUID v4 of the product to retrieve.

    Returns:
        JSON string: Serialized product data.

    Transactions:
        One UnitOfWork per call. Read-only transaction.

    Side Effects:
        None. Pure query operation.
    """
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        product = await uow.products.get(id)
        return json.dumps(ApiProduct.from_domain(product).model_dump())
