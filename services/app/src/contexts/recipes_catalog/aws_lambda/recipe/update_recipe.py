import json
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.external_providers.iam.iam_provider_api_for_recipes_catalog import \
    IAMProvider
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_recipe import ApiUpdateRecipe
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import \
    EntityNotFoundException
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to update a recipe by its id.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    # Validate user authentication and get user object for permission checking
    auth_result = await LambdaHelpers.validate_user_authentication(
        event, CORS_headers, IAMProvider, return_user_object=True
    )
    if isinstance(auth_result, dict):
        return auth_result  # Return error response
    user_id, current_user = auth_result
    
    # Extract recipe ID from path parameters
    recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
    if not recipe_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Recipe ID is required in path parameters"}),
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
    
    # Parse and validate request body as a complete recipe using ApiRecipe
    try:
        # Parse raw_body as complete recipe
        api_recipe_from_request = ApiRecipe.model_validate_json(raw_body)
        logger.debug(f"Successfully parsed raw_body as complete ApiRecipe")
    except Exception as e:
        logger.error(f"Failed to parse raw_body as complete recipe: {str(e)}")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": f"Invalid recipe data: {str(e)}"}),
        }

    # Business context: Check if recipe exists and validate permissions
    try:
        bus: MessageBus = container.bootstrap()
        uow: UnitOfWork
        async with bus.uow as uow:
            try:
                existing_recipe = await uow.recipes.get(recipe_id)
                logger.debug(f"Recipe {recipe_id} found in database")
            except EntityNotFoundException:
                logger.warning(f"Recipe {recipe_id} not found in database")
                return {
                    "statusCode": 404,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": f"Recipe {recipe_id} not found."}),
                }
            
            # Business context: Permission validation for recipe update
            if not (
                current_user.has_permission(Permission.MANAGE_RECIPES)
                or current_user.id == existing_recipe.author_id
            ):
                logger.warning(f"User {current_user.id} does not have permission to update recipe {recipe_id}")
                return {
                    "statusCode": 403,
                    "headers": CORS_headers,
                    "body": json.dumps(
                        {"message": "User does not have enough privileges to update this recipe."}
                    ),
                }

            # Convert existing domain recipe to ApiRecipe for comparison
            try:
                existing_api_recipe = ApiRecipe.from_domain(existing_recipe)
                logger.debug(f"Successfully converted existing domain recipe to ApiRecipe")
            except Exception as e:
                logger.error(f"Failed to convert existing domain recipe to ApiRecipe: {str(e)}")
                return {
                    "statusCode": 500,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": "Internal server error during recipe conversion"}),
                }

            # Create ApiUpdateRecipe using from_api_recipe with new recipe and old recipe for comparison
            try:
                api_of_update_cmd = ApiUpdateRecipe.from_api_recipe(
                    api_recipe=api_recipe_from_request,
                    old_api_recipe=existing_api_recipe
                )
                logger.debug(f"Successfully created ApiUpdateRecipe with only changed fields")
            except Exception as e:
                logger.error(f"Failed to create ApiUpdateRecipe from api recipes: {str(e)}")
                return {
                    "statusCode": 500,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": "Internal server error during update command creation"}),
                }

    except Exception as e:
        logger.error(f"Failed to validate recipe existence and permissions: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during recipe validation"}),
        }
      
    logger.debug(f"Final processed API model: {api_of_update_cmd}")
    
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
    
    # Business context: Recipe update through message bus
    try:
        await bus.handle(cmd)
        logger.debug(f"Recipe {recipe_id} updated successfully")
    except Exception as e:
        logger.error(f"Failed to update recipe: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during recipe update"}),
        }
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Recipe updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to update a recipe by its id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
