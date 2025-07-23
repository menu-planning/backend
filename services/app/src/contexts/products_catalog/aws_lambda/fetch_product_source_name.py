import json
import os
import uuid
from typing import Any, cast

import anyio
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification_filter import ApiClassificationFilter
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_source import ApiSource
from src.contexts.products_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers


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
        logger.debug(f"Fetching product sources for user {user_id}")
        
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
    
    # Use LambdaHelpers for regular query parameters (preserving existing logic)
    query_params: dict[str, Any] | Any = LambdaHelpers.extract_query_parameters(event)
    if not query_params:
        query_params = {}
    
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}

    api = ApiClassificationFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        logger.debug(f"Querying product sources with filters {filters}")
        result = await uow.sources.query(filter=filters)
    logger.debug(f"Sources found: {result}")
    data = [ApiSource.from_domain(i) for i in result] if result else []
    logger.debug(f"Returning sources: {data}")
    
    # Preserve existing dictionary response format
    body = {}
    for i in data:
        body[i.id] = i.name
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps(body),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
