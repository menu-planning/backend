import json
import os
import urllib.parse
import uuid
from typing import Any, cast

import anyio
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import ApiProduct
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
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers

container = Container()


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to search products by name similarity.
    """
    logger.debug(f"Event received {event}")
    
    # Use LambdaHelpers for environment detection
    if not LambdaHelpers.is_localstack_environment():
        # Use LambdaHelpers for user ID extraction
        user_id = LambdaHelpers.extract_user_id(event)
        
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
    
    # Use LambdaHelpers for path parameter extraction
    name = LambdaHelpers.extract_path_parameter(event, "name")
    if not name:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": "Name parameter is required.",
        }
    
    # Preserve existing URL decoding logic
    name = urllib.parse.unquote(name)
    
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result = await uow.products.list_top_similar_names(name)
    logger.debug(f"Found {len(result)} products similar to {name}")
    logger.debug(f"Result: {result[0] if result else []}")
    logger.debug(f"Result1: {ApiProduct.from_domain(result[0]) if result else []}")
    logger.debug(
        f"Result2: {json.dumps(ApiProduct.from_domain(result[0]).model_dump() if result else [],default=custom_serializer)}"
    )
    
    # Preserve existing response format and serialization
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps(
            (
                [ApiProduct.from_domain(i).model_dump() for i in result]
                if result
                else []
            ),
            default=custom_serializer,
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
