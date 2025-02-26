import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tag.delete import \
    ApiDeleteTag
from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.domain.enums import \
    Permission as EnumPermission
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """ "
    Lambda function handler to delete a tag.
    """
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
    else:
        current_user = SeedUser(id="localstack-user")

    tag_id = event.get("pathParameters", {}).get("id")
    
    uow: UnitOfWork
    bus: MessageBus = Container().bootstrap()
    async with bus.uow as uow:
        tag: Tag = await uow.tags.get(tag_id)

    if not (
        current_user.has_permission(EnumPermission.MANAGE_RECIPES)
        or tag.author_id == current_user.id
    ):
        return {
            "statusCode": 403,
            "headers": CORS_headers,
            "body": json.dumps({"message": "User does not have enough privilegies."}),
        }

    cmd = ApiDeleteTag(id=tag_id)
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to delete a tag.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_handler, event, context)
    return anyio.run(async_handler, event, context)
    return anyio.run(async_handler, event, context)
    return anyio.run(async_handler, event, context)
