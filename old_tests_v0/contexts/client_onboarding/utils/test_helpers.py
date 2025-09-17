"""
Test utilities for Client Onboarding equality testing, validation, and webhooks.

This module provides context-specific utilities that complement tests/utils/utils.py:
- Command and event comparison utilities
- TypeForm response validation helpers
- Webhook payload validation and testing helpers
- Client data validation utilities
- Integration with existing counter_manager patterns
"""

import hashlib
import hmac
from datetime import datetime
from typing import Any, Union
from uuid import UUID

from src.contexts.client_onboarding.core.domain.commands.setup_onboarding_form import (
    SetupOnboardingFormCommand,
)
from src.contexts.client_onboarding.core.domain.commands.update_webhook_url import (
    UpdateWebhookUrlCommand,
)


def assert_commands_equal(
    command1: SetupOnboardingFormCommand | UpdateWebhookUrlCommand,
    command2: SetupOnboardingFormCommand | UpdateWebhookUrlCommand,
    message: str | None = None,
) -> None:
    """
    Assert that two client onboarding commands are equal with detailed error reporting.

    Args:
        command1: First command to compare
        command2: Second command to compare
        message: Optional custom error message

    Raises:
        AssertionError: If commands are not equal
    """
    if type(command1) is not type(command2):
        error_msg = f"Commands are different types: {type(command1).__name__} vs {type(command2).__name__}"
        if message:
            error_msg = f"{message}\n{error_msg}"
        raise AssertionError(error_msg)

    differences = find_command_differences(command1, command2)
    if differences:
        error_msg = "Commands are not equal. Differences found:\n"
        for diff in differences:
            error_msg += f"  - {diff}\n"

        if message:
            error_msg = f"{message}\n{error_msg}"

        raise AssertionError(error_msg)


def find_command_differences(
    command1: SetupOnboardingFormCommand | UpdateWebhookUrlCommand,
    command2: SetupOnboardingFormCommand | UpdateWebhookUrlCommand,
) -> list[str]:
    """
    Find differences between two commands.

    Returns:
        List of difference descriptions
    """
    differences = []

    if isinstance(command1, SetupOnboardingFormCommand) and isinstance(
        command2, SetupOnboardingFormCommand
    ):
        if command1.user_id != command2.user_id:
            differences.append(f"user_id: {command1.user_id} != {command2.user_id}")
        if command1.typeform_id != command2.typeform_id:
            differences.append(
                f"typeform_id: {command1.typeform_id} != {command2.typeform_id}"
            )
        if command1.webhook_url != command2.webhook_url:
            differences.append(
                f"webhook_url: {command1.webhook_url} != {command2.webhook_url}"
            )

    elif isinstance(command1, UpdateWebhookUrlCommand) and isinstance(
        command2, UpdateWebhookUrlCommand
    ):
        if command1.form_id != command2.form_id:
            differences.append(f"form_id: {command1.form_id} != {command2.form_id}")
        if command1.new_webhook_url != command2.new_webhook_url:
            differences.append(
                f"new_webhook_url: {command1.new_webhook_url} != {command2.new_webhook_url}"
            )

    return differences


def validate_webhook_payload(payload: dict[str, Any]) -> bool:
    """
    Validate that a webhook payload has the expected TypeForm structure.

    Args:
        payload: The webhook payload to validate

    Returns:
        True if payload is valid, False otherwise
    """
    required_fields = ["event_id", "event_type", "form_response"]

    # Check top-level required fields
    for field in required_fields:
        if field not in payload:
            return False

    # Check form_response structure
    form_response = payload.get("form_response", {})
    response_required_fields = ["form_id", "token"]

    for field in response_required_fields:
        if field not in form_response:
            return False

    # Check answers structure if present
    if "answers" in form_response:
        answers = form_response["answers"]
        if not isinstance(answers, list):
            return False

        for answer in answers:
            if not isinstance(answer, dict):
                return False
            if "field" not in answer or "type" not in answer:
                return False

    return True


def create_webhook_signature(payload: str, secret: str) -> str:
    """
    Create a TypeForm webhook signature for testing.

    Args:
        payload: The webhook payload as a string
        secret: The webhook secret

    Returns:
        The signature string that should be in the header
    """
    signature = hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


def validate_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Validate a TypeForm webhook signature.

    Args:
        payload: The webhook payload as a string
        signature: The signature from the header
        secret: The webhook secret

    Returns:
        True if signature is valid, False otherwise
    """
    expected_signature = create_webhook_signature(payload, secret)
    return hmac.compare_digest(signature, expected_signature)


def extract_client_info_from_webhook(payload: dict[str, Any]) -> dict[str, Any] | None:
    """
    Extract client information from a TypeForm webhook payload.

    Args:
        payload: The webhook payload

    Returns:
        Dictionary containing extracted client info, or None if extraction fails
    """
    if not validate_webhook_payload(payload):
        return None

    form_response = payload.get("form_response", {})
    answers = form_response.get("answers", [])

    client_info = {
        "form_id": form_response.get("form_id"),
        "response_token": form_response.get("token"),
        "submission_time": form_response.get("submitted_at"),
        "extracted_data": {},
    }

    # Extract data from answers
    for answer in answers:
        field = answer.get("field", {})
        field_id = field.get("id", "")
        field_type = answer.get("type", "")

        # Extract value based on answer type
        if field_type == "text" and "text" in answer:
            client_info["extracted_data"][field_id] = answer["text"]
        elif field_type == "email" and "email" in answer:
            client_info["extracted_data"][field_id] = answer["email"]
        elif field_type == "choice" and "choice" in answer:
            client_info["extracted_data"][field_id] = answer["choice"].get("label")
        elif field_type == "number" and "number" in answer:
            client_info["extracted_data"][field_id] = answer["number"]

    return client_info


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Check if a string is a valid UUID.

    Args:
        uuid_string: The string to validate

    Returns:
        True if valid UUID, False otherwise
    """
    try:
        UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_timestamp(timestamp_string: str) -> bool:
    """
    Check if a string is a valid ISO timestamp.

    Args:
        timestamp_string: The timestamp string to validate

    Returns:
        True if valid timestamp, False otherwise
    """
    try:
        datetime.fromisoformat(timestamp_string.replace("Z", "+00:00"))
        return True
    except (ValueError, TypeError):
        return False


def create_test_webhook_headers(secret: str, payload: str) -> dict[str, str]:
    """
    Create realistic webhook headers for testing.

    Args:
        secret: The webhook secret
        payload: The payload string

    Returns:
        Dictionary of headers
    """
    signature = create_webhook_signature(payload, secret)

    return {
        "Content-Type": "application/json",
        "Typeform-Signature": signature,
        "User-Agent": "Typeform/1.0 (+https://www.typeform.com)",
        "X-Forwarded-For": "192.168.1.1",
        "Accept": "application/json",
    }


def assert_client_data_complete(
    client_data: dict[str, Any], required_fields: list[str] | None = None
) -> None:
    """
    Assert that client data contains all required fields.

    Args:
        client_data: The client data to validate
        required_fields: List of required field names (default: basic client fields)

    Raises:
        AssertionError: If required fields are missing
    """
    if required_fields is None:
        required_fields = ["form_id", "response_token", "extracted_data"]

    missing_fields = []
    for field in required_fields:
        if field not in client_data:
            missing_fields.append(field)

    if missing_fields:
        raise AssertionError(f"Client data missing required fields: {missing_fields}")


def normalize_webhook_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a webhook payload for consistent testing.

    Args:
        payload: The webhook payload to normalize

    Returns:
        Normalized payload with consistent structure
    """
    normalized = payload.copy()

    # Ensure required structure exists
    if "form_response" not in normalized:
        normalized["form_response"] = {}

    if "answers" not in normalized["form_response"]:
        normalized["form_response"]["answers"] = []

    # Sort answers by field id for consistent comparison
    if normalized["form_response"]["answers"]:
        normalized["form_response"]["answers"] = sorted(
            normalized["form_response"]["answers"],
            key=lambda x: x.get("field", {}).get("id", ""),
        )

    return normalized
