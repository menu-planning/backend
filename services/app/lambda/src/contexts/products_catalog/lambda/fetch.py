import uuid
from typing import Any

import anyio
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.decorators import lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger


@lambda_exception_handler
async def async_fetch(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for products.
    """
    # Extract query parameters from the event
    query_params = event.get("queryStringParameters", {})
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}
    filters["limit"] = int(query_params.get("limit", 500))
    filters["sort"] = query_params.get("sort", "-date")

    api = ApiProductFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result = await uow.products.query(filter=filters)
    return {
        "statusCode": 200,
        "body": (
            [ApiProduct.from_domain(i).model_dump_json() for i in result]
            if result
            else []
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_fetch, event, context)
