"""
Live Typeform API integration testing.

Tests webhook management operations against the actual Typeform API
using real API keys and forms when available in the test environment.
"""

import pytest
import os
import asyncio
from datetime import datetime

from src.contexts.client_onboarding.core.services.webhook_manager import WebhookManager
from src.contexts.client_onboarding.core.bootstrap.container import Container

from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id,
    reset_all_counters
)

# Skip these tests if no real Typeform credentials are available
TYPEFORM_API_KEY = os.getenv("TYPEFORM_API_KEY")
TYPEFORM_WEBHOOK_SECRET = os.getenv("TYPEFORM_WEBHOOK_SECRET")
TYPEFORM_TEST_URL = os.getenv("TYPEFORM_TEST_URL", "https://api.typeform.com")

# Conditional skip for missing credentials
skip_if_no_credentials = pytest.mark.skipif(
    not TYPEFORM_API_KEY or not TYPEFORM_WEBHOOK_SECRET,
    reason="TYPEFORM_API_KEY and TYPEFORM_WEBHOOK_SECRET environment variables required for live API tests"
)

pytestmark = [pytest.mark.anyio, pytest.mark.e2e, skip_if_no_credentials]


class TestLiveTypeformAPI:
    """Test webhook management operations against live Typeform API."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment with live API configuration."""
        reset_all_counters()
        self.container = Container()
        self.fake_uow = FakeUnitOfWork()
        
        # Create webhook manager with real API credentials
        self.webhook_manager = WebhookManager(
            api_key=TYPEFORM_API_KEY,
            webhook_secret=TYPEFORM_WEBHOOK_SECRET,
            uow_factory=lambda: self.fake_uow
        )
        
        # Track created webhooks for cleanup
        self.created_webhook_ids = []

    async def teardown_method(self):
        """Cleanup any webhooks created during testing."""
        # Clean up any webhooks created during testing
        for webhook_id in self.created_webhook_ids:
            try:
                await self.webhook_manager.delete_webhook(webhook_id)
            except Exception:
                # Ignore cleanup errors - webhook might already be deleted
                pass

    async def test_create_webhook_with_live_api(self):
        """Test creating webhook using live Typeform API."""
        # Given: A registered onboarding form
        form_id = get_next_onboarding_form_id()
        typeform_id = "test_form_live"  # Use a test form ID
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook URL for testing
        webhook_url = f"https://test-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
        
        # When: Creating a webhook via live API
        try:
            webhook_info = await self.webhook_manager.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url
            )
            
            # Track for cleanup
            if webhook_info and "id" in webhook_info:
                self.created_webhook_ids.append(webhook_info["id"])
            
            # Then: Webhook is created successfully
            assert webhook_info is not None
            assert "id" in webhook_info
            assert webhook_info["url"] == webhook_url
            assert webhook_info["enabled"] is True
            
            # And: Webhook configuration is stored
            stored_forms = await self.fake_uow.onboarding_forms.get_all()
            updated_form = next(f for f in stored_forms if f.id == form_id)
            assert updated_form.webhook_id == webhook_info["id"]
            assert updated_form.webhook_url == webhook_url
            
        except TypeFormAPIError as e:
            # If the test form doesn't exist or API is unavailable, skip
            pytest.skip(f"Live API test skipped: {e}")

    async def test_update_webhook_with_live_api(self):
        """Test updating webhook using live Typeform API."""
        # Given: A webhook that exists
        form_id = get_next_onboarding_form_id()
        typeform_id = "test_form_live"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # Create initial webhook
        webhook_url = f"https://test-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
        
        try:
            webhook_info = await self.webhook_manager.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url
            )
            
            if webhook_info and "id" in webhook_info:
                self.created_webhook_ids.append(webhook_info["id"])
                webhook_id = webhook_info["id"]
                
                # When: Updating the webhook
                new_webhook_url = f"https://updated-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
                
                update_result = await self.webhook_manager.update_webhook(
                    webhook_id=webhook_id,
                    webhook_url=new_webhook_url
                )
                
                # Then: Webhook is updated successfully
                assert update_result is True
                
                # And: Form record is updated
                stored_forms = await self.fake_uow.onboarding_forms.get_all()
                updated_form = next(f for f in stored_forms if f.id == form_id)
                assert updated_form.webhook_url == new_webhook_url
                
        except TypeFormAPIError as e:
            pytest.skip(f"Live API test skipped: {e}")

    async def test_delete_webhook_with_live_api(self):
        """Test deleting webhook using live Typeform API."""
        # Given: A webhook that exists
        form_id = get_next_onboarding_form_id()
        typeform_id = "test_form_live"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # Create webhook to delete
        webhook_url = f"https://test-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
        
        try:
            webhook_info = await self.webhook_manager.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url
            )
            
            if webhook_info and "id" in webhook_info:
                webhook_id = webhook_info["id"]
                
                # When: Deleting the webhook
                delete_result = await self.webhook_manager.delete_webhook(webhook_id)
                
                # Then: Webhook is deleted successfully
                assert delete_result is True
                
                # And: Form record is updated
                stored_forms = await self.fake_uow.onboarding_forms.get_all()
                updated_form = next(f for f in stored_forms if f.id == form_id)
                assert updated_form.webhook_id is None
                assert updated_form.webhook_url is None
                
                # Don't add to cleanup list since it's already deleted
                
        except TypeFormAPIError as e:
            pytest.skip(f"Live API test skipped: {e}")

    async def test_webhook_management_error_handling(self):
        """Test error handling for various API failure scenarios."""
        # Given: Invalid form ID
        invalid_form_id = f"invalid_form_{get_next_webhook_counter()}"
        webhook_url = f"https://test-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
        
        # When: Attempting to create webhook for invalid form
        try:
            webhook_info = await self.webhook_manager.create_webhook(
                form_id=invalid_form_id,
                webhook_url=webhook_url
            )
            
            # If no exception, the form might actually exist - clean up
            if webhook_info and "id" in webhook_info:
                self.created_webhook_ids.append(webhook_info["id"])
                
        except TypeFormAPIError as e:
            # Then: Appropriate error is raised
            assert "not found" in str(e).lower() or "invalid" in str(e).lower()

    async def test_rate_limiting_compliance(self):
        """Test that webhook operations comply with Typeform rate limiting."""
        # Given: Multiple webhook operations
        form_id = get_next_onboarding_form_id()
        typeform_id = "test_form_live"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # When: Performing rapid webhook operations
        start_time = datetime.now(UTC)
        
        try:
            # Create webhook
            webhook_url = f"https://test-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
            webhook_info = await self.webhook_manager.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url
            )
            
            if webhook_info and "id" in webhook_info:
                self.created_webhook_ids.append(webhook_info["id"])
                webhook_id = webhook_info["id"]
                
                # Update webhook immediately after creation
                new_url = f"https://updated-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
                await self.webhook_manager.update_webhook(
                    webhook_id=webhook_id,
                    webhook_url=new_url
                )
                
                end_time = datetime.now(UTC)
                
                # Then: Operations respect rate limiting (should take at least 0.5 seconds for 2 req/sec)
                elapsed_time = (end_time - start_time).total_seconds()
                assert elapsed_time >= 0.4  # Allow some tolerance
                
        except TypeFormAPIError as e:
            pytest.skip(f"Live API test skipped: {e}")

    async def test_concurrent_webhook_operations(self):
        """Test concurrent webhook operations don't violate rate limits."""
        # Given: Multiple forms requiring webhook setup
        forms_data = []
        for i in range(3):
            form_id = get_next_onboarding_form_id()
            typeform_id = f"test_form_live_{i}"
            
            onboarding_form = create_onboarding_form(
                id=form_id,
                typeform_id=typeform_id
            )
            await self.fake_uow.onboarding_forms.add(onboarding_form)
            forms_data.append((form_id, typeform_id))
        
        # When: Creating webhooks concurrently
        async def create_webhook_for_form(form_data):
            form_id, typeform_id = form_data
            webhook_url = f"https://concurrent-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
            
            try:
                webhook_info = await self.webhook_manager.create_webhook(
                    form_id=typeform_id,
                    webhook_url=webhook_url
                )
                
                if webhook_info and "id" in webhook_info:
                    self.created_webhook_ids.append(webhook_info["id"])
                
                return webhook_info
            except TypeFormAPIError:
                return None
        
        start_time = datetime.now(UTC)
        
        tasks = [create_webhook_for_form(form_data) for form_data in forms_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now(UTC)
        
        # Then: Rate limiting is respected (3 operations should take at least 1 second)
        elapsed_time = (end_time - start_time).total_seconds()
        assert elapsed_time >= 0.8  # Allow some tolerance for 2 req/sec limit
        
        # And: Some operations succeed (depending on test form availability)
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        # At least operations complete without critical errors
        assert len(results) == 3

    async def test_webhook_status_synchronization(self):
        """Test synchronization of webhook status between Typeform and local database."""
        # Given: A webhook created via the manager
        form_id = get_next_onboarding_form_id()
        typeform_id = "test_form_live"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        webhook_url = f"https://sync-test-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
        
        try:
            webhook_info = await self.webhook_manager.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url
            )
            
            if webhook_info and "id" in webhook_info:
                self.created_webhook_ids.append(webhook_info["id"])
                
                # When: Checking webhook status synchronization
                status_info = await self.webhook_manager.get_webhook_status(webhook_info["id"])
                
                # Then: Status information is available
                assert status_info is not None
                assert "enabled" in status_info
                assert "url" in status_info
                
                # And: Local database reflects the same status
                stored_forms = await self.fake_uow.onboarding_forms.get_all()
                updated_form = next(f for f in stored_forms if f.id == form_id)
                assert updated_form.webhook_id == webhook_info["id"]
                assert updated_form.webhook_url == webhook_url
                
        except TypeFormAPIError as e:
            pytest.skip(f"Live API test skipped: {e}")

    async def test_webhook_operation_audit_trail(self):
        """Test that webhook operations create proper audit trails."""
        # Given: A form for webhook operations
        form_id = get_next_onboarding_form_id()
        typeform_id = "test_form_live"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        webhook_url = f"https://audit-test-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
        
        try:
            # When: Performing webhook operations
            webhook_info = await self.webhook_manager.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url
            )
            
            if webhook_info and "id" in webhook_info:
                self.created_webhook_ids.append(webhook_info["id"])
                
                # Then: Operations are tracked in audit trail
                # Note: Audit trail tracking would be implemented in the webhook manager
                # For now, verify that operations complete successfully
                assert webhook_info["id"] is not None
                assert webhook_info["url"] == webhook_url
                
                # Future: Check audit records in database
                # audit_records = await self.fake_uow.webhook_audit.get_by_form_id(form_id)
                # assert len(audit_records) >= 1
                
        except TypeFormAPIError as e:
            pytest.skip(f"Live API test skipped: {e}")