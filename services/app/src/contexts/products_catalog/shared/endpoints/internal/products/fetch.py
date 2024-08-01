import json
from typing import Any

from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def get_products(filter: dict[str, Any] | None = None) -> Any:
    if filter:
        ApiProductFilter(**filter)
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        products = await uow.products.query(
            filter=filter,
        )
    return json.dumps(
        [ApiProduct.from_domain(product).model_dump() for product in products]
    )
