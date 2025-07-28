import json
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_create_menu import ApiCreateMenu
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
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
    Lambda function handler to create a menu.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    # Extract client_id from path parameters
    client_id = event.get("pathParameters", {}).get("client_id")
    if not client_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Client ID is required in path parameters"}),
        }
    
    # Validate user authentication and get user object for permission checking
    auth_result = await LambdaHelpers.validate_user_authentication(
        event, CORS_headers, IAMProvider, return_user_object=True
    )
    if isinstance(auth_result, dict):
        return auth_result  # Return error response
    _, current_user = auth_result
    
    # Extract and parse request body with validation error handling
    try:
        raw_body = LambdaHelpers.extract_request_body(event, parse_json=False)
        logger.debug(f"Raw request body extracted successfully")
    except Exception as e:
        logger.error(f"Unexpected error extracting request body: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during request parsing"}),
        }
    
    # Ensure body is a string and not empty
    if not isinstance(raw_body, str) or not raw_body.strip():
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Request body is required"}),
        }
    
    # Parse and validate request body using Pydantic model
    try:
        api = ApiCreateMenu.model_validate_json(raw_body)
        logger.debug(f"Successfully parsed and validated request body")
    except Exception as e:
        logger.error(f"Failed to parse and validate request body: {str(e)}")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": f"Invalid menu data: {str(e)}"}),
        }
    
    # Business context: Client validation
    try:
        bus: MessageBus = container.bootstrap()
        uow: UnitOfWork
        async with bus.uow as uow:
            try:
                client = await uow.clients.get(client_id)
                logger.debug(f"Client {client_id} found in database")
            except EntityNotFoundException:
                logger.warning(f"Client {client_id} not found in database")
                return {
                    "statusCode": 403,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": f"Client {client_id} not in database."}),
                }
    except Exception as e:
        logger.error(f"Failed to validate client: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during client validation"}),
        }
    
    # Business context: Permission validation for menu creation
    if not (
        current_user.has_permission(Permission.MANAGE_MENUS)
        or current_user.id == client.author_id
    ):
        logger.warning(f"User {current_user.id} does not have permission to create menu for client {client_id}")
        return {
            "statusCode": 403,
            "headers": CORS_headers,
            "body": json.dumps(
                {"message": "User does not have enough privileges."}
            ),
        }
    
    # Convert to domain command with validation error handling
    try:
        cmd = api.to_domain()
        logger.debug(f"Successfully converted to domain command")
    except Exception as e:
        logger.error(f"Failed to convert API to domain command: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during command creation"}),
        }
    
    # Business context: Menu creation through message bus
    try:
        await bus.handle(cmd)
        logger.debug(f"Menu created successfully with ID: {cmd.menu_id}")
    except Exception as e:
        logger.error(f"Failed to create menu: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during menu creation"}),
        }
    
    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({
            "message": "Menu created successfully",
            "menu_id": cmd.menu_id
        }),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create a menu.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
