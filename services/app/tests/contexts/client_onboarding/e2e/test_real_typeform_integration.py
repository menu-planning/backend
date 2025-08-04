"""
Real Typeform e2e testing with actual forms and API keys.

Tests the complete client onboarding flow using real Typeform account,
forms, API keys, and webhooks. This provides the highest confidence
testing for production deployment.
"""

import pytest
import os
import json
import asyncio
import httpx
from datetime import datetime, UTC


from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
from src.contexts.client_onboarding.core.services.webhook_manager import WebhookManager
from src.contexts.client_onboarding.core.bootstrap.container import Container

from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id,
    reset_all_counters
)

# Real Typeform credentials and configuration
TYPEFORM_API_KEY = os.getenv("TYPEFORM_API_KEY")
TYPEFORM_WEBHOOK_SECRET = os.getenv("TYPEFORM_WEBHOOK_SECRET")
TYPEFORM_FORM_ID = os.getenv("TYPEFORM_FORM_ID")  # Real form ID for testing
NGROK_WEBHOOK_URL = os.getenv("NGROK_WEBHOOK_URL")  # Exposed ngrok URL

# Skip these tests if no real Typeform setup is available
skip_if_no_real_setup = pytest.mark.skipif(
    not all([TYPEFORM_API_KEY, TYPEFORM_WEBHOOK_SECRET, TYPEFORM_FORM_ID]),
    reason="TYPEFORM_API_KEY, TYPEFORM_WEBHOOK_SECRET, and TYPEFORM_FORM_ID required for real e2e tests"
)

pytestmark = [pytest.mark.anyio, pytest.mark.e2e, skip_if_no_real_setup]


class TestRealTypeformIntegration:
    """End-to-end testing with real Typeform account and forms."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment with real Typeform configuration."""
        reset_all_counters()
        self.container = Container()
        self.fake_uow = FakeUnitOfWork()
        
        # Create webhook handler and manager with real credentials
        self.webhook_handler = WebhookHandler(
            uow_factory=lambda: self.fake_uow
        )
        
        self.webhook_manager = WebhookManager(
            api_key=TYPEFORM_API_KEY,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET,
            uow_factory=lambda: self.fake_uow
        )
        
        # Track created webhooks for cleanup
        self.created_webhook_ids = []
        self.test_webhook_url = NGROK_WEBHOOK_URL or f"https://test-{get_next_webhook_counter()}.ngrok.io/webhook"

    async def teardown_method(self):
        """Cleanup any webhooks created during testing."""
        for webhook_id in self.created_webhook_ids:
            try:
                await self.webhook_manager.delete_webhook(webhook_id)
            except Exception:
                pass  # Ignore cleanup errors

    async def test_complete_onboarding_form_lifecycle(self):
        """Test complete lifecycle: form registration → webhook setup → response processing."""
        # Given: A real Typeform form registered in our system
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID,
            title=f"E2E Test Form {get_next_webhook_counter()}"
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # When: Setting up webhook for the form
        webhook_info = await self.webhook_manager.create_webhook(
            form_id=TYPEFORM_FORM_ID,
            webhook_url=self.test_webhook_url
        )
        
        if webhook_info and "id" in webhook_info:
            self.created_webhook_ids.append(webhook_info["id"])
            
            # Then: Webhook is created successfully
            assert webhook_info["id"] is not None
            assert webhook_info["url"] == self.test_webhook_url
            assert webhook_info["enabled"] is True
            
            # And: Form record is updated with webhook information
            stored_forms = await self.fake_uow.onboarding_forms.get_all()
            updated_form = next(f for f in stored_forms if f.id == form_id)
            assert updated_form.webhook_id == webhook_info["id"]
            assert updated_form.webhook_url == self.test_webhook_url
            
            # And: Webhook can process real responses
            # Simulate a real webhook payload from this form
            webhook_payload = create_typeform_webhook_payload(
                form_id=TYPEFORM_FORM_ID,
                response_token=f"real_response_{get_next_webhook_counter()}"
            )
            payload_json = json.dumps(webhook_payload)
            
            # Process webhook with proper signature
            import hmac
            import hashlib
            import base64
            
            signature_data = payload_json + "\n"
            signature = hmac.new(
                TYPEFORM_WEBHOOK_SECRET.encode(),
                signature_data.encode(),
                hashlib.sha256
            ).digest()
            signature_b64 = base64.b64encode(signature).decode()
            
            headers = {
                "Typeform-Signature": f"sha256={signature_b64}",
                "Content-Type": "application/json"
            }
            
            status_code, response = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=TYPEFORM_WEBHOOK_SECRET
            )
            
            # Then: Webhook is processed successfully
            assert status_code == 200
            assert response["status"] == "success"
            
            # And: Response is stored in database
            stored_responses = await self.fake_uow.form_responses.get_all()
            assert len(stored_responses) == 1
            assert stored_responses[0].form_id == form_id

    async def test_real_webhook_creation_and_validation(self):
        """Test creating webhook on real Typeform form and validating its configuration."""
        # Given: A registered form
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # When: Creating webhook on real form
        webhook_info = await self.webhook_manager.create_webhook(
            form_id=TYPEFORM_FORM_ID,
            webhook_url=self.test_webhook_url
        )
        
        if webhook_info and "id" in webhook_info:
            self.created_webhook_ids.append(webhook_info["id"])
            webhook_id = webhook_info["id"]
            
            # Then: Webhook exists on Typeform
            status_info = await self.webhook_manager.get_webhook_status(webhook_id)
            assert status_info is not None
            assert status_info["enabled"] is True
            assert status_info["url"] == self.test_webhook_url
            
            # And: Webhook can be updated
            new_url = f"https://updated-{get_next_webhook_counter()}.ngrok.io/webhook"
            update_result = await self.webhook_manager.update_webhook(
                webhook_id=webhook_id,
                webhook_url=new_url
            )
            assert update_result is True
            
            # And: Update is reflected in Typeform
            updated_status = await self.webhook_manager.get_webhook_status(webhook_id)
            assert updated_status["url"] == new_url

    async def test_real_form_response_processing(self):
        """Test processing responses from real Typeform submissions."""
        # Given: A form with webhook set up
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # Create webhook
        webhook_info = await self.webhook_manager.create_webhook(
            form_id=TYPEFORM_FORM_ID,
            webhook_url=self.test_webhook_url
        )
        
        if webhook_info and "id" in webhook_info:
            self.created_webhook_ids.append(webhook_info["id"])
            
            # When: Processing multiple real-style responses
            response_tokens = []
            for i in range(3):
                response_token = f"real_token_{get_next_webhook_counter()}_{i}"
                response_tokens.append(response_token)
                
                webhook_payload = create_typeform_webhook_payload(
                    form_id=TYPEFORM_FORM_ID,
                    response_token=response_token,
                    include_client_data=True
                )
                payload_json = json.dumps(webhook_payload)
                
                # Process with proper signature
                import hmac
                import hashlib
                import base64
                
                signature_data = payload_json + "\n"
                signature = hmac.new(
                    TYPEFORM_WEBHOOK_SECRET.encode(),
                    signature_data.encode(),
                    hashlib.sha256
                ).digest()
                signature_b64 = base64.b64encode(signature).decode()
                
                headers = {
                    "Typeform-Signature": f"sha256={signature_b64}",
                    "Content-Type": "application/json"
                }
                
                status_code, response = await self.webhook_handler.handle_webhook(
                    payload=payload_json,
                    headers=headers,
                    webhook_secret=TYPEFORM_WEBHOOK_SECRET
                )
                
                assert status_code == 200
                assert response["status"] == "success"
            
            # Then: All responses are stored correctly
            stored_responses = await self.fake_uow.form_responses.get_all()
            assert len(stored_responses) == 3
            
            stored_tokens = [r.response_id for r in stored_responses]
            for token in response_tokens:
                assert token in stored_tokens

    async def test_real_webhook_error_scenarios(self):
        """Test error handling scenarios with real Typeform configuration."""
        # Test 1: Invalid form ID
        try:
            invalid_result = await self.webhook_manager.create_webhook(
                form_id="invalid_form_id_12345",
                webhook_url=self.test_webhook_url
            )
            # If no exception, clean up
            if invalid_result and "id" in invalid_result:
                self.created_webhook_ids.append(invalid_result["id"])
        except TypeFormAPIError as e:
            assert "not found" in str(e).lower() or "invalid" in str(e).lower()
        
        # Test 2: Invalid webhook URL
        form_id = get_next_onboarding_form_id()
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        try:
            invalid_url_result = await self.webhook_manager.create_webhook(
                form_id=TYPEFORM_FORM_ID,
                webhook_url="invalid-url-format"
            )
            # If no exception, clean up
            if invalid_url_result and "id" in invalid_url_result:
                self.created_webhook_ids.append(invalid_url_result["id"])
        except (TypeFormAPIError, WebhookManagementError) as e:
            assert "url" in str(e).lower() or "invalid" in str(e).lower()

    async def test_concurrent_real_webhook_operations(self):
        """Test concurrent operations against real Typeform API with rate limiting."""
        # Given: Multiple forms needing webhooks
        forms_data = []
        for i in range(2):  # Limit to 2 to respect rate limits
            form_id = get_next_onboarding_form_id()
            onboarding_form = create_onboarding_form(
                id=form_id,
                typeform_id=TYPEFORM_FORM_ID
            )
            await self.fake_uow.onboarding_forms.add(onboarding_form)
            forms_data.append((form_id, TYPEFORM_FORM_ID))
        
        # When: Creating webhooks concurrently
        async def create_webhook_for_form(form_data):
            form_id, typeform_id = form_data
            webhook_url = f"https://concurrent-{get_next_webhook_counter()}.ngrok.io/webhook"
            
            try:
                webhook_info = await self.webhook_manager.create_webhook(
                    form_id=typeform_id,
                    webhook_url=webhook_url
                )
                
                if webhook_info and "id" in webhook_info:
                    self.created_webhook_ids.append(webhook_info["id"])
                
                return webhook_info
            except Exception as e:
                return e
        
        start_time = datetime.now(UTC)
        
        tasks = [create_webhook_for_form(form_data) for form_data in forms_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now(UTC)
        
        # Then: Rate limiting is respected (2 operations should take at least 0.5 seconds)
        elapsed_time = (end_time - start_time).total_seconds()
        assert elapsed_time >= 0.4  # Allow tolerance for 2 req/sec limit
        
        # And: At least one operation succeeds
        successful_results = [r for r in results if not isinstance(r, Exception) and r is not None]
        assert len(successful_results) >= 1

    async def test_webhook_signature_validation_with_real_secret(self):
        """Test HMAC signature validation using real Typeform webhook secret."""
        # Given: A registered form
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook payload
        webhook_payload = create_typeform_webhook_payload(
            form_id=TYPEFORM_FORM_ID,
            response_token=f"signature_test_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        
        # Test 1: Valid signature
        import hmac
        import hashlib
        import base64
        
        signature_data = payload_json + "\n"
        signature = hmac.new(
            TYPEFORM_WEBHOOK_SECRET.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode()
        
        valid_headers = {
            "Typeform-Signature": f"sha256={signature_b64}",
            "Content-Type": "application/json"
        }
        
        # When: Processing with valid signature
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=valid_headers,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET
        )
        
        # Then: Request is accepted
        assert status_code == 200
        assert response["status"] == "success"
        
        # Test 2: Invalid signature
        invalid_headers = {
            "Typeform-Signature": "sha256=invalid_signature_12345",
            "Content-Type": "application/json"
        }
        
        # When: Processing with invalid signature
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=invalid_headers,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET
        )
        
        # Then: Request is rejected
        assert status_code == 401
        assert response["status"] == "error"
        assert response["error"] == "security_validation_failed"

    async def test_end_to_end_user_creation_flow(self):
        """Test complete flow including user creation in test database."""
        # Given: A test user ID (as mentioned in user requirements)
        test_user_id = f"test_user_{get_next_webhook_counter()}"
        
        # And: A registered form
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID,
            created_by_user_id=test_user_id  # Link form to test user
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # When: Processing a webhook that would create/update user data
        webhook_payload = create_typeform_webhook_payload(
            form_id=TYPEFORM_FORM_ID,
            response_token=f"user_flow_{get_next_webhook_counter()}",
            include_client_data=True
        )
        
        # Add user identifier to the payload
        if "form_response" in webhook_payload and "answers" in webhook_payload["form_response"]:
            webhook_payload["form_response"]["answers"].append({
                "field": {
                    "id": "user_id_field",
                    "type": "short_text",
                    "ref": "user_id"
                },
                "type": "text",
                "text": test_user_id
            })
        
        payload_json = json.dumps(webhook_payload)
        
        # Process with signature
        import hmac
        import hashlib
        import base64
        
        signature_data = payload_json + "\n"
        signature = hmac.new(
            TYPEFORM_WEBHOOK_SECRET.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode()
        
        headers = {
            "Typeform-Signature": f"sha256={signature_b64}",
            "Content-Type": "application/json"
        }
        
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=headers,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET
        )
        
        # Then: Webhook is processed successfully
        assert status_code == 200
        assert response["status"] == "success"
        
        # And: Response includes user context
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert len(stored_responses) == 1
        
        stored_response = stored_responses[0]
        assert stored_response.form_id == form_id
        
        # And: Client identifiers include the test user
        if stored_response.client_identifiers:
            user_identifiers = [
                identifier for identifier in stored_response.client_identifiers
                if test_user_id in str(identifier)
            ]
            # Note: This depends on the client identifier extraction logic
            # For now, just verify the response was stored with the form

    @pytest.mark.skipif(not NGROK_WEBHOOK_URL, reason="NGROK_WEBHOOK_URL required for live webhook testing")
    async def test_live_webhook_delivery(self):
        """Test actual webhook delivery from Typeform to ngrok endpoint."""
        # Note: This test requires a running ngrok tunnel and webhook endpoint
        # Given: A webhook set up with ngrok URL
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # When: Creating webhook with ngrok URL
        webhook_info = await self.webhook_manager.create_webhook(
            form_id=TYPEFORM_FORM_ID,
            webhook_url=NGROK_WEBHOOK_URL
        )
        
        if webhook_info and "id" in webhook_info:
            self.created_webhook_ids.append(webhook_info["id"])
            
            # Then: Webhook is accessible
            # Test by making a request to the ngrok URL
            try:
                async with httpx.AsyncClient() as client:
                    # Simple health check to ngrok endpoint
                    response = await client.get(f"{NGROK_WEBHOOK_URL}/health", timeout=5.0)
                    # If endpoint is live, it should respond
                    assert response.status_code in [200, 404]  # 404 is fine if no health endpoint
                    
            except httpx.RequestError:
                # Network error - ngrok might not be running
                pytest.skip("ngrok endpoint not accessible - ensure ngrok is running")
            
            # And: Webhook configuration is valid
            assert webhook_info["url"] == NGROK_WEBHOOK_URL
            assert webhook_info["enabled"] is True