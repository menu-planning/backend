import json
import os
import urllib.parse
import uuid
from typing import Any

import anyio
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.products_catalog.shared.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.seedwork.shared.utils import custom_serializer
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers

container = Container()


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to retrieve a specific product by id.
    """
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
    path_parameters: Any  = event.get("pathParameters") if event.get("pathParameters") else {}
    name = path_parameters.get("name")
    if not name:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": "Name parameter is required.",
        }
    name = urllib.parse.unquote(name)
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow: # type: ignore
        result = await uow.products.list_top_similar_names(name)
    logger.debug(f"Found {len(result)} products similar to {name}")
    logger.debug(f"Result: {result[0] if result else []}")
    logger.debug(f"Result1: {ApiProduct.from_domain(result[0]) if result else []}")
    logger.debug(
        f"Result2: {json.dumps(ApiProduct.from_domain(result[0]).model_dump() if result else [],default=custom_serializer)}"
    )
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
