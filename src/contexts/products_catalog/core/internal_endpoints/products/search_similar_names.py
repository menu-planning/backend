import json
from typing import Any

from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def search_similar_name(name: str) -> Any:
    """Execute the search similar product names query use case.

    Args:
        name: Product name to search for similar matches.

    Returns:
        JSON string: Serialized list of similar product names.

    Transactions:
        One UnitOfWork per call. Read-only transaction.

    Side Effects:
        None. Pure query operation.
    """
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        names = await uow.products.list_top_similar_names(name)
    return json.dumps(names)
