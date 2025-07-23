import json
import os
import uuid
from typing import Any, cast

import anyio
from pydantic import TypeAdapter
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import ApiProduct
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product_filter import ApiProductFilter
from src.contexts.products_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.seedwork.shared.utils import custom_serializer
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers

container = Container()

ProductListTypeAdapter = TypeAdapter(list[ApiProduct])


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for products.
    """
    logger.debug(f"Event received {event}")
    
    # Use LambdaHelpers for environment detection
    if not LambdaHelpers.is_localstack_environment():
        # Use LambdaHelpers for user ID extraction
        user_id = LambdaHelpers.extract_user_id(event)
        logger.debug(f"Fetching products for user {user_id}")
        
        # Validate user ID extraction
        if not user_id:
            return {
                "statusCode": 401,
                "headers": CORS_headers,
                "body": '{"message": "User ID not found in request context"}',
            }
        
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            # Ensure IAM error responses include CORS headers
            response["headers"] = CORS_headers
            return response
    
    # Use LambdaHelpers for multi-value query parameters (preserving exact existing logic)
    query_params: dict[str, Any] | Any = LambdaHelpers.extract_multi_value_query_parameters(event)
    if not query_params:
        query_params = {}
    
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}
    
    # Handle limit parameter - extract from list if it's a list
    limit_value = query_params.get("limit", [50])
    if isinstance(limit_value, list):
        limit_value = limit_value[0] if limit_value else 50
    filters["limit"] = int(limit_value)
    
    # Handle sort parameter - extract from list if it's a list  
    sort_value = query_params.get("sort", ["-updated_at"])
    if isinstance(sort_value, list):
        sort_value = sort_value[0] if sort_value else "-updated_at"
    filters["sort"] = sort_value
    
    for k, v in filters.items():
        if isinstance(v, list) and len(v) == 1:
            filters[k] = v[0]
            
    api = ApiProductFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        logger.debug(f"Querying products with filters {filters}")
        result: list[Product] = await uow.products.query(filter=filters) # type: ignore
    logger.debug(f"Products found: {result}")
    
    # Preserve existing response format and serialization
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": ProductListTypeAdapter.dump_json(
            [ApiProduct.from_domain(i) for i in result] if result else []
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
