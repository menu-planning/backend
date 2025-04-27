import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.meal.filter import \
    ApiMealFilter
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.meal.meal import \
    ApiMeal
from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.seedwork.shared.utils import custom_serializer
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for meals.
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
    api = ApiMealFilter(**filters).model_dump()
    logger.debug(f"ApiMealFilter: {api}")
    for k, _ in filters.items():
        filters[k] = api.get(k)

    if filters.get("tags"):
        filters["tags"] = [i+(current_user.id,) for i in filters["tags"]]
    if filters.get("tags_not_exists"):
        filters["tags_not_exists"] = [i+(current_user.id,) for i in filters["tags_not_exists"]]

    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow: # type: ignore
        logger.debug(f"Querying meals with filters {filters}")
        result = await uow.meals.query(filter=filters)
    logger.debug(f"Found {len(result)} meals")
    logger.debug(f"Result: {[ApiMeal.from_domain(i) for i in result] if result else []}")

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps(
            ([ApiMeal.from_domain(i).model_dump() for i in result] if result else []),
            default=custom_serializer,
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for meals.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)