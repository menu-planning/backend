import os
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
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers

container = Container()


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to retrieve a specific product by id.
    """
    logger.debug(f"Getting product by id: {event}")
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        logger.debug(f"User id: {user_id}")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
    path_parameters: Any  = event.get("pathParameters") if event.get("pathParameters") else {}
    logger.debug(f"Path params: {path_parameters}")
    product_id = path_parameters.get("id")
    bus: MessageBus = container.bootstrap()

    uow: UnitOfWork
    async with bus.uow as uow: # type: ignore
        product = await uow.products.get(product_id)
    api = ApiProduct.from_domain(product)
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
