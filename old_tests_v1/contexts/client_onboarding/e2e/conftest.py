"""
Pytest configuration and fixtures for E2E tests with real Typeform integration.

Provides consistent setup, teardown, and helper methods for all E2E tests
that need to interact with real Typeform APIs and maintain data isolation.
"""

import base64
import hashlib
import hmac
import json
import os
from typing import Any

import pytest
from src.contexts.client_onboarding.core.services.exceptions import TypeFormAPIError
from src.contexts.client_onboarding.core.services.integrations.typeform.client import (
    create_typeform_client,
)
from src.contexts.client_onboarding.core.services.integrations.typeform.url_parser import (
    TypeformUrlParser,
)
from src.contexts.client_onboarding.core.services.webhooks.manager import WebhookManager
from src.contexts.client_onboarding.core.services.webhooks.security import (
    WebhookSecurityVerifier,
)
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import (
    FakeUnitOfWork,
)
from tests.contexts.client_onboarding.utils.webhook_test_processor import (
    process_typeform_webhook,
)
from tests.utils.counter_manager import (
    get_next_onboarding_form_id,
    get_next_user_id,
    get_next_webhook_counter,
    reset_all_counters,
)

# Environment variables for Typeform integration
TYPEFORM_API_KEY = os.getenv("TYPEFORM_API_KEY")
TYPEFORM_WEBHOOK_SECRET = os.getenv("TYPEFORM_WEBHOOK_SECRET")
TYPEFORM_TEST_URL = os.getenv("TYPEFORM_TEST_URL")
TYPEFORM_WEBHOOK_URL = os.getenv("TYPEFORM_WEBHOOK_URL")

# Extract form ID from URL
try:
    TYPEFORM_FORM_ID = (
        TypeformUrlParser.extract_form_id(TYPEFORM_TEST_URL)
        if TYPEFORM_TEST_URL
        else None
    )
except ValueError:
    TYPEFORM_FORM_ID = None

# Type guard and casting for when TYPEFORM_FORM_ID is available
if TYPEFORM_FORM_ID:
    TYPEFORM_FORM_ID_STR: str = TYPEFORM_FORM_ID
else:
    TYPEFORM_FORM_ID_STR: str = "placeholder_form_id"


# Skip condition for E2E tests
skip_if_no_real_setup = pytest.mark.skipif(
    not all([TYPEFORM_API_KEY, TYPEFORM_WEBHOOK_SECRET, TYPEFORM_FORM_ID]),
    reason="TYPEFORM_API_KEY, TYPEFORM_WEBHOOK_SECRET, and TYPEFORM_TEST_URL (valid Typeform URL) required for real e2e tests",
)


@pytest.fixture(autouse=True)
async def e2e_test_setup():
    """
    Auto-used fixture that sets up E2E test environment with data isolation.

    Provides:
    - Counter reset for deterministic test data
    - Clean fake database state between tests
    - Proper cleanup after each test
    """
    # Reset counters and database state before each test
    reset_all_counters()
    FakeUnitOfWork.reset_all_data()

    # Track cleanup resources
    created_webhook_ids = []
    created_form_ids = []

    yield {
        "created_webhook_ids": created_webhook_ids,
        "created_form_ids": created_form_ids,
    }

    # Cleanup after test (if cleanup is needed, it should be done in test-specific fixtures)
    # The test-specific fixtures will handle cleanup of their resources


@pytest.fixture
async def fake_uow():
    """Provide a fresh FakeUnitOfWork instance for testing."""
    return FakeUnitOfWork()


@pytest.fixture
async def webhook_handler(fake_uow):
    """Backward-compatible alias used by some tests; returns the unit of work."""
    return fake_uow


@pytest.fixture
async def webhook_manager():
    """Provide a WebhookManager instance with real Typeform client."""
    if not TYPEFORM_API_KEY:
        raise ValueError("TYPEFORM_API_KEY is required for E2E tests but was not found")

    typeform_client = create_typeform_client(api_key=TYPEFORM_API_KEY)
    return WebhookManager(typeform_client=typeform_client)


@pytest.fixture
def typeform_config():
    """Provide Typeform configuration constants using real TypeForm ID."""
    # Use the real TypeForm ID - isolation is achieved through user IDs and database records
    # The real form exists and can be used by multiple tests safely
    return {
        "api_key": TYPEFORM_API_KEY,
        "webhook_secret": TYPEFORM_WEBHOOK_SECRET,
        "test_url": TYPEFORM_TEST_URL,
        "form_id": TYPEFORM_FORM_ID_STR,  # Use real TypeForm ID
        "webhook_endpoint_url": TYPEFORM_WEBHOOK_URL,
    }


@pytest.fixture
def test_user_id():
    """Provide a unique user ID for testing."""
    return get_next_user_id() + 1000  # Start from 1001 to avoid conflicts


@pytest.fixture
def unique_form_id():
    """Provide a unique form ID for testing."""
    return get_next_onboarding_form_id()


@pytest.fixture
def test_webhook_url():
    """Provide a test webhook URL."""
    return (
        TYPEFORM_WEBHOOK_URL
        or f"https://test-{get_next_webhook_counter()}.ngrok.io/webhook"
    )


@pytest.fixture
async def webhook_cleanup(webhook_manager):
    """
    Fixture to handle webhook cleanup.

    Usage in tests:
        webhook_ids = webhook_cleanup
        # ... create webhooks and track IDs ...
        webhook_ids.append(created_webhook_id)
        # Cleanup happens automatically at test end
    """
    created_webhook_ids = []

    yield created_webhook_ids

    # Cleanup webhooks after test
    if webhook_manager and TYPEFORM_FORM_ID:
        for webhook_id in created_webhook_ids:
            try:
                await webhook_manager.typeform_client.delete_webhook(
                    TYPEFORM_FORM_ID_STR, "client_onboarding"
                )
            except Exception:
                pass  # Ignore cleanup errors


def create_valid_signature_headers(
    payload_json: str, webhook_secret: str | None = None
) -> dict[str, str]:
    """Helper function to create headers with valid HMAC signature."""
    secret = webhook_secret or TYPEFORM_WEBHOOK_SECRET or ""
    signature_data = payload_json + "\n"
    signature = hmac.new(
        secret.encode(), signature_data.encode(), hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature).decode()

    return {
        "Typeform-Signature": f"sha256={signature_b64}",
        "Content-Type": "application/json",
    }


async def process_webhook_with_signature(
    uow_factory: FakeUnitOfWork,
    webhook_payload: dict[str, Any],
    webhook_secret: str | None = None,
) -> tuple[int[str, Any]]:
    """Process webhook via core processor, optionally verifying signature.

    Returns an HTTP-like status code and a minimal response payload for tests.
    """
    payload_json = json.dumps(webhook_payload)
    headers = create_valid_signature_headers(payload_json, webhook_secret)

    if webhook_secret:
        verifier = WebhookSecurityVerifier(webhook_secret)
        is_valid, err = await verifier.verify_webhook_request(payload_json, headers, 5)
        if not is_valid:
            return 401, {
                "status": "error",
                "error": "security_validation_failed",
                "message": err,
            }

    success, error_message, response_id = await process_typeform_webhook(
        payload=payload_json,
        headers=headers,
        uow_factory=lambda: uow_factory,
    )

    if success:
        return 200, {"status": "success", "response_id": response_id}

    # Map common errors to status/error codes for assertions
    error_lower = (error_message or "").lower()
    if "form not found" in error_lower:
        return 404, {
            "status": "error",
            "error": "form_not_found",
            "message": error_message,
        }
    if (
        "invalid json" in error_lower
        or "invalid payload" in error_lower
        or "missing" in error_lower
    ):
        return 400, {
            "status": "error",
            "error": "invalid_payload",
            "message": error_message,
        }
    if "database" in error_lower or "internal" in error_lower:
        return 500, {
            "status": "error",
            "error": "database_error",
            "message": error_message,
        }
    return 422, {
        "status": "error",
        "error": "processing_error",
        "message": error_message,
    }


def get_test_webhook_url_with_path(base_url: str, path: str = "/webhook") -> str:
    """Helper function to get test webhook URL with optional path."""
    return f"{base_url}{path}"


def skip_if_api_error(error: TypeFormAPIError, test_name: str = "test"):
    """Helper function to skip test if TypeForm API error occurs."""
    pytest.skip(f"{test_name} skipped due to Typeform API error: {error}")
