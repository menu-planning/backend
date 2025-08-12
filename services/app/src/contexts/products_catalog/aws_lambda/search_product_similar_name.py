import urllib.parse
from typing import Any

import anyio
from pydantic import TypeAdapter
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import ApiProduct
from src.contexts.products_catalog.core.adapters.external_providers.iam.api import (
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

ProductListTypeAdapter = TypeAdapter(list[ApiProduct])

@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to search products by name similarity.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    if not LambdaHelpers.is_localstack_environment():
        user_id = LambdaHelpers.extract_user_id(event)
        if not user_id:
            logger.warning("User ID not found in request context")
            return {
                "statusCode": 401,
                "headers": CORS_headers,
                "body": '{"message": "User ID not found in request context"}',
            }
        
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            logger.warning(f"IAM validation failed for user {user_id}: {response.get('statusCode')}")
            response["headers"] = CORS_headers
            return response
        logger.debug(f"IAM validation successful for user: {user_id}")
    
    name = LambdaHelpers.extract_path_parameter(event, "name")
    if not name:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": "Name parameter is required.",
        }
    
    name = urllib.parse.unquote(name)
    
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Query execution with search name
        logger.debug(f"Searching products with similar name: {name}")
        result = await uow.products.list_top_similar_names(name)
    
    # Business context: Results summary
    logger.debug(f"Found {len(result)} similar products")

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": ProductListTypeAdapter.dump_json(
            (
                [ApiProduct.from_domain(i) for i in result]
                if result
                else []
            )
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
