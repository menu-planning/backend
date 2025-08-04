"""
End-to-end webhook flow testing.

Tests the complete flow from Typeform webhook reception to database storage,
including signature verification, payload processing, and data persistence.
"""

import pytest
import json
import asyncio
from unittest.mock import  patch

from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
from src.contexts.client_onboarding.core.bootstrap.container import Container


from tests.contexts.client_onboarding.data_factories.client_factories import create_onboarding_form
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork

from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id,
    reset_all_counters
)

pytestmark = [pytest.mark.anyio, pytest.mark.e2e]


class TestCompleteWebhookFlow:
    """Test complete webhook processing flow from reception to storage."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment."""
        reset_all_counters()
        self.container = Container()
        self.fake_uow = FakeUnitOfWork()
        
        # Create webhook handler with fake UoW
        self.webhook_handler = WebhookHandler(
            uow_factory=lambda: self.fake_uow
        )

    async def test_complete_webhook_flow_with_valid_signature(self):
        """Test complete webhook flow with valid HMAC signature."""
        # Given: A registered onboarding form
        form_id = get_next_onboarding_form_id()
        typeform_id = f"typeform_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A valid webhook payload
        webhook_payload = create_typeform_webhook_payload(
            form_id=typeform_id,
            response_token=f"response_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        
        # And: Valid HMAC signature
        webhook_secret = "test_webhook_secret"
        import hmac
        import hashlib
        import base64
        
        signature_data = payload_json + "\n"
        signature = hmac.new(
            webhook_secret.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode()
        
        headers = {
            "Typeform-Signature": f"sha256={signature_b64}",
            "Content-Type": "application/json"
        }
        
        # When: Processing the webhook
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=headers,
            webhook_secret=webhook_secret
        )
        
        # Then: Webhook is processed successfully
        assert status_code == 200
        assert response["status"] == "success"
        assert "form_response_id" in response["data"]
        
        # And: Form response is stored in database
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert len(stored_responses) == 1
        
        stored_response = stored_responses[0]
        assert stored_response.form_id == form_id
        assert stored_response.response_id == webhook_payload["form_response"]["token"]
        assert stored_response.response_data["form_id"] == typeform_id

    async def test_complete_webhook_flow_invalid_signature(self):
        """Test webhook flow rejection with invalid signature."""
        # Given: A registered onboarding form
        form_id = get_next_onboarding_form_id()
        typeform_id = f"typeform_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook payload
        webhook_payload = create_typeform_webhook_payload(
            form_id=typeform_id,
            response_token=f"response_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        
        # And: Invalid HMAC signature
        headers = {
            "Typeform-Signature": "sha256=invalid_signature",
            "Content-Type": "application/json"
        }
        
        # When: Processing the webhook
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=headers,
            webhook_secret="test_webhook_secret"
        )
        
        # Then: Webhook is rejected
        assert status_code == 401
        assert response["status"] == "error"
        assert response["error"] == "security_validation_failed"
        
        # And: No form response is stored
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert len(stored_responses) == 0

    async def test_complete_webhook_flow_nonexistent_form(self):
        """Test webhook flow with form that doesn't exist in database."""
        # Given: A webhook payload for a form that doesn't exist
        typeform_id = f"nonexistent_form_{get_next_webhook_counter()}"
        webhook_payload = create_typeform_webhook_payload(
            form_id=typeform_id,
            response_token=f"response_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        
        # And: Valid HMAC signature
        webhook_secret = "test_webhook_secret"
        import hmac
        import hashlib
        import base64
        
        signature_data = payload_json + "\n"
        signature = hmac.new(
            webhook_secret.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode()
        
        headers = {
            "Typeform-Signature": f"sha256={signature_b64}",
            "Content-Type": "application/json"
        }
        
        # When: Processing the webhook
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=headers,
            webhook_secret=webhook_secret
        )
        
        # Then: Webhook processing fails
        assert status_code == 404
        assert response["status"] == "error"
        assert response["error"] == "onboarding_form_not_found"
        
        # And: No form response is stored
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert len(stored_responses) == 0

    async def test_complete_webhook_flow_malformed_payload(self):
        """Test webhook flow with malformed JSON payload."""
        # Given: A malformed JSON payload
        payload_json = '{"invalid": json malformed'
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # When: Processing the webhook
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=headers,
            webhook_secret=None  # Skip signature verification
        )
        
        # Then: Webhook processing fails
        assert status_code == 400
        assert response["status"] == "error"
        assert response["error"] == "invalid_payload"

    async def test_complete_webhook_flow_missing_required_fields(self):
        """Test webhook flow with payload missing required fields."""
        # Given: A payload missing required fields
        webhook_payload = {
            "event_id": f"event_{get_next_webhook_counter()}",
            "event_type": "form_response",
            # Missing form_response field
        }
        payload_json = json.dumps(webhook_payload)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # When: Processing the webhook
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=headers,
            webhook_secret=None  # Skip signature verification
        )
        
        # Then: Webhook processing fails
        assert status_code == 400
        assert response["status"] == "error"
        assert response["error"] == "invalid_payload"

    async def test_complete_webhook_flow_with_client_identifiers(self):
        """Test complete webhook flow including client identifier extraction."""
        # Given: A registered onboarding form
        form_id = get_next_onboarding_form_id()
        typeform_id = f"typeform_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook payload with client identifiers
        webhook_payload = create_typeform_webhook_payload(
            form_id=typeform_id,
            response_token=f"response_{get_next_webhook_counter()}",
            include_client_data=True
        )
        payload_json = json.dumps(webhook_payload)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # When: Processing the webhook without signature verification
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=headers,
            webhook_secret=None
        )
        
        # Then: Webhook is processed successfully
        assert status_code == 200
        assert response["status"] == "success"
        
        # And: Client identifiers are extracted and stored
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert len(stored_responses) == 1
        
        stored_response = stored_responses[0]
        assert stored_response.client_identifiers is not None
        assert len(stored_response.client_identifiers) > 0

    async def test_complete_webhook_flow_concurrent_processing(self):
        """Test concurrent webhook processing doesn't cause data corruption."""
        # Given: A registered onboarding form
        form_id = get_next_onboarding_form_id()
        typeform_id = f"typeform_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: Multiple webhook payloads
        payloads = []
        for i in range(5):
            webhook_payload = create_typeform_webhook_payload(
                form_id=typeform_id,
                response_token=f"response_{get_next_webhook_counter()}_{i}"
            )
            payloads.append(json.dumps(webhook_payload))
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # When: Processing webhooks concurrently
        tasks = []
        for payload in payloads:
            task = self.webhook_handler.handle_webhook(
                payload=payload,
                headers=headers,
                webhook_secret=None
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Then: All webhooks are processed successfully
        for status_code, response in results:
            assert status_code == 200
            assert response["status"] == "success"
        
        # And: All responses are stored correctly
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert len(stored_responses) == 5
        
        # And: All responses have unique response IDs
        response_ids = [r.response_id for r in stored_responses]
        assert len(set(response_ids)) == 5  # All unique

    async def test_complete_webhook_flow_database_rollback_on_error(self):
        """Test that database operations are rolled back on processing errors."""
        # Given: A registered onboarding form
        form_id = get_next_onboarding_form_id()
        typeform_id = f"typeform_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook payload
        webhook_payload = create_typeform_webhook_payload(
            form_id=typeform_id,
            response_token=f"response_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # And: Mock UoW to simulate database error
        with patch.object(self.fake_uow, 'commit', side_effect=Exception("Database error")):
            # When: Processing the webhook
            status_code, response = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=None
            )
            
            # Then: Webhook processing fails
            assert status_code == 500
            assert response["status"] == "error"
            
            # And: No form response is stored (rolled back)
            stored_responses = await self.fake_uow.form_responses.get_all()
            assert len(stored_responses) == 0