import json
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.external_providers.iam.iam_provider_api_for_recipes_catalog import IAMProvider
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_meal import ApiUpdateMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
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
    Lambda function handler to update a meal by its id.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    # Validate user authentication and get user object for permission checking
    auth_result = await LambdaHelpers.validate_user_authentication(
        event, CORS_headers, IAMProvider, return_user_object=True
    )
    if isinstance(auth_result, dict):
        return auth_result  # Return error response
    user_id, current_user = auth_result
    
    # Extract meal ID from path parameters
    meal_id = event.get("pathParameters", {}).get("id")
    if not meal_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Meal ID is required in path parameters"}),
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
    
    # Parse and validate request body as a complete meal using ApiMeal
    try:
        # Parse raw_body as complete meal
        api_meal_from_request = ApiMeal.model_validate_json(raw_body)
        logger.debug(f"Successfully parsed raw_body as complete ApiMeal")
    except Exception as e:
        logger.error(f"Failed to parse raw_body as complete meal: {str(e)}")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": f"Invalid meal data: {str(e)}"}),
        }

    # Business context: Check if meal exists and validate permissions
    try:
        bus: MessageBus = container.bootstrap()
        uow: UnitOfWork
        async with bus.uow as uow:
            try:
                existing_meal = await uow.meals.get(meal_id)
                logger.debug(f"Meal {meal_id} found in database")
            except EntityNotFoundException:
                logger.warning(f"Meal {meal_id} not found in database")
                return {
                    "statusCode": 404,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": f"Meal {meal_id} not found."}),
                }
            
            # Business context: Permission validation for meal update
            if not (
                current_user.has_permission(Permission.MANAGE_MEALS)
                or current_user.id == existing_meal.author_id
            ):
                logger.warning(f"User {current_user.id} does not have permission to update meal {meal_id}")
                return {
                    "statusCode": 403,
                    "headers": CORS_headers,
                    "body": json.dumps(
                        {"message": "User does not have enough privileges to update this meal."}
                    ),
                }

            # Convert existing domain meal to ApiMeal for comparison
            try:
                existing_api_meal = ApiMeal.from_domain(existing_meal)
                logger.debug(f"Successfully converted existing domain meal to ApiMeal")
            except Exception as e:
                logger.error(f"Failed to convert existing domain meal to ApiMeal: {str(e)}")
                return {
                    "statusCode": 500,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": "Internal server error during meal conversion"}),
                }

            # Create ApiUpdateMeal using from_api_meal with new meal and old meal for comparison
            try:
                api_of_update_cmd = ApiUpdateMeal.from_api_meal(
                    api_meal=api_meal_from_request,
                    old_api_meal=existing_api_meal
                )
                logger.debug(f"Successfully created ApiUpdateMeal with only changed fields")
            except Exception as e:
                logger.error(f"Failed to create ApiUpdateMeal from api meals: {str(e)}")
                return {
                    "statusCode": 500,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": "Internal server error during update command creation"}),
                }

    except Exception as e:
        logger.error(f"Failed to validate meal existence and permissions: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during meal validation"}),
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
    
    # Business context: Meal update through message bus
    try:
        await bus.handle(cmd)
        logger.debug(f"Meal {meal_id} updated successfully")
    except Exception as e:
        logger.error(f"Failed to update meal: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during meal update"}),
        }
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Meal updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to update a meal by its id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
