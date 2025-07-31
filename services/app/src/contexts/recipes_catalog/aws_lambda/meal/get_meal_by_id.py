import json
import os
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.iam_provider_api_for_recipes_catalog import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundException,
)
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
    Lambda function handler to retrieve a specific meal by id.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    # Validate user authentication using the new utility
    auth_result = await LambdaHelpers.validate_user_authentication(
        event, CORS_headers, IAMProvider, return_user_object=False
    )
    if isinstance(auth_result, dict):
        return auth_result  # Return error response
    _, user_id = auth_result  # Extract user_id (though we don't need it for this endpoint)
    
    meal_id = LambdaHelpers.extract_path_parameter(event, "id")
    
    if not meal_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": '{"message": "Meal ID is required"}',
        }
    
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Meal retrieval by ID
        logger.debug(f"Retrieving meal with ID: {meal_id}")
        try:
            meal = await uow.meals.get(meal_id)
        except EntityNotFoundException:
            logger.error(f"Meal not found: {meal_id}")
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps({"message": f"Meal {meal_id} not in database."}),
            }
    
    # Convert domain meal to API meal with validation error handling
    try:
        api = ApiMeal.from_domain(meal)
        logger.debug(f"Successfully converted meal {meal_id} to API format")
    except Exception as e:
        logger.error(f"Failed to convert meal {meal_id} to API format: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": '{"message": "Internal server error during meal conversion"}',
        }
    
    # Serialize API meal with validation error handling
    try:
        response_body = api.model_dump_json()
        logger.debug(f"Successfully serialized meal {meal_id}")
    except Exception as e:
        logger.error(f"Failed to serialize meal {meal_id} to JSON: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": '{"message": "Internal server error during response serialization"}',
        }
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to get a meal by its id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
