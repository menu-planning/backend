"""
End-to-end webhook flow testing.

Tests the complete flow from Typeform webhook reception to database storage,
including signature verification, payload processing, and data persistence.
"""

import pytest
import json
import asyncio
from unittest.mock import  patch

from src.contexts.client_onboarding.core.services.webhook_processor import process_typeform_webhook
from src.contexts.client_onboarding.core.services.webhook_security import WebhookSecurityVerifier
from src.contexts.client_onboarding.core.bootstrap.container import Container


from tests.contexts.client_onboarding.data_factories import (
    create_onboarding_form,
    create_typeform_webhook_payload
)
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from typing import List, cast
from tests.contexts.client_onboarding.utils.e2e_test_helpers import (
    setup_e2e_test_environment,
)

from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id
)

pytestmark = [pytest.mark.anyio, pytest.mark.e2e]


class TestCompleteWebhookFlow:
    """Test complete webhook processing flow from reception to storage."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment."""
        # Setup clean e2e test environment with data isolation
        self.fake_uow = setup_e2e_test_environment()
        self.container = Container()
        
        # Use fake UoW with core processor path
        self.uow_factory = lambda: self.fake_uow

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
            form_response={
                "form_id": typeform_id,
                "token": f"response_{get_next_webhook_counter()}"
            }
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
        
        # When: Verifying signature and processing the webhook
        verifier = WebhookSecurityVerifier(webhook_secret)
        is_valid, _ = await verifier.verify_webhook_request(payload=payload_json, headers=headers)
        assert is_valid is True
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
        
        # Then: Webhook is processed successfully
        assert success is True
        assert response_id is not None
        
        # And: Form response is stored in database
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
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
            form_response={
                "form_id": typeform_id,
                "token": f"response_{get_next_webhook_counter()}"
            }
        )
        payload_json = json.dumps(webhook_payload)
        
        # And: Invalid HMAC signature
        headers = {
            "Typeform-Signature": "sha256=invalid_signature",
            "Content-Type": "application/json"
        }
        
        # When: Verifying signature fails
        verifier = WebhookSecurityVerifier("test_webhook_secret")
        is_valid, _ = await verifier.verify_webhook_request(payload=payload_json, headers=headers)
        
        # Then: Webhook is rejected
        assert is_valid is False
        
        # And: No form response is stored
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 0

    async def test_complete_webhook_flow_nonexistent_form(self):
        """Test webhook flow with form that doesn't exist in database."""
        # Given: A webhook payload for a form that doesn't exist
        typeform_id = f"nonexistent_form_{get_next_webhook_counter()}"
        webhook_payload = create_typeform_webhook_payload(
            form_response={
                "form_id": typeform_id,
                "token": f"response_{get_next_webhook_counter()}"
            }
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
        
        # When: Verifying signature and processing via processor
        verifier = WebhookSecurityVerifier(webhook_secret)
        is_valid, _ = await verifier.verify_webhook_request(payload=payload_json, headers=headers)
        assert is_valid is True
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
        
        # Then: Webhook processing fails
        assert success is False
        assert error is not None
        assert "form not found" in error.lower()
        
        # And: No form response is stored
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 0

    async def test_complete_webhook_flow_malformed_payload(self):
        """Test webhook flow with malformed JSON payload."""
        # Given: A malformed JSON payload
        payload_json = '{"invalid": json malformed'
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # When: Processing the webhook through processor (will fail JSON parse)
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
        
        # Then: Webhook processing fails
        assert success is False
        assert error is not None
        assert "invalid json" in error.lower()

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
        
        # When: Processing the webhook via processor
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
        
        # Then: Webhook processing fails
        assert success is False
        assert error is not None
        assert "missing" in error.lower() or "invalid" in error.lower()

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
            form_response={
                "form_id": typeform_id,
                "token": f"response_{get_next_webhook_counter()}",
                "answers": [
                    {
                        "field": {
                            "id": "contact_email",
                            "type": "email",
                            "ref": "contact_email"
                        },
                        "type": "email",
                        "email": "test.client@example.com"
                    },
                    {
                        "field": {
                            "id": "company_name",
                            "type": "short_text",
                            "ref": "company_name"
                        },
                        "type": "text",
                        "text": "Test Company Inc"
                    }
                ]
            }
        )
        payload_json = json.dumps(webhook_payload)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # When: Processing the webhook via processor
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
        
        # Then: Webhook is processed successfully
        assert success is True
        
        # And: Client identifiers are extracted and stored
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
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
        await self.fake_uow.commit()  # Ensure form is committed before concurrent processing
        
        # And: Multiple webhook payloads
        payloads = []
        for i in range(5):
            webhook_payload = create_typeform_webhook_payload(
                form_response={
                    "form_id": typeform_id,
                    "token": f"response_{get_next_webhook_counter()}_{i}"
                }
            )
            payloads.append(json.dumps(webhook_payload))
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # When: Processing webhooks concurrently with separate UoW instances for each
        async def process_webhook_with_new_uow(payload):
            """Process webhook with a fresh UoW instance to simulate real concurrent requests."""
            fresh_uow = FakeUnitOfWork()
            return await process_typeform_webhook(payload=payload, headers=headers, uow_factory=lambda: fresh_uow)
        
        tasks = [process_webhook_with_new_uow(payload) for payload in payloads]
        results = await asyncio.gather(*tasks)
        
        # Then: All webhooks are processed successfully
        for success, error, response_id in results:
            assert success is True
        
        # And: All responses are stored correctly in the shared repository
        # Create a fresh UoW to check final state
        check_uow = FakeUnitOfWork()
        stored_responses = cast(List, await check_uow.form_responses.get_all())
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
            form_response={
                "form_id": typeform_id,
                "token": f"response_{get_next_webhook_counter()}"
            }
        )
        payload_json = json.dumps(webhook_payload)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # And: Mock UoW to simulate database error
        with patch.object(self.fake_uow, 'commit', side_effect=Exception("Database error")):
            # When: Processing the webhook
            success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
            
            # Then: Webhook processing fails
            assert success is False
            
            # And: No form response is stored (rolled back)
            stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
            assert len(stored_responses) == 0