import json
from typing import Any

from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def get_products(filters: dict[str, Any] | None = None) -> Any:
    """Execute the get products query use case.

    Args:
        filters: Optional product filter criteria.

    Returns:
        JSON string: Serialized list of products matching filters.

    Transactions:
        One UnitOfWork per call. Read-only transaction.

    Side Effects:
        None. Pure query operation.
    """
    if filters:
        ApiProductFilter(**filters)
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        products = await uow.products.query(
            filters=filters if filters else {},
        )
    return json.dumps(
        [ApiProduct.from_domain(product).model_dump() for product in products] # type: ignore
    )
