import json
from typing import Any

from src.contexts.products_catalog.core.adapters.api_schemas.entities.product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def get_filter_options(filter: dict[str, Any] | None = None) -> Any:
    if filter:
        ApiProductFilter(**filter)
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow: # type: ignore
        data = await uow.products.list_filter_options(
            filter=filter,
        )
    return json.dumps(data)
