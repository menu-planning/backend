import json
from typing import Any

import anyio
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

container = Container()


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to retrieve a specific source by id.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event)}")
    
    if not LambdaHelpers.is_localstack_environment():
        user_id = LambdaHelpers.extract_user_id(event)        
        if not user_id:
            return {
                "statusCode": 401,
                "headers": CORS_headers,
                "body": '{"message": "User ID not found in request context"}',
            }
        
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            response["headers"] = CORS_headers
            return response
    
    source_id = LambdaHelpers.extract_path_parameter(event, "id")
    
    if not source_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": '{"message": "Source ID is required"}',
        }
    
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        source = await uow.sources.get(source_id)
    validated_source = ApiSource.from_domain(source)
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({validated_source.id: validated_source.name}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """

    Lambda function handler to retrieve a specific product by id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
