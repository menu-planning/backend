"""
Internal Provider Endpoint: Get Single Form Response

Provides internal HTTP endpoint to expose form response data to other contexts.
Similar to IAM internal endpoints pattern.
"""

import json
import time
from typing import Any

from src.contexts.client_onboarding.core.adapters.external_providers.api_schemas.api_form_response import ApiFormResponse
from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

container = Container()


async def get_form_response(response_id: str, caller_context: str) -> dict[str, int | str]:
    """
    Get a single form response by TypeForm response ID.
    
    Args:
        response_id: TypeForm response ID
        caller_context: The context making the request (e.g., 'recipes_catalog')
    
    Returns:
        Dict with statusCode and body containing form response data or error message
    """
    start_time = time.time()
    logger.info(f"Internal client_onboarding get_form_response() called - Response: {response_id}, Caller context: {caller_context}")
    
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    
    async with bus.uow as uow:
        try:
            logger.debug(f"Querying database for form response: {response_id}")
            form_response = await uow.form_responses.get_by_response_id(response_id)
            
            if not form_response:
                elapsed_time = time.time() - start_time
                logger.error(f"Form response not found in database after {elapsed_time:.3f}s - Response: {response_id}")
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "Form response not found."}),
                }
                
            db_elapsed = time.time() - start_time
            logger.debug(f"Form response retrieved from database in {db_elapsed:.3f}s - Response: {response_id}")
            
        except EntityNotFoundException:
            elapsed_time = time.time() - start_time
            logger.error(f"Form response not found in database after {elapsed_time:.3f}s - Response: {response_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Form response not found."}),
            }
        except MultipleEntitiesFoundException:
            elapsed_time = time.time() - start_time
            logger.error(f"Multiple form responses found in database after {elapsed_time:.3f}s - Response: {response_id}")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Multiple form responses found."}),
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Database error after {elapsed_time:.3f}s for response {response_id} - Error: {type(e).__name__}: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Internal server error."}),
            }
        
        logger.debug(f"Processing form response data for context: {caller_context}")
        api_form_response = ApiFormResponse.from_domain(form_response)
        result_data = api_form_response.to_dict()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Internal client_onboarding get_form_response() completed successfully in {elapsed_time:.3f}s - Response: {response_id}, Context: {caller_context}")
        
        return {
            "statusCode": 200,
            "body": json.dumps(result_data),
        }


# Note: _prepare_form_response_data function removed - now using ApiFormResponse.from_domain() directly