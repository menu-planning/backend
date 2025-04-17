import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.client.filter import ApiClientFilter
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.client.client import \
    ApiClient
from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.seedwork.shared.utils import custom_serializer
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for clients.
    """
    logger.debug(f"Event received {event}")
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]

    query_params = (
        event.get("multiValueQueryStringParameters") if event.get("multiValueQueryStringParameters") else {}
    )
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}
    filters["limit"] = int(query_params.get("limit", 50))
    filters["sort"] = query_params.get("sort", "-date")
    
    for k, v in filters.items():
        if isinstance(v, list) and len(v) == 1:
            filters[k] = v[0]

    logger.debug(f"Filters: {filters}")
    api = ApiClientFilter(**filters).model_dump()
    logger.debug(f"ApiClientFilter: {api}")
    for k, _ in filters.items():
        filters[k] = api.get(k)

    if filters.get("tags"):
        filters["tags"] = [i+(current_user.id,) for i in filters["tags"]]
    if filters.get("tags_not_exists"):
        filters["tags_not_exists"] = [i+(current_user.id,) for i in filters["tags_not_exists"]]

    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        logger.debug(f"Querying clients with filters {filters}")
        result = await uow.clients.query(filter=filters)
    logger.debug(f"Found {len(result)} clients")
    logger.debug(f"Result: {[ApiClient.from_domain(i) for i in result] if result else []}")

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps(
            ([ApiClient.from_domain(i).model_dump() for i in result] if result else []),
            default=custom_serializer,
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for clients.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_handler, event, context)