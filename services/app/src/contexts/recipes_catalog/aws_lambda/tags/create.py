import json
import os
import uuid
from typing import Any, Type

import anyio
from src.contexts.recipes_catalog.aws_lambda import utils
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.category.create import (
    ApiCreateCategory,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.create import (
    ApiCreateTag,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.meal_planning.create import (
    ApiCreateMealPlanning,
)
from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.domain.enums import Permission, RecipeTagType
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    body = event.get("body", "")
    author_id = body.get("author_id", "")
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
        if author_id and not (
            current_user.has_permission(Permission.MANAGE_RECIPES)
            or current_user.id == author_id
        ):
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps(
                    {"message": "User does not have enough privilegies."}
                ),
            }
        else:
            body["author_id"] = current_user.id
    else:
        current_user = SeedUser(id="localstack-user")

    tag_config: dict[RecipeTagType, Type[ApiCreateTag]] = {
        RecipeTagType.CATEGORY: ApiCreateCategory,
        RecipeTagType.MEAL_PLANNING: ApiCreateMealPlanning,
    }
    tag_type = event.get("pathParameters", {}).get("tag_type")
    tag_data = event.get("body", {})

    if tag_type not in tag_config:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Invalid tag type provided."}),
        }

    api_class = tag_config[tag_type]
    tag_data = api_class(**tag_data)
    bus: MessageBus = Container().bootstrap()
    await utils.create_tag(
        tag_data,
        current_user,
        bus,
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create a tag.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_handler, event, context)
