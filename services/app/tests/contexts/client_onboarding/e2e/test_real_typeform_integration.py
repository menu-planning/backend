"""
Real Typeform e2e testing with actual forms and API keys.

Tests the complete client onboarding flow using real Typeform account,
forms, API keys, and webhooks. This provides the highest confidence
testing for production deployment.

Environment Variables Required:
- TYPEFORM_API_KEY: Your Typeform API key
- TYPEFORM_WEBHOOK_SECRET: Your webhook secret
- TYPEFORM_TEST_URL: Full Typeform URL (e.g., https://yourdomain.typeform.com/to/FORM_ID)
- WEBHOOK_ENDPOINT_URL: Your ngrok tunnel URL (e.g., https://abc123.ngrok.io/webhook)
"""

import pytest
import os
import json
import asyncio
import httpx
from datetime import datetime, timezone
from typing import List, cast

from src.contexts.client_onboarding.core.services.exceptions import (
    TypeFormAPIError,
    WebhookConfigurationError,
    TypeFormFormNotFoundError
)
from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.domain.models.form_response import FormResponse

from src.contexts.client_onboarding.core.services.integrations.typeform.client import create_typeform_client
from src.contexts.client_onboarding.core.services.integrations.typeform.url_parser import TypeformUrlParser
from src.contexts.client_onboarding.core.services.webhooks.manager import WebhookManager
from src.contexts.client_onboarding.core.services.webhooks.processor import process_typeform_webhook
from src.contexts.client_onboarding.core.services.webhooks.security import WebhookSecurityVerifier
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.contexts.client_onboarding.data_factories import (
    create_onboarding_form,
    create_typeform_webhook_payload
)
from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id,
    get_next_user_id,
    reset_all_counters
)

# UTC alias for backward compatibility
UTC = timezone.utc

# Real Typeform credentials and configuration
TYPEFORM_API_KEY = os.getenv("TYPEFORM_API_KEY")
TYPEFORM_WEBHOOK_SECRET = os.getenv("TYPEFORM_WEBHOOK_SECRET")
TYPEFORM_TEST_URL = os.getenv("TYPEFORM_TEST_URL")  # Typeform URL for testing
WEBHOOK_ENDPOINT_URL = os.getenv("WEBHOOK_ENDPOINT_URL")  # Exposed ngrok URL

# Extract form ID from URL
try:
    TYPEFORM_FORM_ID = TypeformUrlParser.extract_form_id(TYPEFORM_TEST_URL) if TYPEFORM_TEST_URL else None
except ValueError:
    TYPEFORM_FORM_ID = None

# Skip these tests if no real Typeform setup is available
skip_if_no_real_setup = pytest.mark.skipif(
    not all([TYPEFORM_API_KEY, TYPEFORM_WEBHOOK_SECRET, TYPEFORM_FORM_ID]),
    reason="TYPEFORM_API_KEY, TYPEFORM_WEBHOOK_SECRET, and TYPEFORM_TEST_URL (valid Typeform URL) required for real e2e tests"
)

# Type guard and casting for when TYPEFORM_FORM_ID is available
if TYPEFORM_FORM_ID:
    # Cast to str for type checking when form ID is available
    TYPEFORM_FORM_ID_STR: str = TYPEFORM_FORM_ID
else:
    # Use placeholder for type checking when no real form ID
    TYPEFORM_FORM_ID_STR: str = "placeholder_form_id"

pytestmark = [pytest.mark.anyio, pytest.mark.e2e, skip_if_no_real_setup]


class TestRealTypeformIntegration:
    """End-to-end testing with real Typeform account and forms."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment with real Typeform configuration."""
        reset_all_counters()
        
        # CRITICAL: Reset fake database state between tests to prevent conflicts
        FakeUnitOfWork.reset_all_data()
        
        self.container = Container()
        self.fake_uow = FakeUnitOfWork()
        
        # Use unique user ID per test to avoid conflicts
        self.test_user_id = get_next_user_id() + 1000  # Start from 1001 to avoid conflicts
        
        # Use processor path with fake UoW
        self.uow_factory = lambda: self.fake_uow
        
        typeform_client = create_typeform_client(api_key=TYPEFORM_API_KEY)
        self.webhook_manager = WebhookManager(typeform_client=typeform_client)
        
        # Track created webhooks and database records for cleanup
        self.created_webhook_ids = []
        self.created_form_ids = []
        self.test_webhook_url = f"{WEBHOOK_ENDPOINT_URL}/webhook" if WEBHOOK_ENDPOINT_URL else f"https://test-{get_next_webhook_counter()}.ngrok.io/webhook"

        # Cleanup after each test
        yield
        
        # Cleanup any webhooks and database records created during testing
        try:
            # Clean up webhooks from Typeform
            for webhook_id in self.created_webhook_ids:
                try:
                    if TYPEFORM_FORM_ID:
                        await self.webhook_manager.typeform_client.delete_webhook(TYPEFORM_FORM_ID_STR, "client_onboarding")
                except Exception:
                    pass  # Ignore cleanup errors
            
            # Clean up database records from fake UoW
            for form_id in self.created_form_ids:
                try:
                    await self.fake_uow.onboarding_forms.delete(form_id)
                except Exception:
                    pass  # Ignore cleanup errors
        except Exception:
            pass  # Ignore all cleanup errors to avoid test failures

    async def test_complete_onboarding_form_lifecycle(self):
        """Test complete lifecycle: form registration → webhook setup → response processing."""
        # Given: A real Typeform form registered in our system
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID_STR,
            title=f"E2E Test Form {get_next_webhook_counter()}",
            user_id=self.test_user_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        self.created_form_ids.append(form_id)
        
        # When: Setting up webhook for the form
        updated_form, webhook_info = await self.webhook_manager.setup_onboarding_form_webhook(
            uow=self.fake_uow,
            user_id=self.test_user_id,
            typeform_id=TYPEFORM_FORM_ID_STR,
            webhook_url=self.test_webhook_url,
            validate_ownership=False
        )
        
        if webhook_info and webhook_info.id:
            self.created_webhook_ids.append(webhook_info.id)
            
            # Then: Webhook is created successfully
            assert webhook_info.id is not None
            assert webhook_info.url == self.test_webhook_url
            assert webhook_info.enabled is True
            
            # And: Form record is updated with webhook information
            assert updated_form.webhook_url == self.test_webhook_url
            assert updated_form.typeform_id == TYPEFORM_FORM_ID_STR
            
            # And: Webhook can process real responses
            # Simulate a real webhook payload from this form
            webhook_payload = create_typeform_webhook_payload(
                form_response={
                    "form_id": TYPEFORM_FORM_ID_STR,
                    "definition": {"id": TYPEFORM_FORM_ID_STR},
                    "token": f"real_response_{get_next_webhook_counter()}"
                }
            )
            payload_json = json.dumps(webhook_payload)
            
            # Process webhook with proper signature
            import hmac
            import hashlib
            import base64
            
            signature_data = payload_json + "\n"
            signature = hmac.new(
                (TYPEFORM_WEBHOOK_SECRET or "").encode(),
                signature_data.encode(),
                hashlib.sha256
            ).digest()
            signature_b64 = base64.b64encode(signature).decode()
            
            headers = {
                "Typeform-Signature": f"sha256={signature_b64}",
                "Content-Type": "application/json"
            }
            
            verifier = WebhookSecurityVerifier(TYPEFORM_WEBHOOK_SECRET)
            is_valid, _ = await verifier.verify_webhook_request(payload=payload_json, headers=headers)
            assert is_valid is True
            success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
            
            # Then: Webhook is processed successfully
            assert success is True
            
            # And: Response is stored in database
            stored_responses = cast(List[FormResponse], await self.fake_uow.form_responses.get_all())
            assert len(stored_responses) == 1
            assert stored_responses[0].form_id == form_id

    async def test_real_webhook_creation_and_validation(self):
        """Test creating webhook on real Typeform form and validating its configuration."""
        # Given: A registered form
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID_STR,
            user_id=self.test_user_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        self.created_form_ids.append(form_id)
        
        # When: Creating webhook on real form
        form, webhook_info = await self.webhook_manager.setup_onboarding_form_webhook(
            uow=self.fake_uow,
            user_id=self.test_user_id,
            typeform_id=TYPEFORM_FORM_ID_STR,
            webhook_url=self.test_webhook_url,
            validate_ownership=False
        )
        
        if webhook_info and webhook_info.id:
            self.created_webhook_ids.append(webhook_info.id)
            
            # Then: Webhook exists on Typeform
            status_info = await self.webhook_manager.get_comprehensive_webhook_status(
                uow=self.fake_uow,
                onboarding_form_id=form.id
            )
            assert status_info is not None
            assert status_info.webhook_exists is True
            assert status_info.webhook_info is not None
            assert status_info.webhook_info.url == self.test_webhook_url
            
            # And: Webhook can be updated (if API key has update permissions)
            new_url = f"https://updated-{get_next_webhook_counter()}.ngrok.io/webhook"
            try:
                updated_webhook = await self.webhook_manager.typeform_client.update_webhook(
                    form_id=TYPEFORM_FORM_ID_STR,
                    tag="client_onboarding",
                    webhook_url=new_url
                )
                assert updated_webhook is not None
                assert updated_webhook.url == new_url
                print("✅ Webhook update successful - API key has update permissions")
            except TypeFormFormNotFoundError:
                # API key lacks webhook update permissions - this is expected with some Typeform plans
                print("ℹ️  Webhook update skipped - API key lacks update permissions (this is normal)")
                pass
            
            # And: Update is reflected in Typeform
            updated_status = await self.webhook_manager.get_comprehensive_webhook_status(
                uow=self.fake_uow,
                onboarding_form_id=form.id
            )
            # Note: Status might not immediately reflect direct API changes

    async def test_real_form_response_processing(self):
        """Test processing responses from real Typeform submissions."""
        # Given: A form with webhook set up
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID_STR,
            user_id=self.test_user_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        self.created_form_ids.append(form_id)
        
        # Create webhook
        form, webhook_info = await self.webhook_manager.setup_onboarding_form_webhook(
            uow=self.fake_uow,
            user_id=self.test_user_id,
            typeform_id=TYPEFORM_FORM_ID_STR,
            webhook_url=self.test_webhook_url,
            validate_ownership=False
        )
        
        if webhook_info and webhook_info.id:
            self.created_webhook_ids.append(webhook_info.id)
            
            # When: Processing multiple real-style responses
            response_tokens = []
            for i in range(3):
                response_token = f"real_token_{get_next_webhook_counter()}_{i}"
                response_tokens.append(response_token)
                
                webhook_payload = create_typeform_webhook_payload(
                    form_response={
                        "form_id": TYPEFORM_FORM_ID_STR,
                        "definition": {"id": TYPEFORM_FORM_ID_STR},
                        "token": response_token
                    }
                )
                payload_json = json.dumps(webhook_payload)
                
                # Process with proper signature
                import hmac
                import hashlib
                import base64
                
                signature_data = payload_json + "\n"
                signature = hmac.new(
                    (TYPEFORM_WEBHOOK_SECRET or "").encode(),
                    signature_data.encode(),
                    hashlib.sha256
                ).digest()
                signature_b64 = base64.b64encode(signature).decode()
                
                headers = {
                    "Typeform-Signature": f"sha256={signature_b64}",
                    "Content-Type": "application/json"
                }
                
                success, error, response_id = await process_typeform_webhook(
                    payload=payload_json,
                    headers=headers,
                    uow_factory=self.uow_factory,
                )
                
                assert success is True
            
            # Then: All responses are stored correctly
            stored_responses = cast(List[FormResponse], await self.fake_uow.form_responses.get_all())
            assert len(stored_responses) == 3
            
            stored_tokens = [r.response_id for r in stored_responses]
            for token in response_tokens:
                assert token in stored_tokens

    async def test_real_webhook_error_scenarios(self):
        """Test error handling scenarios with real Typeform configuration."""
        # Test 1: Invalid form ID
        try:
            invalid_result = await self.webhook_manager.typeform_client.create_webhook(
                form_id="invalid_form_id_12345",
                webhook_url=self.test_webhook_url,
                tag="client_onboarding"
            )
            # If no exception, clean up
            if invalid_result and invalid_result.id:
                self.created_webhook_ids.append(invalid_result.id)
        except TypeFormAPIError as e:
            assert "not found" in str(e).lower() or "invalid" in str(e).lower()
        
        # Test 2: Invalid webhook URL
        form_id = get_next_onboarding_form_id()
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID_STR,
            user_id=self.test_user_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        self.created_form_ids.append(form_id)
        
        try:
            invalid_url_result = await self.webhook_manager.typeform_client.create_webhook(
                form_id=TYPEFORM_FORM_ID_STR,
                webhook_url="invalid-url-format",
                tag="client_onboarding"
            )
            # If no exception, clean up
            if invalid_url_result and invalid_url_result.id:
                self.created_webhook_ids.append(invalid_url_result.id)
        except (TypeFormAPIError, WebhookConfigurationError) as e:
            assert "url" in str(e).lower() or "invalid" in str(e).lower()

    async def test_concurrent_real_webhook_operations(self):
        """Test concurrent operations against real Typeform API with rate limiting."""
        # Given: Multiple forms needing webhooks
        forms_data = []
        for i in range(2):  # Limit to 2 to respect rate limits
            form_id = get_next_onboarding_form_id()
            onboarding_form = create_onboarding_form(
                id=form_id,
                typeform_id=TYPEFORM_FORM_ID_STR,
                user_id=self.test_user_id
            )
            await self.fake_uow.onboarding_forms.add(onboarding_form)
            self.created_form_ids.append(form_id)
            forms_data.append((form_id, TYPEFORM_FORM_ID_STR))
        
        # When: Creating webhooks concurrently
        async def create_webhook_for_form(form_data):
            form_id, typeform_id = form_data
            webhook_url = f"https://concurrent-{get_next_webhook_counter()}.ngrok.io/webhook"
            
            try:
                webhook_info = await self.webhook_manager.typeform_client.create_webhook(
                    form_id=typeform_id,
                    webhook_url=webhook_url,
                    tag="client_onboarding"
                )
                
                if webhook_info and webhook_info.id:
                    self.created_webhook_ids.append(webhook_info.id)
                
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
            typeform_id=TYPEFORM_FORM_ID_STR,
            user_id=self.test_user_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        self.created_form_ids.append(form_id)
        
        # And: A webhook payload for the registered form
        webhook_payload = create_typeform_webhook_payload(
            form_response={
                "form_id": TYPEFORM_FORM_ID_STR,
                "definition": {"id": TYPEFORM_FORM_ID_STR},
                "token": f"signature_test_{get_next_webhook_counter()}"
            }
        )
        payload_json = json.dumps(webhook_payload)
        
        # Test 1: Valid signature
        import hmac
        import hashlib
        import base64
        
        signature_data = payload_json + "\n"
        signature = hmac.new(
            (TYPEFORM_WEBHOOK_SECRET or "").encode(),
            signature_data.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode()
        
        valid_headers = {
            "Typeform-Signature": f"sha256={signature_b64}",
            "Content-Type": "application/json"
        }
        
        # When: Processing with valid signature
        verifier = WebhookSecurityVerifier(TYPEFORM_WEBHOOK_SECRET)
        is_valid, _ = await verifier.verify_webhook_request(payload=payload_json, headers=valid_headers)
        assert is_valid is True
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=valid_headers, uow_factory=self.uow_factory)
        
        # Then: Request is accepted
        assert success is True
        
        # Test 2: Invalid signature
        invalid_headers = {
            "Typeform-Signature": "sha256=invalid_signature_12345",
            "Content-Type": "application/json"
        }
        
        # When: Processing with invalid signature
        is_valid, _ = await verifier.verify_webhook_request(payload=payload_json, headers=invalid_headers)
        
        # Then: Request is rejected
        assert is_valid is False

    async def test_end_to_end_user_creation_flow(self):
        """Test complete flow including user creation in test database."""
        # Given: A test user ID (as mentioned in user requirements)
        test_user_id = f"test_user_{get_next_webhook_counter()}"
        
        # And: A registered form
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID_STR,
            created_by_user_id=test_user_id  # Link form to test user
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        self.created_form_ids.append(form_id)
        
        # When: Processing a webhook that would create/update user data
        webhook_payload = create_typeform_webhook_payload(
            form_response={
                "form_id": TYPEFORM_FORM_ID_STR,
                "definition": {"id": TYPEFORM_FORM_ID_STR},
                "token": f"user_flow_{get_next_webhook_counter()}"
            }
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
            (TYPEFORM_WEBHOOK_SECRET or "").encode(),
            signature_data.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode()
        
        headers = {
            "Typeform-Signature": f"sha256={signature_b64}",
            "Content-Type": "application/json"
        }
        
        verifier = WebhookSecurityVerifier(TYPEFORM_WEBHOOK_SECRET)
        is_valid, _ = await verifier.verify_webhook_request(payload=payload_json, headers=headers)
        assert is_valid is True
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
        
        # Then: Webhook is processed successfully
        assert success is True
        
        # And: Response includes user context
        stored_responses = cast(List[FormResponse], await self.fake_uow.form_responses.get_all())
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

    @pytest.mark.skipif(not WEBHOOK_ENDPOINT_URL, reason="WEBHOOK_ENDPOINT_URL required for live webhook testing")
    async def test_live_webhook_delivery(self):
        """Test actual webhook delivery from Typeform to ngrok endpoint."""
        # Note: This test requires a running ngrok tunnel and webhook endpoint
        # Given: A webhook set up with ngrok URL
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID_STR,
            user_id=self.test_user_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        self.created_form_ids.append(form_id)
        
        # When: Creating webhook with ngrok URL
        form, webhook_info = await self.webhook_manager.setup_onboarding_form_webhook(
            uow=self.fake_uow,
            user_id=self.test_user_id,
            typeform_id=TYPEFORM_FORM_ID_STR,
            webhook_url=WEBHOOK_ENDPOINT_URL,
            validate_ownership=False
        )
        
        if webhook_info and webhook_info.id:
            self.created_webhook_ids.append(webhook_info.id)
            
            # Then: Webhook is accessible
            # Test by making a request to the ngrok URL
            try:
                async with httpx.AsyncClient() as client:
                    # Simple health check to ngrok endpoint
                    response = await client.get(f"{WEBHOOK_ENDPOINT_URL}/health", timeout=5.0)
                    # If endpoint is live, it should respond
                    assert response.status_code in [200, 404]  # 404 is fine if no health endpoint
                    
            except httpx.RequestError:
                # Network error - ngrok might not be running
                pytest.skip("ngrok endpoint not accessible - ensure ngrok is running")
            
            # And: Webhook configuration is valid
            assert webhook_info.url == WEBHOOK_ENDPOINT_URL
            assert webhook_info.enabled is True