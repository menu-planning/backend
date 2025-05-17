import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.filter import \
    ApiRecipeFilter
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.recipe import \
    ApiRecipe
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.seedwork.shared.utils import custom_serializer
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()

@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for recipes.
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

    query_params: Any | dict[str, Any] = (
        event.get("multiValueQueryStringParameters") if event.get("multiValueQueryStringParameters") else {}
    )
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}
    filters["limit"] = int(query_params.get("limit", 50))
    filters["sort"] = query_params.get("sort", "-updated_at")
    
    for k, v in filters.items():
        if isinstance(v, list) and len(v) == 1:
            filters[k] = v[0]

    logger.debug(f"Filters: {filters}")
    api = ApiRecipeFilter(**filters).model_dump()
    logger.debug(f"ApiRecipeFilter: {api}")
    for k, _ in filters.items():
        filters[k] = api.get(k)
    
    if filters.get("tags"):
        filters["tags"] = [i+(current_user.id,) for i in filters["tags"]]
    if filters.get("tags_not_exists"):
        filters["tags_not_exists"] = [i+(current_user.id,) for i in filters["tags_not_exists"]]

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow: # type: ignore
        logger.debug(f"Querying recipes with filters {filters}")
        result = await uow.recipes.query(filter=filters)
    logger.debug(f"Found {len(result)} recipes")
    # logger.debug(f"ApiRecipe: {ApiRecipe.from_domain(result[0])}")
    # logger.debug(
    #     f"Recipe json: {json.dumps(ApiRecipe.from_domain(result[0]).model_dump(), default=custom_serializer)}"
    # )

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps(
            ([ApiRecipe.from_domain(i).model_dump() for i in result] if result else []),
            default=custom_serializer,
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for recipes.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
