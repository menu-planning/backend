import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import \
    Permission as EnumPermission
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import \
    EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import \
    ApiTag
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to get a tag by id.
    """
    logger.debug(f"Event received {event}")
    authorizer_context = event["requestContext"]["authorizer"]
    user_id = authorizer_context.get("claims").get("sub")
    logger.debug(f"Fetching diet_types for user {user_id}")
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    current_user: SeedUser = response["body"]

    tag_id = event.get("pathParameters", {}).get("id")

    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            tag: Tag = await uow.tags.get(tag_id)
        except EntityNotFoundException:
            return {
                "statusCode": 404,
                "headers": CORS_headers,
                "body": json.dumps({"message": f"Tag {id} not in database."}),
            }
    if not (
        current_user.has_permission(EnumPermission.MANAGE_RECIPES)
        or tag.author_id == current_user.id
    ):
        return {
            "statusCode": 403,
            "headers": CORS_headers,
            "body": json.dumps({"message": "User does not have enough privilegies."}),
        }
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": ApiTag.from_domain(tag).model_dump_json(),
    }

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to get a diet type by its id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)