import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.client.commands.delete_menu import DeleteMenu
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()

@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to delete a menu.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event)}")
    
    # Extract client ID and menu ID from path parameters
    client_id = event.get("pathParameters", {}).get("client_id")
    menu_id = event.get("pathParameters", {}).get("menu_id")
    
    if not client_id:
        logger.error("Client ID not provided in path parameters")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Client ID is required"}),
        }
    
    if not menu_id:
        logger.error("Menu ID not provided in path parameters")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Menu ID is required"}),
        }

    # Business context: Get client to verify existence
    try:
        bus: MessageBus = container.bootstrap()
        uow: UnitOfWork
        async with bus.uow as uow:
            client = await uow.clients.get(client_id)
            logger.debug(f"Client found: {client_id}")
    except EntityNotFoundException:
        logger.warning(f"Client {client_id} not found in database")
        return {
            "statusCode": 403,
            "headers": CORS_headers,
            "body": json.dumps({"message": f"Client {client_id} not in database."}),
        }
    except Exception as e:
        logger.error(f"Unexpected error retrieving client {client_id}: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during client retrieval"}),
        }

    # Validate user authentication and get user object for permission checking
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        auth_result = await LambdaHelpers.validate_user_authentication(
            event, CORS_headers, IAMProvider, return_user_object=True
        )
        if isinstance(auth_result, dict):
            return auth_result  # Return error response
        _, current_user = auth_result
        
        # Business context: Permission validation for menu deletion
        if not (
            current_user.has_permission(Permission.MANAGE_MENUS)
            or client.author_id == current_user.id
        ):
            logger.warning(f"User {current_user.id} does not have permission to delete menu {menu_id} (client author: {client.author_id})")
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps(
                    {"message": "User does not have enough privileges."}
                ),
            }

    # Business context: Menu deletion through message bus
    try:
        cmd = DeleteMenu(menu_id=menu_id)
        await bus.handle(cmd)
        logger.debug(f"Menu deleted successfully: {menu_id}")
    except Exception as e:
        logger.error(f"Failed to delete menu {menu_id}: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during menu deletion"}),
        }

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Menu deleted successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to delete a menu.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
