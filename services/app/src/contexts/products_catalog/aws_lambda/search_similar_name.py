import json
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
async def async_search_similar_name(
    event: dict[str, Any], context: Any
) -> dict[str, Any]:
    """
    Lambda function handler to retrieve a specific product by id.
    """
    user_id = event["user_id"]
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    query_params = event.get("queryStringParameters", {})
    name = query_params.get("name")
    if not name:
        return {"statusCode": 400, "body": "Name parameter is required."}
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        names = await uow.products.list_top_similar_names(name)
    return {
        "statusCode": 200,
        "body": json.dumps(names),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_search_similar_name, event, context)
