import os
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
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers

container = Container()


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to retrieve a specific product by id.
    """
    logger.debug(f"Getting product by id: {event}")
    
    # Use LambdaHelpers for environment detection
    if not LambdaHelpers.is_localstack_environment():
        # Use LambdaHelpers for user ID extraction
        user_id = LambdaHelpers.extract_user_id(event)
        logger.debug(f"User id: {user_id}")
        
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
    product_id = LambdaHelpers.extract_path_parameter(event, "id")
    logger.debug(f"Product id: {product_id}")
    
    # Validate required path parameter
    if not product_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": '{"message": "Product ID is required"}',
        }
    
    # At this point, product_id is guaranteed to be a string
    product_id = cast(str, product_id)
    
    bus: MessageBus = container.bootstrap()

    uow: UnitOfWork
    async with bus.uow as uow:
        product = await uow.products.get(product_id)
    api = ApiProduct.from_domain(product)
    
    # Use existing CORS_headers to maintain backward compatibility
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": api.model_dump_json(),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """

    Lambda function handler to retrieve a specific product by id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
