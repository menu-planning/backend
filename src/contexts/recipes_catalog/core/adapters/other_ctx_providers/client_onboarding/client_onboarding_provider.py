"""
Client Onboarding Provider

HTTP client for accessing client_onboarding internal endpoints from recipes_catalog context.
Follows the same pattern as ProductsCatalogProvider and IAM providers.
"""

import json
from typing import Any

from src.contexts.client_onboarding.core.internal_endpoints.multiple_form_response import (
    get_form_responses,
)
from src.contexts.client_onboarding.core.internal_endpoints.single_form_response import (
    get_form_response,
)
from src.contexts.recipes_catalog.core.adapters.other_ctx_providers.client_onboarding.schemas import (
    ClientOnboardingFormResponse,
    ClientOnboardingFormResponseList,
)


class ClientOnboardingProvider:
    """
    Internal provider for accessing client_onboarding context data.

    Provides methods to retrieve form response data for client creation workflows.
    """

    @staticmethod
    async def get_form_response(response_id: str) -> dict[str, Any]:
        """
        Get a single form response by TypeForm response ID.

        Args:
            response_id: TypeForm response ID

        Returns:
            Dictionary containing form response data

        Raises:
            Exception: If form response not found or API error occurs
        """
        response = await get_form_response(
            response_id=response_id,
            caller_context="recipes_catalog"
        )

        if response.get("statusCode") != 200:
            error_body_str = response.get("body", "{}")
            error_body = json.loads(error_body_str) if isinstance(error_body_str, str) else {}
            error_message = error_body.get("message", "Unknown error")
            raise Exception(f"Failed to get form response {response_id}: {error_message}")

        response_body = response.get("body", "{}")
        if isinstance(response_body, str):
            form_response_data = json.loads(response_body)
        else:
            form_response_data = response_body

        if not isinstance(form_response_data, dict):
            raise Exception(f"Invalid response format for form response {response_id}")

        return ClientOnboardingFormResponse(**form_response_data).model_dump()

    @staticmethod
    async def get_form_responses(
        form_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get multiple form responses with optional filtering.

        Args:
            form_id: Optional form ID to filter responses
            limit: Optional limit for pagination
            offset: Optional offset for pagination

        Returns:
            List of form response dictionaries

        Raises:
            Exception: If API error occurs
        """
        response = await get_form_responses(
            caller_context="recipes_catalog",
            form_id=form_id,
            limit=limit,
            offset=offset
        )

        if response.get("statusCode") != 200:
            error_body_str = response.get("body", "{}")
            error_body = json.loads(error_body_str) if isinstance(error_body_str, str) else {}
            error_message = error_body.get("message", "Unknown error")
            raise Exception(f"Failed to get form responses: {error_message}")

        response_body = response.get("body", "{}")
        if isinstance(response_body, str):
            responses_data = json.loads(response_body)
        else:
            responses_data = response_body

        if not isinstance(responses_data, dict):
            raise Exception("Invalid response format for form responses")

        response_list = ClientOnboardingFormResponseList(**responses_data)

        return [response.model_dump() for response in response_list.responses]

    @staticmethod
    async def get_form_responses_for_client_creation() -> list[dict[str, Any]]:
        """
        Get form responses that are suitable for client creation.

        This method filters responses to find those with adequate client identification
        data for creating recipes_catalog Client entities.

        Returns:
            List of form response dictionaries with client identifier data
        """
        all_responses = await ClientOnboardingProvider.get_form_responses()

        # Filter responses that have client identifiers suitable for client creation
        suitable_responses = []
        for response in all_responses:
            client_identifiers = response.get("client_identifiers")
            if client_identifiers and _has_sufficient_client_data(client_identifiers):
                suitable_responses.append(response)

        return suitable_responses

    @staticmethod
    async def get_client_data_from_response(response_id: str) -> dict[str, Any]:
        """
        Extract client data from a form response for client creation.

        Args:
            response_id: TypeForm response ID

        Returns:
            Dictionary with extracted client data ready for Client entity creation

        Raises:
            Exception: If form response not found or insufficient data
        """
        form_response = await ClientOnboardingProvider.get_form_response(response_id)

        client_identifiers = form_response.get("client_identifiers", {})
        response_data = form_response.get("response_data", {})

        if not _has_sufficient_client_data(client_identifiers):
            raise Exception(f"Form response {response_id} lacks sufficient client identification data")

        # Extract and format client data
        client_data = {
            "email": client_identifiers.get("email"),
            "phone": client_identifiers.get("phone"),
            "first_name": client_identifiers.get("first_name"),
            "last_name": client_identifiers.get("last_name"),
            "company": client_identifiers.get("company"),
            "form_response_data": {
                "response_id": form_response.get("response_id"),
                "submission_id": form_response.get("submission_id"),
                "submitted_at": form_response.get("submitted_at"),
                "raw_data": response_data,
                "client_identifiers": client_identifiers,
            }
        }

        return client_data


def _has_sufficient_client_data(client_identifiers: dict[str, Any]) -> bool:
    """
    Check if client identifiers contain sufficient data for client creation.

    Args:
        client_identifiers: Dictionary of client identification data

    Returns:
        True if sufficient data is available, False otherwise
    """
    if not client_identifiers:
        return False

    # At minimum, we need email or phone for client creation
    has_email = client_identifiers.get("email")
    has_phone = client_identifiers.get("phone")

    return bool(has_email or has_phone)
