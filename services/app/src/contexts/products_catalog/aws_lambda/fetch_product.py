import json
import os
import uuid
from typing import Any

import anyio
from src.contexts.products_catalog.core.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.products_catalog.core.adapters.api_schemas.entities.product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.seedwork.shared.utils import custom_serializer
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for products.
    """
    logger.debug(f"Event received {event}")
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        logger.debug(f"Fetching products for user {user_id}")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
    query_params: dict[str, Any] | Any = (
        event.get("multiValueQueryStringParameters") if event.get("multiValueQueryStringParameters") else {}
    )
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}
    filters["limit"] = int(query_params.get("limit", 50))
    filters["sort"] = query_params.get("sort", "-updated_at")
    
    for k, v in filters.items():
        if isinstance(v, list) and len(v) == 1:
            filters[k] = v[0]
            
    api = ApiProductFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        logger.debug(f"Querying products with filters {filters}")
        result = await uow.products.query(filter=filters)
    logger.debug(f"Products found: {result}")
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps(
            [ApiProduct.from_domain(i).model_dump() for i in result] if result else [],
            default=custom_serializer,
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
