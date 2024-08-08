import uuid
from typing import Any

import anyio
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.aws_lambda.decorators.with_user_id import with_user_id
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

from .internal_providers.iam.api import IAMProvider

container = Container()


@lambda_exception_handler
@with_user_id
async def async_get_by_id(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to retrieve a specific product by id.
    """
    user_id = event["user_id"]
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    path_parameters = event.get("pathParameters", {})
    product_id = path_parameters.get("id")
    bus: MessageBus = container.bootstrap()

    uow: UnitOfWork
    async with bus.uow as uow:
        product = await uow.products.get(product_id)
    api = ApiProduct.from_domain(product)
    return {
        "statusCode": 200,
        "body": api.model_dump_json(),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """

    Lambda function handler to retrieve a specific product by id.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_get_by_id, event, context)
