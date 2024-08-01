import json
from typing import Any

from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def get(id: str) -> Any:
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        product = await uow.products.get(id)
        return json.dumps(ApiProduct.from_domain(product).model_dump())
