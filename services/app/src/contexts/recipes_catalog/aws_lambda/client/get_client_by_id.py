import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.client.client import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to retrieve a specific client by id.
    """
    logger.debug(f"Getting client by id: {event}")
    client_id = event.get("pathParameters", {}).get("client_id")

    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow: # type: ignore
        try:
            client = await uow.clients.get(client_id)
        except EntityNotFoundException:
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps({"message": f"Client {client_id} not in database."}),
            }

    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
        if not (
            current_user.has_permission(Permission.MANAGE_MENUS)
            or client.author_id == current_user.id
        ):
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps(
                    {"message": "User does not have enough privilegies."}
                ),
            }

    api = ApiClient.from_domain(client)
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": api.model_dump_json(),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to get a client by its id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
