"""
Fake TypeForm API Implementation

Provides a testable mock of the TypeForm API that returns consistent,
deterministic responses without making actual HTTP calls.

Supports all TypeForm API operations including:
- Form validation and retrieval
- Webhook CRUD operations
- Authentication scenarios
- Error conditions and edge cases
"""

import logging
from datetime import UTC, datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

from tests.utils.counter_manager import (
    get_next_form_response_counter,
    get_next_typeform_api_counter,
    get_next_webhook_counter,
)

logger = logging.getLogger(__name__)


class FakeTypeFormAPI:
    """
    Fake TypeForm API that simulates real API behavior for testing.

    Provides consistent, deterministic responses for all TypeForm operations
    without making actual HTTP requests.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        simulate_errors: bool = False,
    ):
        """
        Initialize fake TypeForm API.

        Args:
            api_key: Fake API key (for testing auth scenarios)
            base_url: Fake base URL (not used but maintains interface)
            simulate_errors: Whether to simulate error conditions
        """
        self.api_key = api_key or "fake_typeform_key_123"
        self.base_url = base_url or "https://fake-api.typeform.com"
        self.simulate_errors = simulate_errors

        # Storage for fake data
        self._forms: dict[str[str, Any]] = {}
        self._webhooks: dict[str, list[dict[str, Any]]] = {}
        self._responses: dict[str, list[dict[str, Any]]] = {}

        # Initialize with some default forms
        self._create_default_forms()

    def _create_default_forms(self):
        """Create default forms for testing."""
        for i in range(1, 4):
            form_id = f"fake_form_{i:03d}"
            counter = get_next_typeform_api_counter()

            self._forms[form_id] = {
                "id": form_id,
                "title": f"Test Onboarding Form {counter}",
                "type": "quiz",  # Required field
                "description": f"Fake form for testing purposes - Form {counter}",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "published": True,
                "public_url": f"https://fake-form.typeform.com/to/{form_id}",
                "workspace": {
                    "href": f"https://api.typeform.com/workspaces/fake_workspace_{counter}"
                },
                "theme": {
                    "href": f"https://api.typeform.com/themes/fake_theme_{counter}"
                },
                "settings": {
                    "is_public": True,
                    "progress_bar": "percentage",
                    "show_progress_bar": True,
                    "show_typeform_branding": True,
                    "meta": {"allow_indexing": False},
                },
                # Required fields for FormInfo model
                "welcome_screens": [
                    {
                        "id": f"welcome_{counter}",
                        "title": f"Welcome to Form {counter}",
                        "properties": {},
                    }
                ],
                "thankyou_screens": [
                    {
                        "id": f"thankyou_{counter}",
                        "title": "Thank you!",
                        "properties": {},
                    }
                ],
                "fields": [
                    {
                        "id": f"field_{counter}_1",
                        "title": "What is your name?",
                        "type": "short_text",
                        "ref": f"name_ref_{counter}",
                        "properties": {},
                    },
                    {
                        "id": f"field_{counter}_2",
                        "title": "What is your email?",
                        "type": "email",
                        "ref": f"email_ref_{counter}",
                        "properties": {},
                    },
                ],
                "hidden": [],
                "variables": {},
                "_links": {
                    "display": f"https://fake-form.typeform.com/to/{form_id}",
                    "responses": f"https://api.typeform.com/forms/{form_id}/responses",
                },
            }

            # Initialize empty webhooks for each form
            self._webhooks[form_id] = []

    def get_form(self, form_id: str) -> dict[str, Any]:
        """
        Get form details by ID.

        Args:
            form_id: Form identifier

        Returns:
            Form data dictionary

        Raises:
            Exception: If form not found or auth fails
        """
        logger.info(f"Fake API: Getting form {form_id}")

        # Simulate authentication error
        if self.simulate_errors and self.api_key == "invalid_key":
            raise Exception("401: Invalid API key")

        # Simulate form not found
        if form_id not in self._forms:
            if self.simulate_errors:
                raise Exception(f"404: Form {form_id} not found")

            # Create form on-the-fly for flexibility
            counter = get_next_typeform_api_counter()
            self._forms[form_id] = {
                "id": form_id,
                "title": f"Test Onboarding Form {counter}",  # Match factory pattern
                "type": "quiz",  # Required field
                "description": f"Dynamically created fake form - {counter}",
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
                "published": True,
                "public_url": f"https://fake-form.typeform.com/to/{form_id}",
                "workspace": {
                    "href": f"https://api.typeform.com/workspaces/fake_workspace_{counter}"
                },
                "theme": {
                    "href": f"https://api.typeform.com/themes/fake_theme_{counter}"
                },
                "settings": {
                    "is_public": True,
                    "progress_bar": "percentage",
                    "show_progress_bar": True,
                    "show_typeform_branding": True,
                    "meta": {"allow_indexing": False},
                },
                # Required fields for FormInfo model
                "welcome_screens": [
                    {
                        "id": f"welcome_{counter}",
                        "title": f"Welcome to Form {counter}",
                        "properties": {},
                    }
                ],
                "thankyou_screens": [
                    {
                        "id": f"thankyou_{counter}",
                        "title": "Thank you!",
                        "properties": {},
                    }
                ],
                "fields": [
                    {
                        "id": f"field_{counter}_1",
                        "title": "What is your name?",
                        "type": "short_text",
                        "ref": f"name_ref_{counter}",
                        "properties": {},
                    },
                    {
                        "id": f"field_{counter}_2",
                        "title": "What is your email?",
                        "type": "email",
                        "ref": f"email_ref_{counter}",
                        "properties": {},
                    },
                ],
                "hidden": [],
                "variables": {},
                "_links": {
                    "display": f"https://fake-form.typeform.com/to/{form_id}",
                    "responses": f"https://api.typeform.com/forms/{form_id}/responses",
                },
            }
            self._webhooks[form_id] = []

        return self._forms[form_id].copy()

    def list_webhooks(self, form_id: str) -> dict[str, Any]:
        """
        List webhooks for a form.

        Args:
            form_id: Form identifier

        Returns:
            Webhooks list response
        """
        logger.info(f"Fake API: Listing webhooks for form {form_id}")

        # Ensure form exists
        self.get_form(form_id)

        webhooks = self._webhooks.get(form_id, [])

        return {"items": webhooks, "page_count": 1, "total_items": len(webhooks)}

    def create_webhook(
        self, form_id: str, webhook_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a webhook for a form.

        Args:
            form_id: Form identifier
            webhook_data: Webhook configuration

        Returns:
            Created webhook data
        """
        logger.info(f"Fake API: Creating webhook for form {form_id}")

        # Ensure form exists - but don't let form creation errors override webhook validation errors
        try:
            self.get_form(form_id)
        except Exception as e:
            if "404" in str(e):
                # If form doesn't exist and we're not simulating errors, create it
                if not self.simulate_errors or not webhook_data.get("url"):
                    counter = get_next_typeform_api_counter()
                    self._forms[form_id] = {
                        "id": form_id,
                        "title": f"Test Onboarding Form {counter}",
                        "description": f"Auto-created test form for webhook testing",
                        "type": "quiz",
                        "workspace": {
                            "href": f"https://api.typeform.com/workspaces/test_workspace_{counter}"
                        },
                        "theme": {
                            "href": f"https://api.typeform.com/themes/test_theme_{counter}"
                        },
                        "settings": {
                            "language": "en",
                            "progress_bar": "percentage",
                            "show_progress_bar": True,
                            "show_typeform_branding": True,
                            "meta": {"allow_indexing": False},
                        },
                        "_links": {
                            "display": f"https://test-typeform.typeform.com/to/{form_id}",
                            "responses": f"https://api.typeform.com/forms/{form_id}/responses",
                        },
                    }
                else:
                    # Re-raise the original form not found error
                    raise

        # Simulate validation error (this should take precedence over form not found)
        if self.simulate_errors and not webhook_data.get("url"):
            raise Exception("422: Webhook URL is required")

        webhook_id = f"fake_webhook_{get_next_webhook_counter()}"
        tag = webhook_data.get("tag", "default")

        webhook = {
            "id": webhook_id,
            "form_id": form_id,
            "tag": tag,
            "url": webhook_data["url"],
            "enabled": webhook_data.get("enabled", True),
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "verify_ssl": webhook_data.get("verify_ssl", True),
            "secret": webhook_data.get("secret"),
            "_links": {
                "self": f"https://api.typeform.com/forms/{form_id}/webhooks/{webhook_id}"
            },
        }

        if form_id not in self._webhooks:
            self._webhooks[form_id] = []

        # Remove any existing webhook with the same tag (replace functionality)
        self._webhooks[form_id] = [
            w for w in self._webhooks[form_id] if w.get("tag") != tag
        ]
        self._webhooks[form_id].append(webhook)

        return webhook

    def get_webhook(self, form_id: str, webhook_tag: str) -> dict[str, Any]:
        """
        Get webhook details by tag.

        Args:
            form_id: Form identifier
            webhook_tag: Webhook tag identifier

        Returns:
            Webhook data
        """
        logger.info(f"Fake API: Getting webhook {webhook_tag} for form {form_id}")

        # Ensure form exists
        self.get_form(form_id)

        webhooks = self._webhooks.get(form_id, [])

        for webhook in webhooks:
            if webhook.get("tag") == webhook_tag:
                return webhook.copy()

        if self.simulate_errors:
            raise Exception(f"404: Webhook {webhook_tag} not found")

        # Return a default webhook if not found and not simulating errors
        webhook_id = f"fake_webhook_{get_next_webhook_counter()}"
        return {
            "id": webhook_id,
            "form_id": form_id,
            "tag": webhook_tag,
            "url": f"https://fake-webhook.example.com/hook/{webhook_tag}",
            "enabled": True,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "verify_ssl": True,
            "_links": {
                "self": f"https://api.typeform.com/forms/{form_id}/webhooks/{webhook_id}"
            },
        }

    def update_webhook(
        self, form_id: str, webhook_tag: str, webhook_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update webhook configuration by tag.

        Args:
            form_id: Form identifier
            webhook_tag: Webhook tag identifier
            webhook_data: Updated webhook data

        Returns:
            Updated webhook data
        """
        logger.info(f"Fake API: Updating webhook {webhook_tag} for form {form_id}")

        # Get existing webhook
        existing_webhook = self.get_webhook(form_id, webhook_tag)

        # Update fields
        existing_webhook.update(webhook_data)
        existing_webhook["updated_at"] = datetime.now(UTC).isoformat()

        # Update in storage
        webhooks = self._webhooks.get(form_id, [])
        for i, webhook in enumerate(webhooks):
            if webhook.get("tag") == webhook_tag:
                webhooks[i] = existing_webhook
                break
        else:
            # If webhook doesn't exist in storage, add it
            webhooks.append(existing_webhook)

        return existing_webhook

    def delete_webhook(self, form_id: str, webhook_tag: str) -> bool:
        """
        Delete a webhook by tag.

        Args:
            form_id: Form identifier
            webhook_tag: Webhook tag identifier

        Returns:
            True if deleted successfully
        """
        logger.info(f"Fake API: Deleting webhook {webhook_tag} for form {form_id}")

        # Ensure form exists
        self.get_form(form_id)

        webhooks = self._webhooks.get(form_id, [])

        for i, webhook in enumerate(webhooks):
            if webhook.get("tag") == webhook_tag:
                del webhooks[i]
                return True

        if self.simulate_errors:
            raise Exception(f"404: Webhook {webhook_tag} not found")

        return True

    def get_responses(self, form_id: str, **params) -> dict[str, Any]:
        """
        Get form responses (for testing webhook payloads).

        Args:
            form_id: Form identifier
            **params: Query parameters (page_size, since, until, etc.)

        Returns:
            Responses data
        """
        logger.info(f"Fake API: Getting responses for form {form_id}")

        # Ensure form exists
        self.get_form(form_id)

        responses = self._responses.get(form_id, [])

        # Apply pagination
        page_size = params.get("page_size", 25)
        page = params.get("page", 1)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        paginated_responses = responses[start_idx:end_idx]

        return {
            "total_items": len(responses),
            "page_count": (len(responses) + page_size - 1) // page_size,
            "items": paginated_responses,
        }

    def add_fake_response(
        self, form_id: str, response_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Add a fake response for testing (not part of real API).

        Args:
            form_id: Form identifier
            response_data: Response data (will create default if None)

        Returns:
            Created response data
        """
        counter = get_next_form_response_counter()

        if response_data is None:
            response_data = {
                "landing_id": f"fake_landing_{counter}",
                "token": f"fake_token_{counter}",
                "response_id": f"fake_response_{counter}",
                "landed_at": datetime.now(UTC).isoformat(),
                "submitted_at": datetime.now(UTC).isoformat(),
                "definition": {
                    "id": form_id,
                    "title": f"Test Form {counter}",
                    "fields": [
                        {
                            "id": f"field_{counter}_1",
                            "title": "What is your name?",
                            "type": "short_text",
                            "ref": f"name_ref_{counter}",
                            "properties": {},
                        },
                        {
                            "id": f"field_{counter}_2",
                            "title": "What is your email?",
                            "type": "email",
                            "ref": f"email_ref_{counter}",
                            "properties": {},
                        },
                    ],
                },
                "answers": [
                    {
                        "field": {
                            "id": f"field_{counter}_1",
                            "type": "short_text",
                            "ref": f"name_ref_{counter}",
                        },
                        "type": "text",
                        "text": f"Test User {counter}",
                    },
                    {
                        "field": {
                            "id": f"field_{counter}_2",
                            "type": "email",
                            "ref": f"email_ref_{counter}",
                        },
                        "type": "email",
                        "email": f"test.user.{counter}@example.com",
                    },
                ],
            }

        if form_id not in self._responses:
            self._responses[form_id] = []

        self._responses[form_id].append(response_data)

        return response_data

    def reset_data(self):
        """Reset all fake data (useful for test isolation)."""
        self._forms.clear()
        self._webhooks.clear()
        self._responses.clear()
        self._create_default_forms()

    def set_error_mode(self, enabled: bool):
        """Enable/disable error simulation."""
        self.simulate_errors = enabled


def create_fake_typeform_api(**kwargs) -> FakeTypeFormAPI:
    """
    Create a FakeTypeFormAPI instance with sensible defaults.

    Args:
        **kwargs: Arguments to pass to FakeTypeFormAPI constructor

    Returns:
        Configured fake API instance
    """
    return FakeTypeFormAPI(**kwargs)


def create_fake_httpx_client(fake_api: FakeTypeFormAPI) -> Mock:
    """
    Create a mock httpx.Client that uses the fake API.

    Args:
        fake_api: Fake API instance to use for responses

    Returns:
        Mock client that can be used to replace httpx.Client in tests
    """
    mock_client = Mock()

    def mock_get(url, **kwargs):
        """Mock GET requests."""
        mock_response = Mock()

        try:
            if "/forms/" in url and "/webhooks/" in url:
                # Individual webhook request - extract form_id and webhook_id
                parts = url.split("/")
                form_id = parts[parts.index("forms") + 1]
                webhook_id = parts[parts.index("webhooks") + 1]
                data = fake_api.get_webhook(form_id, webhook_id)
                mock_response.status_code = 200
                mock_response.json.return_value = data

            elif "/forms/" in url and "/webhooks" in url:
                # Webhooks list request
                form_id = url.split("/forms/")[1].split("/webhooks")[0]
                data = fake_api.list_webhooks(form_id)
                mock_response.status_code = 200
                mock_response.json.return_value = data

            elif "/forms/" in url:
                # Form details request
                form_id = url.split("/forms/")[1].split("/")[0]
                data = fake_api.get_form(form_id)
                mock_response.status_code = 200
                mock_response.json.return_value = data

            else:
                mock_response.status_code = 404
                mock_response.json.return_value = {"message": "Not found"}

        except Exception as e:
            if "401" in str(e):
                mock_response.status_code = 401
                mock_response.json.return_value = {"message": "Unauthorized"}
            elif "404" in str(e):
                mock_response.status_code = 404
                mock_response.json.return_value = {"message": "Not found"}
            elif "422" in str(e):
                mock_response.status_code = 422
                mock_response.json.return_value = {"message": "Validation error"}
            else:
                mock_response.status_code = 500
                mock_response.json.return_value = {"message": "Internal server error"}

        return mock_response

    def mock_post(url, **kwargs):
        """Mock POST requests."""
        mock_response = Mock()

        try:
            if "/webhooks" in url:
                # Create webhook request
                form_id = url.split("/forms/")[1].split("/webhooks")[0]
                data = kwargs.get("json", {})
                webhook_data = fake_api.create_webhook(form_id, data)
                mock_response.status_code = 200
                mock_response.json.return_value = webhook_data
            else:
                mock_response.status_code = 404
                mock_response.json.return_value = {"message": "Not found"}

        except Exception as e:
            if "422" in str(e):
                mock_response.status_code = 422
                mock_response.json.return_value = {"message": "Validation error"}
            else:
                mock_response.status_code = 500
                mock_response.json.return_value = {"message": "Internal server error"}

        return mock_response

    def mock_put(url, **kwargs):
        """Mock PUT requests."""
        mock_response = Mock()

        try:
            if "/webhooks/" in url:
                # Create/Update webhook request
                parts = url.split("/")
                form_id = parts[parts.index("forms") + 1]
                webhook_tag = parts[parts.index("webhooks") + 1]
                data = kwargs.get("json", {})
                # For PUT requests, we treat this as webhook creation
                webhook_data = fake_api.create_webhook(form_id, data)
                mock_response.status_code = 200
                mock_response.json.return_value = webhook_data
            else:
                mock_response.status_code = 404
                mock_response.json.return_value = {"message": "Not found"}

        except Exception as e:
            if "404" in str(e):
                mock_response.status_code = 404
                mock_response.json.return_value = {"message": "Not found"}
            elif "422" in str(e):
                mock_response.status_code = 422
                mock_response.json.return_value = {"message": "Validation error"}
            else:
                mock_response.status_code = 500
                mock_response.json.return_value = {"message": "Internal server error"}

        return mock_response

    def mock_patch(url, **kwargs):
        """Mock PATCH requests."""
        mock_response = Mock()

        try:
            if "/webhooks/" in url:
                # Update webhook request
                parts = url.split("/")
                form_id = parts[parts.index("forms") + 1]
                webhook_tag = parts[parts.index("webhooks") + 1]
                data = kwargs.get("json", {})
                webhook_data = fake_api.update_webhook(form_id, webhook_tag, data)
                mock_response.status_code = 200
                mock_response.json.return_value = webhook_data
            else:
                mock_response.status_code = 404
                mock_response.json.return_value = {"message": "Not found"}

        except Exception as e:
            if "404" in str(e):
                mock_response.status_code = 404
                mock_response.json.return_value = {"message": "Not found"}
            else:
                mock_response.status_code = 500
                mock_response.json.return_value = {"message": "Internal server error"}

        return mock_response

    def mock_delete(url, **kwargs):
        """Mock DELETE requests."""
        mock_response = Mock()

        try:
            if "/webhooks/" in url:
                # Delete webhook request
                parts = url.split("/")
                form_id = parts[parts.index("forms") + 1]
                webhook_tag = parts[parts.index("webhooks") + 1]
                fake_api.delete_webhook(form_id, webhook_tag)
                mock_response.status_code = 204
                mock_response.json.return_value = {}
            else:
                mock_response.status_code = 404
                mock_response.json.return_value = {"message": "Not found"}

        except Exception as e:
            if "404" in str(e):
                mock_response.status_code = 404
                mock_response.json.return_value = {"message": "Not found"}
            else:
                mock_response.status_code = 500
                mock_response.json.return_value = {"message": "Internal server error"}

        return mock_response

    async def mock_request(method, url, **kwargs):
        """Generic async request method that delegates to specific HTTP methods."""
        method = method.upper()
        if method == "GET":
            return mock_get(url, **kwargs)
        elif method == "POST":
            return mock_post(url, **kwargs)
        elif method == "PUT":
            return mock_put(url, **kwargs)
        elif method == "PATCH":
            return mock_patch(url, **kwargs)
        elif method == "DELETE":
            return mock_delete(url, **kwargs)
        else:
            mock_response = Mock()
            mock_response.status_code = 405
            mock_response.json.return_value = {"message": "Method not allowed"}
            return mock_response

    async def async_mock_delete(url, **kwargs):
        """Async version of mock_delete for direct client.delete() calls."""
        return mock_delete(url, **kwargs)

    mock_client.get = mock_get
    mock_client.post = mock_post
    mock_client.put = mock_put
    mock_client.patch = mock_patch
    mock_client.delete = async_mock_delete
    mock_client.request = mock_request
    mock_client.close = Mock()
    mock_client.aclose = Mock()

    return mock_client
