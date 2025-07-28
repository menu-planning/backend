import json
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_update_menu import ApiUpdateMenu
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import ApiMenu
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException
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
    Lambda function handler to update a menu by its id.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    # Validate user authentication and get user object for permission checking
    auth_result = await LambdaHelpers.validate_user_authentication(
        event, CORS_headers, IAMProvider, return_user_object=True
    )
    if isinstance(auth_result, dict):
        return auth_result  # Return error response
    user_id, current_user = auth_result
    
    # Extract client ID and menu ID from path parameters
    client_id = event.get("pathParameters", {}).get("client_id")
    menu_id = event.get("pathParameters", {}).get("menu_id")
    
    if not client_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Client ID is required in path parameters"}),
        }
    
    if not menu_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Menu ID is required in path parameters"}),
        }
    
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
    
    # Parse and validate request body as a complete menu using ApiMenu
    try:
        # Parse raw_body as complete menu
        api_menu_from_request = ApiMenu.model_validate_json(raw_body)
        logger.debug(f"Successfully parsed raw_body as complete ApiMenu")
        
        # Validate that menu_id and client_id in path match those in body
        if menu_id != api_menu_from_request.id:
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": json.dumps({"message": "Menu ID in path and body must be the same"}),
            }
        
        if client_id != api_menu_from_request.client_id:
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": json.dumps({"message": "Client ID in path and body must be the same"}),
            }
            
    except Exception as e:
        logger.error(f"Failed to parse raw_body as complete menu: {str(e)}")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": f"Invalid menu data: {str(e)}"}),
        }

    # Business context: Check if client exists and validate permissions
    try:
        bus: MessageBus = container.bootstrap()
        uow: UnitOfWork
        async with bus.uow as uow:
            try:
                client_on_db = await uow.clients.get(client_id)
                logger.debug(f"Client {client_id} found in database")
            except EntityNotFoundException:
                logger.warning(f"Client {client_id} not found in database")
                return {
                    "statusCode": 404,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": f"Client {client_id} not found."}),
                }
            
            # Business context: Permission validation for menu update
            if not (
                current_user.has_permission(Permission.MANAGE_MENUS)
                or client_on_db.author_id == current_user.id
            ):
                logger.warning(f"User {current_user.id} does not have permission to update menu {menu_id} for client {client_id}")
                return {
                    "statusCode": 403,
                    "headers": CORS_headers,
                    "body": json.dumps(
                        {"message": "User does not have enough privileges to update this menu."}
                    ),
                }

            # Check if menu exists and get existing menu for comparison
            try:
                existing_menu = await uow.menus.get(menu_id)
                logger.debug(f"Menu {menu_id} found in database")
            except EntityNotFoundException:
                logger.warning(f"Menu {menu_id} not found in database")
                return {
                    "statusCode": 404,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": f"Menu {menu_id} not found."}),
                }

            # Convert existing domain menu to ApiMenu for comparison
            try:
                existing_api_menu = ApiMenu.from_domain(existing_menu)
                logger.debug(f"Successfully converted existing domain menu to ApiMenu")
            except Exception as e:
                logger.error(f"Failed to convert existing domain menu to ApiMenu: {str(e)}")
                return {
                    "statusCode": 500,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": "Internal server error during menu conversion"}),
                }

            # Create ApiUpdateMenu using from_api_menu with new menu and old menu for comparison
            try:
                api_of_update_cmd = ApiUpdateMenu.from_api_menu(
                    api_menu=api_menu_from_request,
                    old_api_menu=existing_api_menu
                )
                logger.debug(f"Successfully created ApiUpdateMenu with only changed fields")
            except Exception as e:
                logger.error(f"Failed to create ApiUpdateMenu from api menus: {str(e)}")
                return {
                    "statusCode": 500,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": "Internal server error during update command creation"}),
                }

    except Exception as e:
        logger.error(f"Failed to validate client/menu existence and permissions: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during validation"}),
        }
        
    # Convert to domain command with validation error handling
    try:
        cmd = api_of_update_cmd.to_domain()
        logger.debug(f"Successfully converted to domain command")
    except Exception as e:
        logger.error(f"Failed to convert API to domain command: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during command creation"}),
        }
    
    # Business context: Menu update through message bus
    try:
        await bus.handle(cmd)
        logger.debug(f"Menu {menu_id} updated successfully")
    except Exception as e:
        logger.error(f"Failed to update menu: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during menu update"}),
        }
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Menu updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to update a menu by its id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
