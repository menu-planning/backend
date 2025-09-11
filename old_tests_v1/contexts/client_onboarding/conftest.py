"""
Pytest fixtures for client_onboarding context tests

This conftest.py provides the core fixtures for testing the client onboarding
domain and services, following established testing patterns:

- Domain-focused fixtures for commands and events
- TypeForm API fake implementations
- Test data factories using centralized counter management
- Context-specific test utilities
"""

from unittest.mock import AsyncMock

import pytest
from tests.utils.counter_manager import reset_all_counters


# Mark all tests in this context as using the counter management system
@pytest.fixture(autouse=True)
def reset_counters():
    """Auto-reset all counters before each test for isolation"""
    reset_all_counters()


@pytest.fixture
def mock_webhook_manager():
    """Mock webhook manager for testing webhook operations"""
    mock = AsyncMock()
    mock.create_webhook.return_value = {
        "id": "webhook_123",
        "url": "https://api.typeform.com/webhooks/webhook_123",
        "enabled": True,
    }
    mock.update_webhook.return_value = True
    mock.delete_webhook.return_value = True
    return mock


@pytest.fixture
def mock_event_publisher():
    """Mock event publisher for testing event publishing"""
    mock = AsyncMock()
    mock.publish.return_value = None
    return mock


@pytest.fixture
def mock_typeform_client():
    """Mock TypeForm client for testing API interactions"""
    mock = AsyncMock()
    mock.create_form.return_value = {
        "id": "form_123",
        "title": "Test Onboarding Form",
        "_links": {"display": "https://test.typeform.com/to/form_123"},
    }
    mock.get_form.return_value = {"id": "form_123", "title": "Test Onboarding Form"}
    return mock
