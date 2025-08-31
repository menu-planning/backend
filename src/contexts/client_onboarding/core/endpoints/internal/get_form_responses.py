"""
Internal Provider Endpoint: Get Multiple Form Responses

Provides internal HTTP endpoint to expose form response data to other contexts.
Supports filtering by form_id and other criteria.
"""

import json
import time
from typing import Optional

from src.contexts.client_onboarding.core.adapters.external_providers.api_schemas.api_form_response import (
    ApiFormResponseList,
)
from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)
container = Container()


async def get_form_responses(
    caller_context: str,
    form_id: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict[str, int | str]:
    """
    Get multiple form responses with optional filtering.

    Args:
        caller_context: The context making the request (e.g., 'recipes_catalog')
        form_id: Optional form ID to filter responses
        limit: Optional limit for pagination
        offset: Optional offset for pagination

    Returns:
        Dict with statusCode and body containing list of form responses or error message
    """
    start_time = time.time()
    logger.info(
        f"Internal client_onboarding get_form_responses() called - Form ID: {form_id}, Caller context: {caller_context}"
    )

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork

    async with bus.uow as uow:
        try:
            logger.debug("Querying database for form responses", form_id=form_id, action="form_responses_query")

            if form_id:
                # Get responses for specific form
                form_responses = await uow.form_responses.get_by_form_id(form_id)
                logger.debug(
                    f"Retrieved {len(form_responses)} responses for form {form_id}"
                )
            else:
                # Get all form responses
                form_responses = await uow.form_responses.get_all()
                logger.debug("Form responses retrieved", response_count=len(form_responses), action="form_responses_retrieved")

            # Apply pagination if specified
            if offset:
                form_responses = form_responses[offset:]
            if limit:
                form_responses = form_responses[:limit]

            db_elapsed = time.time() - start_time
            logger.debug(
                f"Form responses retrieved from database in {db_elapsed:.3f}s - Count: {len(form_responses)}"
            )

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Database error after {elapsed_time:.3f}s for form responses query - Error: {type(e).__name__}: {e!s}"
            )
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Internal server error."}),
            }

        logger.debug("Processing form responses data", caller_context=caller_context, action="form_responses_processing")
        api_form_response_list = ApiFormResponseList.from_domain_list(
            form_responses=form_responses,
            caller_context=caller_context,
            offset=offset,
            limit=limit,
        )
        result_data = api_form_response_list.to_dict()

        elapsed_time = time.time() - start_time
        logger.info(
            f"Internal client_onboarding get_form_responses() completed successfully in {elapsed_time:.3f}s - Count: {len(form_responses)}, Context: {caller_context}"
        )

        return {
            "statusCode": 200,
            "body": json.dumps(result_data),
        }


# Note: _prepare_form_responses_data function removed - now using ApiFormResponseList.from_domain_list() directly
