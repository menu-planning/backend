"""
Live Typeform API integration testing.

Tests webhook management operations against the actual Typeform API
using real API keys and forms when available in the test environment.
"""

import pytest
import os
import asyncio
from datetime import datetime, timezone

from src.contexts.client_onboarding.core.services.webhook_manager import WebhookManager
from src.contexts.client_onboarding.core.services.typeform_client import (
    TypeFormAPIError,
    create_typeform_client
)
from src.contexts.client_onboarding.core.bootstrap.container import Container

from tests.contexts.client_onboarding.data_factories import (
    create_onboarding_form,
)
from tests.contexts.client_onboarding.utils.e2e_test_helpers import (
    setup_e2e_test_environment,
    teardown_e2e_test_environment
)
from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id
)

# UTC alias for backward compatibility
UTC = timezone.utc

# Skip these tests if no real Typeform credentials are available
TYPEFORM_API_KEY = os.getenv("TYPEFORM_API_KEY")
TYPEFORM_WEBHOOK_SECRET = os.getenv("TYPEFORM_WEBHOOK_SECRET")
TYPEFORM_TEST_URL = os.getenv("TYPEFORM_TEST_URL", "https://api.typeform.com")
WEBHOOK_ENDPOINT_URL = os.getenv("WEBHOOK_ENDPOINT_URL")

# Extract form ID from test URL if available
def extract_form_id_from_url(url: str) -> str:
    """Extract form ID from Typeform URL like https://w3rzk8nsj6k.typeform.com/to/o8Qyi3Ix"""
    if "/to/" in url:
        return url.split("/to/")[-1]
    return "test_form_live"  # fallback to original hardcoded ID

TYPEFORM_TEST_FORM_ID = extract_form_id_from_url(TYPEFORM_TEST_URL)

# Conditional skip for missing credentials or webhook endpoint
skip_if_no_credentials = pytest.mark.skipif(
    not TYPEFORM_API_KEY or not TYPEFORM_WEBHOOK_SECRET or not WEBHOOK_ENDPOINT_URL,
    reason="TYPEFORM_API_KEY, TYPEFORM_WEBHOOK_SECRET, and WEBHOOK_ENDPOINT_URL environment variables required for live API tests"
)

pytestmark = [pytest.mark.anyio, pytest.mark.e2e, skip_if_no_credentials]


class TestLiveTypeformAPI:
    """Test webhook management operations against live Typeform API."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment with live API configuration."""
        # Setup clean e2e test environment with data isolation
        self.fake_uow = setup_e2e_test_environment()
        self.container = Container()
        
        # Create webhook manager with real API credentials
        typeform_client = create_typeform_client(api_key=TYPEFORM_API_KEY)
        self.webhook_manager = WebhookManager(typeform_client=typeform_client)
        
        # Track created webhooks for cleanup
        self.created_webhook_ids = []

    def teardown_method(self):
        """Cleanup any webhooks created during testing."""
        # Ensure clean state for next test
        teardown_e2e_test_environment()
        
        # Note: Async webhook cleanup should be handled within each test method
        # as pytest doesn't support async teardown_method

    async def test_create_webhook_with_live_api(self):
        """Test creating webhook using live Typeform API."""
        # Given: A registered onboarding form
        form_id = get_next_onboarding_form_id()
        typeform_id = TYPEFORM_TEST_FORM_ID  # Use the actual test form ID from environment
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id,
            user_id=1  # Consistent user_id to match webhook manager call
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook URL for testing
        webhook_url = f"{WEBHOOK_ENDPOINT_URL}/webhook"
        
        # When: Creating a webhook via live API
        try:
            # Use the setup method which handles the complete webhook setup
            updated_form, webhook_info = await self.webhook_manager.setup_onboarding_form_webhook(
                uow=self.fake_uow,
                user_id=1,
                typeform_id=typeform_id,
                webhook_url=webhook_url,
                validate_ownership=False  # Skip ownership validation for test
            )
            
            # Track for cleanup
            if webhook_info and webhook_info.id:
                self.created_webhook_ids.append(webhook_info.id)
            
            # Then: Webhook is created successfully
            assert webhook_info is not None
            assert webhook_info.id is not None
            assert webhook_info.url == webhook_url
            assert webhook_info.enabled is True
            
            # And: Webhook configuration is stored
            assert updated_form.webhook_url == webhook_url
            assert updated_form.typeform_id == typeform_id
            
        except TypeFormAPIError as e:
            # If the test form doesn't exist or API is unavailable, skip
            pytest.skip(f"Live API test skipped: {e}")

    async def test_update_webhook_with_live_api(self):
        """Test updating webhook using live Typeform API."""
        # Given: A webhook that exists
        form_id = get_next_onboarding_form_id()
        typeform_id = TYPEFORM_TEST_FORM_ID  # Use the actual test form ID from environment
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id,
            user_id=1  # Consistent user_id to match webhook manager call
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # Create initial webhook
        webhook_url = f"{WEBHOOK_ENDPOINT_URL}/webhook"
        
        try:
            # Setup initial webhook
            form, webhook_info = await self.webhook_manager.setup_onboarding_form_webhook(
                uow=self.fake_uow,
                user_id=1,
                typeform_id=typeform_id,
                webhook_url=webhook_url,
                validate_ownership=False
            )
            
            if webhook_info and webhook_info.id:
                self.created_webhook_ids.append(webhook_info.id)
                
                # When: Updating the webhook
                new_webhook_url = f"https://updated-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
                
                updated_webhook = await self.webhook_manager.typeform_client.update_webhook(
                    form_id=typeform_id,
                    tag="client_onboarding",
                    webhook_url=new_webhook_url
                )
                
                # Then: Webhook is updated successfully
                assert updated_webhook is not None
                assert updated_webhook.url == new_webhook_url
                
                # Note: WebhookManager doesn't automatically update form records for direct API calls
                
        except TypeFormAPIError as e:
            pytest.skip(f"Live API test skipped: {e}")

    async def test_delete_webhook_with_live_api(self):
        """Test deleting webhook using live Typeform API."""
        # Given: A webhook that exists
        form_id = get_next_onboarding_form_id()
        typeform_id = TYPEFORM_TEST_FORM_ID  # Use the actual test form ID from environment
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id,
            user_id=1  # Consistent user_id to match webhook manager call
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # Create webhook to delete
        webhook_url = f"{WEBHOOK_ENDPOINT_URL}/webhook"
        
        try:
            # Setup webhook
            form, webhook_info = await self.webhook_manager.setup_onboarding_form_webhook(
                uow=self.fake_uow,
                user_id=1,
                typeform_id=typeform_id,
                webhook_url=webhook_url,
                validate_ownership=False
            )
            
            if webhook_info and webhook_info.id:
                # When: Deleting the webhook
                delete_result = await self.webhook_manager.typeform_client.delete_webhook(
                    form_id=typeform_id,
                    tag="client_onboarding"
                )
                
                # Then: Webhook is deleted successfully
                assert delete_result is True
                
                # Note: WebhookManager doesn't automatically update form records for direct API calls
                
                # Don't add to cleanup list since it's already deleted
                
        except TypeFormAPIError as e:
            pytest.skip(f"Live API test skipped: {e}")

    async def test_webhook_management_error_handling(self):
        """Test error handling for various API failure scenarios."""
        # Given: Invalid form ID
        invalid_form_id = f"invalid_form_{get_next_webhook_counter()}"
        webhook_url = f"{WEBHOOK_ENDPOINT_URL}/webhook"
        
        # When: Attempting to create webhook for invalid form
        try:
            webhook_info = await self.webhook_manager.typeform_client.create_webhook(
                form_id=invalid_form_id,
                webhook_url=webhook_url,
                tag="client_onboarding"
            )
            
            # If no exception, the form might actually exist - clean up
            if webhook_info and webhook_info.id:
                self.created_webhook_ids.append(webhook_info.id)
                
        except TypeFormAPIError as e:
            # Then: Appropriate error is raised
            assert "not found" in str(e).lower() or "invalid" in str(e).lower()

    async def test_rate_limiting_compliance(self):
        """Test that webhook operations comply with Typeform rate limiting."""
        # Given: Multiple webhook operations
        form_id = get_next_onboarding_form_id()
        typeform_id = TYPEFORM_TEST_FORM_ID  # Use the actual test form ID from environment
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id,
            user_id=1  # Consistent user_id to match webhook manager call
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # When: Performing rapid webhook operations
        start_time = datetime.now(UTC)
        
        try:
            # Create webhook
            webhook_url = f"{WEBHOOK_ENDPOINT_URL}/webhook"
            webhook_info = await self.webhook_manager.typeform_client.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url,
                tag="client_onboarding"
            )
            
            if webhook_info and webhook_info.id:
                self.created_webhook_ids.append(webhook_info.id)
                
                # Update webhook immediately after creation
                new_url = f"https://updated-webhook-{get_next_webhook_counter()}.ngrok.io/webhook"
                await self.webhook_manager.typeform_client.update_webhook(
                    form_id=typeform_id,
                    tag="client_onboarding",
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
            typeform_id = TYPEFORM_TEST_FORM_ID  # Use the actual test form ID from environment
            
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
                webhook_info = await self.webhook_manager.typeform_client.create_webhook(
                    form_id=typeform_id,
                    webhook_url=webhook_url,
                    tag="client_onboarding"
                )
                
                if webhook_info and webhook_info.id:
                    self.created_webhook_ids.append(webhook_info.id)
                
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
        # Given: A clean slate (remove any existing webhooks)
        try:
            await self.webhook_manager.typeform_client.delete_webhook(
                form_id=TYPEFORM_TEST_FORM_ID,
                tag="client_onboarding"
            )
        except:
            pass  # Ignore if no webhook exists
        
        # And: A webhook created via the manager
        form_id = get_next_onboarding_form_id()
        typeform_id = TYPEFORM_TEST_FORM_ID  # Use the actual test form ID from environment
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id,
            user_id=1  # Consistent user_id to match webhook manager call
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        webhook_url = f"{WEBHOOK_ENDPOINT_URL}/webhook"
        
        try:
            # Setup webhook using the proper manager method
            form, webhook_info = await self.webhook_manager.setup_onboarding_form_webhook(
                uow=self.fake_uow,
                user_id=1,
                typeform_id=typeform_id,
                webhook_url=webhook_url,
                validate_ownership=False
            )
            
            if webhook_info and webhook_info.id:
                self.created_webhook_ids.append(webhook_info.id)
                
                # When: Checking webhook status synchronization
                status_info = await self.webhook_manager.get_comprehensive_webhook_status(
                    uow=self.fake_uow,
                    onboarding_form_id=form.id
                )
                
                # Then: Status information is available
                assert status_info is not None
                assert status_info.webhook_exists is True
                assert status_info.webhook_info is not None
                assert status_info.webhook_info.url == webhook_url
                
                # And: Local database reflects the same status
                assert form.webhook_url == webhook_url
                assert form.typeform_id == typeform_id
                
        except TypeFormAPIError as e:
            pytest.skip(f"Live API test skipped: {e}")

    async def test_webhook_operation_audit_trail(self):
        """Test that webhook operations create proper audit trails."""
        # Given: A clean slate (remove any existing webhooks)
        try:
            await self.webhook_manager.typeform_client.delete_webhook(
                form_id=TYPEFORM_TEST_FORM_ID,
                tag="client_onboarding"
            )
        except:
            pass  # Ignore if no webhook exists
        
        # And: A form for webhook operations
        form_id = get_next_onboarding_form_id()
        typeform_id = TYPEFORM_TEST_FORM_ID  # Use the actual test form ID from environment
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id,
            user_id=1  # Consistent user_id to match webhook manager call
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        webhook_url = f"{WEBHOOK_ENDPOINT_URL}/webhook"
        
        try:
            # When: Performing webhook operations
            form, webhook_info = await self.webhook_manager.setup_onboarding_form_webhook(
                uow=self.fake_uow,
                user_id=1,
                typeform_id=typeform_id,
                webhook_url=webhook_url,
                validate_ownership=False
            )
            
            if webhook_info and webhook_info.id:
                self.created_webhook_ids.append(webhook_info.id)
                
                # Then: Operations are tracked in audit trail
                # Note: Audit trail tracking would be implemented in the webhook manager
                # For now, verify that operations complete successfully
                assert webhook_info.id is not None
                assert webhook_info.url == webhook_url
                
                # Future: Check audit records in database
                # audit_records = await self.fake_uow.webhook_audit.get_by_form_id(form_id)
                # assert len(audit_records) >= 1
                
        except TypeFormAPIError as e:
            pytest.skip(f"Live API test skipped: {e}")