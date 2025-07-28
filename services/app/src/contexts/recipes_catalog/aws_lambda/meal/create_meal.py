import json
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_meal import ApiCreateMeal
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
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
    Lambda function handler to create a meal.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
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
        api = ApiCreateMeal.model_validate_json(raw_body)
        logger.debug(f"Successfully parsed and validated request body")
    except Exception as e:
        logger.error(f"Failed to parse and validate request body: {str(e)}")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": f"Invalid meal data: {str(e)}"}),
        }
    
    # Business context: Permission validation for meal creation
    if not (
        current_user.has_permission(Permission.MANAGE_MEALS)
        or current_user.id == api.author_id
    ):
        logger.warning(f"User {current_user.id} does not have permission to create meal for author {api.author_id}")
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
    
    # Business context: Meal creation through message bus
    try:
        bus: MessageBus = container.bootstrap()
        await bus.handle(cmd)
        logger.debug(f"Meal created successfully with ID: {cmd.meal_id}")
    except Exception as e:
        logger.error(f"Failed to create meal: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during meal creation"}),
        }
    
    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({
            "message": "Meal created successfully",
            "meal_id": cmd.meal_id
        }),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create a meal.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
