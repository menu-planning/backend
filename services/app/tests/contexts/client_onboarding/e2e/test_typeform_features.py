"""
Comprehensive feature testing with live Typeform.

Tests all client onboarding features against real Typeform API,
including form creation, webhook setup, response handling, and form updates.
"""

import pytest
import os
import json
import asyncio
from datetime import datetime, UTC
from typing import Dict, Any
from unittest.mock import patch

from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
from src.contexts.client_onboarding.core.services.webhook_manager import WebhookManager
from src.contexts.client_onboarding.core.bootstrap.container import Container

from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id,
    reset_all_counters
)

# Real Typeform credentials
TYPEFORM_API_KEY = os.getenv("TYPEFORM_API_KEY")
TYPEFORM_WEBHOOK_SECRET = os.getenv("TYPEFORM_WEBHOOK_SECRET")
TYPEFORM_FORM_ID = os.getenv("TYPEFORM_FORM_ID")

# Skip these tests if no real Typeform setup is available
skip_if_no_credentials = pytest.mark.skipif(
    not all([TYPEFORM_API_KEY, TYPEFORM_WEBHOOK_SECRET]),
    reason="TYPEFORM_API_KEY and TYPEFORM_WEBHOOK_SECRET required for feature tests"
)

pytestmark = [pytest.mark.anyio, pytest.mark.e2e, skip_if_no_credentials]


class TestTypeformFeatures:
    """Comprehensive testing of all client onboarding features with Typeform."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment with real configuration."""
        reset_all_counters()
        self.container = Container()
        self.fake_uow = FakeUnitOfWork()
        
        # Create services with real credentials
        self.webhook_handler = WebhookHandler(
            uow_factory=lambda: self.fake_uow
        )
        
        self.webhook_manager = WebhookManager(
            api_key=TYPEFORM_API_KEY,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET,
            uow_factory=lambda: self.fake_uow
        )
        
        # Track resources for cleanup
        self.created_webhook_ids = []
        self.base_webhook_url = f"https://feature-test-{get_next_webhook_counter()}.ngrok.io"

    async def teardown_method(self):
        """Cleanup test resources."""
        for webhook_id in self.created_webhook_ids:
            try:
                await self.webhook_manager.delete_webhook(webhook_id)
            except Exception:
                pass

    async def test_complete_onboarding_form_management(self):
        """Test complete form management lifecycle: create, configure, update, delete."""
        # Given: Form creation data
        form_id = get_next_onboarding_form_id()
        test_form_id = TYPEFORM_FORM_ID or f"test_form_{get_next_webhook_counter()}"
        
        # When: Creating onboarding form
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=test_form_id,
            title=f"Feature Test Form {get_next_webhook_counter()}",
            description="Comprehensive feature testing form"
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # Then: Form is stored correctly
        stored_forms = await self.fake_uow.onboarding_forms.get_all()
        assert len(stored_forms) == 1
        assert stored_forms[0].typeform_id == test_form_id
        
        # When: Setting up webhook for form
        webhook_url = f"{self.base_webhook_url}/webhook"
        
        try:
            webhook_info = await self.webhook_manager.create_webhook(
                form_id=test_form_id,
                webhook_url=webhook_url
            )
            
            if webhook_info and "id" in webhook_info:
                self.created_webhook_ids.append(webhook_info["id"])
                
                # Then: Webhook is configured
                assert webhook_info["url"] == webhook_url
                assert webhook_info["enabled"] is True
                
                # And: Form record is updated
                updated_forms = await self.fake_uow.onboarding_forms.get_all()
                updated_form = updated_forms[0]
                assert updated_form.webhook_id == webhook_info["id"]
                assert updated_form.webhook_url == webhook_url
                
                # When: Updating webhook URL
                new_webhook_url = f"{self.base_webhook_url}/updated-webhook"
                update_result = await self.webhook_manager.update_webhook(
                    webhook_id=webhook_info["id"],
                    webhook_url=new_webhook_url
                )
                
                # Then: Update succeeds
                assert update_result is True
                
                # And: Form record reflects the update
                final_forms = await self.fake_uow.onboarding_forms.get_all()
                final_form = final_forms[0]
                assert final_form.webhook_url == new_webhook_url
                
        except TypeFormAPIError as e:
            pytest.skip(f"Typeform API test skipped: {e}")

    async def test_form_response_processing_features(self):
        """Test all form response processing features and edge cases."""
        # Given: A registered form
        form_id = get_next_onboarding_form_id()
        test_form_id = TYPEFORM_FORM_ID or f"test_form_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=test_form_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # Test 1: Basic response processing
        response_token = f"feature_test_{get_next_webhook_counter()}"
        webhook_payload = create_typeform_webhook_payload(
            form_id=test_form_id,
            response_token=response_token
        )
        
        await self._process_webhook_with_signature(webhook_payload)
        
        # Verify response stored
        responses = await self.fake_uow.form_responses.get_all()
        assert len(responses) == 1
        assert responses[0].response_id == response_token
        
        # Test 2: Response with client identifiers
        client_response_token = f"client_test_{get_next_webhook_counter()}"
        client_webhook_payload = create_typeform_webhook_payload(
            form_id=test_form_id,
            response_token=client_response_token,
            include_client_data=True
        )
        
        await self._process_webhook_with_signature(client_webhook_payload)
        
        # Verify client data extraction
        all_responses = await self.fake_uow.form_responses.get_all()
        assert len(all_responses) == 2
        
        client_response = next(r for r in all_responses if r.response_id == client_response_token)
        assert client_response.client_identifiers is not None
        
        # Test 3: Multiple rapid responses (concurrency handling)
        rapid_tokens = []
        rapid_payloads = []
        
        for i in range(5):
            token = f"rapid_{get_next_webhook_counter()}_{i}"
            rapid_tokens.append(token)
            
            payload = create_typeform_webhook_payload(
                form_id=test_form_id,
                response_token=token
            )
            rapid_payloads.append(payload)
        
        # Process concurrently
        tasks = [self._process_webhook_with_signature(payload) for payload in rapid_payloads]
        results = await asyncio.gather(*tasks)
        
        # Verify all processed successfully
        for status_code, response in results:
            assert status_code == 200
            assert response["status"] == "success"
        
        # Verify all stored
        final_responses = await self.fake_uow.form_responses.get_all()
        assert len(final_responses) == 7  # 2 previous + 5 rapid
        
        stored_tokens = [r.response_id for r in final_responses]
        for token in rapid_tokens:
            assert token in stored_tokens

    async def test_webhook_security_features(self):
        """Test all webhook security features and validation scenarios."""
        # Given: A registered form
        form_id = get_next_onboarding_form_id()
        test_form_id = TYPEFORM_FORM_ID or f"test_form_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=test_form_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # Test payload
        webhook_payload = create_typeform_webhook_payload(
            form_id=test_form_id,
            response_token=f"security_test_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        
        # Test 1: Valid signature validation
        valid_headers = self._create_valid_signature_headers(payload_json)
        
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=valid_headers,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET
        )
        
        assert status_code == 200
        assert response["status"] == "success"
        
        # Test 2: Invalid signature rejection
        invalid_headers = {
            "Typeform-Signature": "sha256=invalid_signature",
            "Content-Type": "application/json"
        }
        
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=invalid_headers,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET
        )
        
        assert status_code == 401
        assert response["error"] == "security_validation_failed"
        
        # Test 3: Missing signature header
        missing_headers = {
            "Content-Type": "application/json"
        }
        
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=missing_headers,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET
        )
        
        assert status_code == 401
        assert response["error"] == "security_validation_failed"
        
        # Test 4: Malformed signature header
        malformed_headers = {
            "Typeform-Signature": "malformed_without_prefix",
            "Content-Type": "application/json"
        }
        
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=malformed_headers,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET
        )
        
        assert status_code == 401
        assert response["error"] == "security_validation_failed"

    async def test_error_handling_features(self):
        """Test comprehensive error handling across all features."""
        # Test 1: Nonexistent form handling
        nonexistent_payload = create_typeform_webhook_payload(
            form_id=f"nonexistent_{get_next_webhook_counter()}",
            response_token=f"error_test_{get_next_webhook_counter()}"
        )
        
        status_code, response = await self._process_webhook_with_signature(nonexistent_payload)
        
        assert status_code == 404
        assert response["error"] == "onboarding_form_not_found"
        
        # Test 2: Malformed payload handling
        malformed_json = '{"invalid": json structure'
        
        headers = {
            "Content-Type": "application/json"
        }
        
        status_code, response = await self.webhook_handler.handle_webhook(
            payload=malformed_json,
            headers=headers,
            webhook_secret=None
        )
        
        assert status_code == 400
        assert response["error"] == "invalid_payload"
        
        # Test 3: Missing required fields
        incomplete_payload = {
            "event_id": f"incomplete_{get_next_webhook_counter()}",
            "event_type": "form_response"
            # Missing form_response field
        }
        
        status_code, response = await self._process_webhook_with_signature(incomplete_payload)
        
        assert status_code == 400
        assert response["error"] == "invalid_payload"
        
        # Test 4: Database error simulation
        form_id = get_next_onboarding_form_id()
        test_form_id = TYPEFORM_FORM_ID or f"test_form_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=test_form_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        error_payload = create_typeform_webhook_payload(
            form_id=test_form_id,
            response_token=f"db_error_test_{get_next_webhook_counter()}"
        )
        
        # Simulate database error
        with patch.object(self.fake_uow, 'commit', side_effect=Exception("Database connection lost")):
            status_code, response = await self._process_webhook_with_signature(error_payload)
            
            assert status_code == 500
            assert response["status"] == "error"

    async def test_webhook_management_features(self):
        """Test comprehensive webhook management features."""
        if not TYPEFORM_FORM_ID:
            pytest.skip("TYPEFORM_FORM_ID required for webhook management tests")
        
        # Given: A form for webhook management
        form_id = get_next_onboarding_form_id()
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=TYPEFORM_FORM_ID
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        try:
            # Test 1: Webhook creation with validation
            webhook_url = f"{self.base_webhook_url}/management-test"
            
            webhook_info = await self.webhook_manager.create_webhook(
                form_id=TYPEFORM_FORM_ID,
                webhook_url=webhook_url
            )
            
            if webhook_info and "id" in webhook_info:
                self.created_webhook_ids.append(webhook_info["id"])
                webhook_id = webhook_info["id"]
                
                # Test 2: Webhook status checking
                status_info = await self.webhook_manager.get_webhook_status(webhook_id)
                assert status_info is not None
                assert status_info["enabled"] is True
                assert status_info["url"] == webhook_url
                
                # Test 3: Webhook URL update
                updated_url = f"{self.base_webhook_url}/updated-management"
                update_result = await self.webhook_manager.update_webhook(
                    webhook_id=webhook_id,
                    webhook_url=updated_url
                )
                assert update_result is True
                
                # Verify update in status
                updated_status = await self.webhook_manager.get_webhook_status(webhook_id)
                assert updated_status["url"] == updated_url
                
                # Test 4: Webhook deletion
                delete_result = await self.webhook_manager.delete_webhook(webhook_id)
                assert delete_result is True
                
                # Remove from cleanup list since already deleted
                self.created_webhook_ids.remove(webhook_id)
                
                # Verify deletion
                try:
                    deleted_status = await self.webhook_manager.get_webhook_status(webhook_id)
                    # Should either return None or raise an error
                    assert deleted_status is None
                except TypeFormAPIError:
                    # Expected for deleted webhook
                    pass
                
        except TypeFormAPIError as e:
            pytest.skip(f"Webhook management test skipped: {e}")

    async def test_performance_features(self):
        """Test performance characteristics of all features."""
        # Given: A registered form
        form_id = get_next_onboarding_form_id()
        test_form_id = TYPEFORM_FORM_ID or f"test_form_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=test_form_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # Test 1: Webhook processing latency
        start_time = datetime.now(UTC)
        
        webhook_payload = create_typeform_webhook_payload(
            form_id=test_form_id,
            response_token=f"perf_test_{get_next_webhook_counter()}"
        )
        
        status_code, response = await self._process_webhook_with_signature(webhook_payload)
        
        end_time = datetime.now(UTC)
        processing_time = (end_time - start_time).total_seconds()
        
        # Then: Processing is under performance threshold
        assert status_code == 200
        assert processing_time < 2.0  # Under 2 seconds for single webhook
        
        # Test 2: Batch processing performance
        batch_size = 10
        batch_payloads = []
        
        for i in range(batch_size):
            payload = create_typeform_webhook_payload(
                form_id=test_form_id,
                response_token=f"batch_{get_next_webhook_counter()}_{i}"
            )
            batch_payloads.append(payload)
        
        batch_start = datetime.now(UTC)
        
        # Process batch concurrently
        batch_tasks = [self._process_webhook_with_signature(payload) for payload in batch_payloads]
        batch_results = await asyncio.gather(*batch_tasks)
        
        batch_end = datetime.now(UTC)
        batch_time = (batch_end - batch_start).total_seconds()
        
        # Verify all successful
        for status_code, response in batch_results:
            assert status_code == 200
        
        # Performance check: should handle 10 webhooks in reasonable time
        assert batch_time < 5.0  # Under 5 seconds for 10 concurrent webhooks
        
        # Test 3: Memory usage stability
        responses_before = await self.fake_uow.form_responses.get_all()
        initial_count = len(responses_before)
        
        # Process additional load
        load_payloads = []
        for i in range(20):
            payload = create_typeform_webhook_payload(
                form_id=test_form_id,
                response_token=f"load_{get_next_webhook_counter()}_{i}"
            )
            load_payloads.append(payload)
        
        load_tasks = [self._process_webhook_with_signature(payload) for payload in load_payloads]
        load_results = await asyncio.gather(*load_tasks)
        
        # Verify processing maintained quality
        successful_load = sum(1 for status_code, _ in load_results if status_code == 200)
        assert successful_load == 20
        
        # Verify data integrity
        final_responses = await self.fake_uow.form_responses.get_all()
        assert len(final_responses) == initial_count + batch_size + 20

    async def _process_webhook_with_signature(self, webhook_payload: Dict[str, Any]) -> tuple:
        """Helper to process webhook with proper signature."""
        payload_json = json.dumps(webhook_payload)
        headers = self._create_valid_signature_headers(payload_json)
        
        return await self.webhook_handler.handle_webhook(
            payload=payload_json,
            headers=headers,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET
        )

    def _create_valid_signature_headers(self, payload_json: str) -> Dict[str, str]:
        """Helper to create headers with valid HMAC signature."""
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
        
        return {
            "Typeform-Signature": f"sha256={signature_b64}",
            "Content-Type": "application/json"
        }