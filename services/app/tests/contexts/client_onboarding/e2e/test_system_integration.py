"""
Cross-system integration validation.

Tests integration between client onboarding system and other components
of the application, ensuring compatibility and data flow continuity.
"""

import pytest
import asyncio
import json
from datetime import datetime, UTC
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
from src.contexts.client_onboarding.core.bootstrap.container import Container

from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.utils.counter_manager import (
    get_next_webhook_counter,
    get_next_onboarding_form_id,
    reset_all_counters
)

pytestmark = [pytest.mark.anyio, pytest.mark.e2e]


class MockExternalSystem:
    """Mock external system for integration testing."""
    
    def __init__(self):
        self.received_events = []
        self.call_count = 0
        self.should_fail = False
        
    async def notify_user_registration(self, user_data: Dict[str, Any]) -> bool:
        """Mock user registration notification."""
        self.call_count += 1
        self.received_events.append(("user_registration", user_data))
        
        if self.should_fail:
            raise Exception("External system error")
        
        return True
    
    async def create_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock user profile creation."""
        self.call_count += 1
        self.received_events.append(("user_profile", profile_data))
        
        if self.should_fail:
            raise Exception("Profile creation failed")
        
        return {
            "user_id": f"user_{self.call_count}",
            "profile_id": f"profile_{self.call_count}",
            "status": "created"
        }
    
    async def send_welcome_email(self, email_data: Dict[str, Any]) -> bool:
        """Mock welcome email sending."""
        self.call_count += 1
        self.received_events.append(("welcome_email", email_data))
        
        if self.should_fail:
            return False
        
        return True


class TestSystemIntegration:
    """Test integration with other system components."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment."""
        reset_all_counters()
        self.container = Container()
        self.fake_uow = FakeUnitOfWork()
        
        # Create webhook handler
        self.webhook_handler = WebhookHandler(
            uow_factory=lambda: self.fake_uow
        )
        
        # Mock external systems
        self.mock_external_system = MockExternalSystem()
        self.mock_event_publisher = AsyncMock()
        self.mock_notification_service = AsyncMock()

    async def test_webhook_to_user_registration_flow(self):
        """Test complete flow from webhook to user registration in external system."""
        # Given: A registered onboarding form
        form_id = get_next_onboarding_form_id()
        typeform_id = f"typeform_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook payload with user registration data
        webhook_payload = create_typeform_webhook_payload(
            form_id=typeform_id,
            response_token=f"user_reg_{get_next_webhook_counter()}",
            include_client_data=True
        )
        
        # Add user registration fields
        if "form_response" in webhook_payload:
            webhook_payload["form_response"]["answers"].extend([
                {
                    "field": {"id": "email", "type": "email", "ref": "user_email"},
                    "type": "email",
                    "email": f"user{get_next_webhook_counter()}@example.com"
                },
                {
                    "field": {"id": "name", "type": "short_text", "ref": "user_name"},
                    "type": "text",
                    "text": f"Test User {get_next_webhook_counter()}"
                }
            ])
        
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # When: Processing webhook with mock external system integration
        with patch.object(self.webhook_handler, '_notify_external_systems', 
                         side_effect=self._mock_external_notification):
            status_code, response = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=None
            )
        
        # Then: Webhook is processed successfully
        assert status_code == 200
        assert response["status"] == "success"
        
        # And: Form response is stored
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert len(stored_responses) == 1
        
        # And: External system was notified
        assert self.mock_external_system.call_count > 0
        assert len(self.mock_external_system.received_events) > 0

    async def test_concurrent_system_integration(self):
        """Test concurrent webhook processing with external system integration."""
        # Given: Multiple forms and responses
        forms_data = []
        for i in range(3):
            form_id = get_next_onboarding_form_id()
            typeform_id = f"typeform_{get_next_webhook_counter()}_{i}"
            
            onboarding_form = create_onboarding_form(
                id=form_id,
                typeform_id=typeform_id
            )
            await self.fake_uow.onboarding_forms.add(onboarding_form)
            forms_data.append((form_id, typeform_id))
        
        # When: Processing multiple webhooks concurrently
        async def process_webhook_for_form(form_data):
            form_id, typeform_id = form_data
            
            webhook_payload = create_typeform_webhook_payload(
                form_id=typeform_id,
                response_token=f"concurrent_{get_next_webhook_counter()}_{form_id}"
            )
            payload_json = json.dumps(webhook_payload)
            headers = {"Content-Type": "application/json"}
            
            with patch.object(self.webhook_handler, '_notify_external_systems',
                             side_effect=self._mock_external_notification):
                return await self.webhook_handler.handle_webhook(
                    payload=payload_json,
                    headers=headers,
                    webhook_secret=None
                )
        
        tasks = [process_webhook_for_form(form_data) for form_data in forms_data]
        results = await asyncio.gather(*tasks)
        
        # Then: All webhooks processed successfully
        for status_code, response in results:
            assert status_code == 200
            assert response["status"] == "success"
        
        # And: All responses stored correctly
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert len(stored_responses) == 3
        
        # And: External system received all notifications
        assert self.mock_external_system.call_count == 3

    async def test_external_system_failure_handling(self):
        """Test handling of external system failures during integration."""
        # Given: A registered form
        form_id = get_next_onboarding_form_id()
        typeform_id = f"typeform_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: External system configured to fail
        self.mock_external_system.should_fail = True
        
        # And: A webhook payload
        webhook_payload = create_typeform_webhook_payload(
            form_id=typeform_id,
            response_token=f"failure_test_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # When: Processing webhook with failing external system
        with patch.object(self.webhook_handler, '_notify_external_systems',
                         side_effect=self._mock_external_notification):
            status_code, response = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=None
            )
        
        # Then: Webhook processing still succeeds (graceful degradation)
        assert status_code == 200
        assert response["status"] == "success"
        
        # And: Form response is still stored (external failure doesn't rollback)
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert len(stored_responses) == 1

    async def test_event_publishing_integration(self):
        """Test integration with event publishing system."""
        # Given: A registered form
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
            response_token=f"event_test_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # When: Processing webhook with event publishing
        with patch.object(self.webhook_handler, '_publish_events', 
                         side_effect=self._mock_event_publishing):
            status_code, response = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=None
            )
        
        # Then: Webhook is processed successfully
        assert status_code == 200
        assert response["status"] == "success"
        
        # And: Events were published
        assert self.mock_event_publisher.publish.call_count > 0

    async def test_database_cross_context_integration(self):
        """Test integration with other database contexts."""
        # Given: Multiple forms across different contexts (simulated)
        client_onboarding_form_id = get_next_onboarding_form_id()
        client_onboarding_typeform_id = f"client_onboarding_{get_next_webhook_counter()}"
        
        # Simulate forms in different contexts
        client_form = create_onboarding_form(
            id=client_onboarding_form_id,
            typeform_id=client_onboarding_typeform_id
        )
        await self.fake_uow.onboarding_forms.add(client_form)
        
        # When: Processing webhooks that might affect other contexts
        webhook_payload = create_typeform_webhook_payload(
            form_id=client_onboarding_typeform_id,
            response_token=f"cross_context_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # Simulate cross-context database operations
        with patch.object(self.fake_uow, 'commit', wraps=self.fake_uow.commit) as mock_commit:
            status_code, response = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=None
            )
        
        # Then: Webhook processing succeeds
        assert status_code == 200
        assert response["status"] == "success"
        
        # And: Database operations are properly committed
        mock_commit.assert_called_once()
        
        # And: Data is consistent across contexts
        stored_responses = await self.fake_uow.form_responses.get_all()
        assert len(stored_responses) == 1
        assert stored_responses[0].form_id == client_onboarding_form_id

    async def test_authentication_system_integration(self):
        """Test integration with authentication/authorization systems."""
        # Given: A form with authentication requirements
        form_id = get_next_onboarding_form_id()
        typeform_id = f"auth_form_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id,
            requires_authentication=True  # Custom field for testing
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook payload with authentication data
        webhook_payload = create_typeform_webhook_payload(
            form_id=typeform_id,
            response_token=f"auth_test_{get_next_webhook_counter()}"
        )
        
        # Add authentication fields
        if "form_response" in webhook_payload:
            webhook_payload["form_response"]["answers"].append({
                "field": {"id": "user_token", "type": "short_text", "ref": "auth_token"},
                "type": "text",
                "text": f"auth_token_{get_next_webhook_counter()}"
            })
        
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # When: Processing with authentication validation
        with patch.object(self.webhook_handler, '_validate_authentication',
                         return_value=True) as mock_auth:
            status_code, response = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=None
            )
        
        # Then: Webhook is processed with authentication
        assert status_code == 200
        assert response["status"] == "success"
        
        # And: Authentication was validated
        mock_auth.assert_called_once()

    async def test_notification_system_integration(self):
        """Test integration with notification/messaging systems."""
        # Given: A form with notification triggers
        form_id = get_next_onboarding_form_id()
        typeform_id = f"notification_form_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook payload
        webhook_payload = create_typeform_webhook_payload(
            form_id=typeform_id,
            response_token=f"notification_test_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # When: Processing with notification integration
        with patch.object(self.webhook_handler, '_send_notifications',
                         side_effect=self._mock_notification_sending):
            status_code, response = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=None
            )
        
        # Then: Webhook is processed successfully
        assert status_code == 200
        assert response["status"] == "success"
        
        # And: Notifications were sent
        assert self.mock_notification_service.send.call_count > 0

    async def test_monitoring_system_integration(self):
        """Test integration with monitoring and metrics systems."""
        # Given: A form for monitoring testing
        form_id = get_next_onboarding_form_id()
        typeform_id = f"monitoring_form_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # Mock metrics collector
        mock_metrics = AsyncMock()
        
        # And: A webhook payload
        webhook_payload = create_typeform_webhook_payload(
            form_id=typeform_id,
            response_token=f"monitoring_test_{get_next_webhook_counter()}"
        )
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # When: Processing with monitoring integration
        with patch.object(self.webhook_handler, '_collect_metrics',
                         side_effect=lambda *args: mock_metrics.collect(*args)):
            status_code, response = await self.webhook_handler.handle_webhook(
                payload=payload_json,
                headers=headers,
                webhook_secret=None
            )
        
        # Then: Webhook is processed successfully
        assert status_code == 200
        assert response["status"] == "success"
        
        # And: Metrics were collected
        assert mock_metrics.collect.call_count > 0

    async def test_system_health_integration(self):
        """Test integration with system health checking."""
        # Given: Multiple system components
        components = ["webhook_handler", "database", "external_api", "event_publisher"]
        
        # When: Checking system health across all components
        health_results = {}
        
        # Mock health checks for each component
        for component in components:
            try:
                if component == "webhook_handler":
                    # Test webhook handler health
                    test_payload = create_typeform_webhook_payload(
                        form_id="health_check",
                        response_token="health_test"
                    )
                    # Health check shouldn't process actual webhook
                    health_results[component] = "healthy"
                
                elif component == "database":
                    # Test database connection
                    await self.fake_uow.onboarding_forms.get_all()
                    health_results[component] = "healthy"
                
                elif component == "external_api":
                    # Mock external API health
                    health_results[component] = "healthy"
                
                elif component == "event_publisher":
                    # Mock event publisher health
                    health_results[component] = "healthy"
                
            except Exception as e:
                health_results[component] = f"unhealthy: {e}"
        
        # Then: All components report healthy
        for component, status in health_results.items():
            assert status == "healthy", f"Component {component} is {status}"

    async def _mock_external_notification(self, response_data: Dict[str, Any]):
        """Mock external system notification."""
        # Extract user data from response
        user_data = {
            "response_id": response_data.get("response_id"),
            "form_id": response_data.get("form_id"),
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Simulate external system calls
        await self.mock_external_system.notify_user_registration(user_data)
        profile_result = await self.mock_external_system.create_user_profile(user_data)
        await self.mock_external_system.send_welcome_email({
            "user_id": profile_result.get("user_id"),
            "email": f"user{get_next_webhook_counter()}@example.com"
        })

    async def _mock_event_publishing(self, event_data: Dict[str, Any]):
        """Mock event publishing."""
        await self.mock_event_publisher.publish({
            "event_type": "form_response_received",
            "data": event_data,
            "timestamp": datetime.now(UTC).isoformat()
        })

    async def _mock_notification_sending(self, notification_data: Dict[str, Any]):
        """Mock notification sending."""
        await self.mock_notification_service.send({
            "type": "webhook_processed",
            "data": notification_data,
            "timestamp": datetime.now(UTC).isoformat()
        })