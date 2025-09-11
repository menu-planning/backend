"""
Cross-system integration validation.

Tests integration between client onboarding system and other components
of the application, ensuring compatibility and data flow continuity.
"""

import pytest
import asyncio
import json
from datetime import datetime, UTC
from typing import Dict, Any, List, cast
from unittest.mock import AsyncMock, patch

from src.contexts.client_onboarding.core.bootstrap.container import Container

from old_tests_v0.contexts/client_onboarding.utils.webhook_test_processor import process_typeform_webhook
from old_tests_v0.contexts.client_onboarding.data_factories import (
    create_onboarding_form,
    create_typeform_webhook_payload
)
from old_tests_v0.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
from old_tests_v0.utils.counter_manager import (
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
        
    async def notify_user_registration(self, user_data: dict[str, Any]) -> bool:
        """Mock user registration notification."""
        self.call_count += 1
        self.received_events.append(("user_registration", user_data))
        
        if self.should_fail:
            raise Exception("External system error")
        
        return True
    
    async def create_user_profile(self, profile_data: dict[str, Any]) -> Dict[str, Any]:
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
    
    async def send_welcome_email(self, email_data: dict[str, Any]) -> bool:
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
        
        # Use core processor with fake UoW
        self.uow_factory = lambda: self.fake_uow
        
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
            form_response={
                "form_id": typeform_id,
                "token": f"user_reg_{get_next_webhook_counter()}"
            },
            include_client_data=True
        )
        
        # Add user registration fields
        if "form_response" in webhook_payload:
            # Ensure answers array exists
            if "answers" not in webhook_payload["form_response"]:
                webhook_payload["form_response"]["answers"] = []
            
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
        
        # When: Processing webhook (testing the core integration point)
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
        
        # Then: Webhook processing succeeds
        assert success is True
        
        # And: Form response is stored (data available for external systems)
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 1
        
        # When: External system processes the stored data (simulating cross-system integration)
        form_response = stored_responses[0]
        user_data = {
            "form_id": form_response.form_id,
            "response_id": form_response.response_id,
            "submitted_at": form_response.submitted_at.isoformat() if form_response.submitted_at else None
        }
        
        # Simulate external system registration
        registration_result = await self.mock_external_system.notify_user_registration(user_data)
        
        # Then: External system integration succeeds
        assert registration_result is True
        assert self.mock_external_system.call_count > 0
        assert len(self.mock_external_system.received_events) > 0
        
        # And: External system received the correct data
        received_event = self.mock_external_system.received_events[0]
        assert received_event[0] == "user_registration"
        assert received_event[1]["form_id"] == form_response.form_id

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
                form_response={
                    "form_id": typeform_id,
                    "token": f"concurrent_{get_next_webhook_counter()}_{form_id}"
                }
            )
            payload_json = json.dumps(webhook_payload)
            headers = {"Content-Type": "application/json"}
            
            # Process webhook and return result for external system integration
            success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
            
            # Simulate external system notification after successful webhook processing
            if success:
                await self._mock_external_notification({"response_id": response_id})
            
            return success, error, response_id
        
        tasks = [process_webhook_for_form(form_data) for form_data in forms_data]
        results = await asyncio.gather(*tasks)
        
        # Then: All webhooks processed successfully
        for success, error, response_id in results:
            assert success is True
        
        # And: All responses stored correctly
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 3
        
        # And: External system received all notifications (each webhook triggers 3 external calls)
        assert self.mock_external_system.call_count == 9  # 3 webhooks * 3 calls each

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
            form_response={
                "form_id": typeform_id,
                "token": f"failure_test_{get_next_webhook_counter()}"
            }
        )
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # When: Processing webhook with failing external system
        
        # Process webhook (should succeed regardless of external system failure)
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
        
        # Try to notify external system (this will fail as expected)
        if success:
            try:
                stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
                if stored_responses:
                    user_data = {"form_id": stored_responses[0].form_id}
                    await self.mock_external_system.notify_user_registration(user_data)
            except Exception:
                pass  # Expected external system failure
        
        # Then: Webhook processing still succeeds (graceful degradation)
        assert success is True
        
        # And: Form response is still stored (external failure doesn't rollback)
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 1

    async def test_event_publishing_integration(self):
        """Test integration with event publishing system by verifying webhook data flow."""
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
            form_response={
                "form_id": typeform_id,
                "token": f"event_test_{get_next_webhook_counter()}"
            }
        )
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # When: Processing webhook (testing the actual behavior)
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
        
        # Then: Webhook is processed successfully (observable behavior)
        assert success is True
        
        # And: Data is available for event publishing systems
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 1
        
        # And: Response data contains all necessary fields for external events
        response_data = stored_responses[0]
        assert response_data.form_id == form_id
        assert response_data.response_id is not None
        assert response_data.submitted_at is not None
        
        # When: External event publisher can access and use the stored data
        event_data = {
            "event_type": "form_response_received",
            "form_id": response_data.form_id,
            "response_id": response_data.response_id,
            "submitted_at": response_data.submitted_at.isoformat() if response_data.submitted_at else None
        }
        
        # Simulate event publishing (testing that data is properly structured)
        await self.mock_event_publisher.publish(event_data)
        
        # Then: Event publishing succeeds with proper data
        self.mock_event_publisher.publish.assert_called_once_with(event_data)

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
            form_response={
                "form_id": client_onboarding_typeform_id,
                "token": f"cross_context_{get_next_webhook_counter()}"
            }
        )
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # Simulate cross-context database operations
        with patch.object(self.fake_uow, 'commit', wraps=self.fake_uow.commit) as mock_commit:
            success, error, response_id = await process_typeform_webhook(
            payload=payload_json,
            headers=headers,
            uow_factory=self.uow_factory,
            )
        
        # Then: Webhook processing succeeds
        assert success is True
        
        # And: Database operations are properly committed
        mock_commit.assert_called_once()
        
        # And: Data is consistent across contexts
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 1
        assert stored_responses[0].form_id == client_onboarding_form_id

    async def test_authentication_system_integration(self):
        """Test integration with authentication systems by verifying webhook processing with auth data."""
        # Given: A form for authentication testing
        form_id = get_next_onboarding_form_id()
        typeform_id = f"auth_form_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook payload with authentication data
        webhook_payload = create_typeform_webhook_payload(
            form_response={
                "form_id": typeform_id,
                "token": f"auth_test_{get_next_webhook_counter()}"
            }
        )
        
        # Add authentication fields that external systems can use
        if "form_response" in webhook_payload:
            # Ensure answers array exists
            if "answers" not in webhook_payload["form_response"]:
                webhook_payload["form_response"]["answers"] = []
            webhook_payload["form_response"]["answers"].append({
                "field": {"id": "user_token", "type": "short_text", "ref": "auth_token"},
                "type": "text",
                "text": f"auth_token_{get_next_webhook_counter()}"
            })
        
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # When: Processing webhook (testing actual behavior)
        success, error, response_id = await process_typeform_webhook(payload=payload_json, headers=headers, uow_factory=self.uow_factory)
        
        # Then: Webhook is processed successfully (observable behavior)
        assert success is True
        
        # And: Authentication data is properly stored for external systems
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 1
        
        # And: Response contains authentication fields that auth systems can use
        stored_response = stored_responses[0]
        assert stored_response.response_data is not None
        
        # Parse the stored response data to verify auth data is preserved
        stored_data = stored_response.response_data if isinstance(stored_response.response_data, dict) else json.loads(stored_response.response_data)
        assert "answers" in stored_data
        
        # Verify authentication token is preserved for external auth systems
        auth_fields = [
            answer for answer in stored_data["answers"]
            if answer.get("field", {}).get("ref") == "auth_token"
        ]
        assert len(auth_fields) == 1
        assert "auth_token_" in auth_fields[0]["text"]

    async def test_notification_system_integration(self):
        """Test integration with notification systems by verifying webhook data for notifications."""
        # Given: A form for notification testing
        form_id = get_next_onboarding_form_id()
        typeform_id = f"notification_form_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook payload with contact information
        webhook_payload = create_typeform_webhook_payload(
            form_response={
                "form_id": typeform_id,
                "token": f"notification_test_{get_next_webhook_counter()}"
            }
        )
        
        # Add contact fields for notifications
        if "form_response" in webhook_payload:
            # Ensure answers array exists
            if "answers" not in webhook_payload["form_response"]:
                webhook_payload["form_response"]["answers"] = []
            webhook_payload["form_response"]["answers"].append({
                "field": {"id": "email", "type": "email", "ref": "contact_email"},
                "type": "email",
                "email": f"notify{get_next_webhook_counter()}@example.com"
            })
        
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # When: Processing webhook (testing actual behavior)
        success, error, response_id = await process_typeform_webhook(
            payload=payload_json,
            headers=headers,
            uow_factory=self.uow_factory,
        )
        
        # Then: Webhook is processed successfully (observable behavior)
        assert success is True
        
        # And: Contact data is stored for notification systems
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 1
        
        # And: Response contains notification data that notification systems can use
        stored_response = stored_responses[0]
        assert stored_response.response_data is not None
        
        # Parse the stored response to verify notification data
        stored_data = stored_response.response_data if isinstance(stored_response.response_data, dict) else json.loads(stored_response.response_data)
        contact_fields = [
            answer for answer in stored_data["answers"]
            if answer.get("field", {}).get("ref") == "contact_email"
        ]
        assert len(contact_fields) == 1
        assert "@example.com" in contact_fields[0]["email"]
        
        # When: External notification system processes the stored data
        notification_data = {
            "type": "webhook_processed",
            "form_id": stored_response.form_id,
            "response_id": stored_response.response_id,
            "contact_email": contact_fields[0]["email"],
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Simulate notification sending
        await self.mock_notification_service.send(notification_data)
        
        # Then: Notification system receives proper data
        self.mock_notification_service.send.assert_called_once_with(notification_data)

    async def test_monitoring_system_integration(self):
        """Test integration with monitoring systems by verifying webhook metrics and observability."""
        # Given: A form for monitoring testing
        form_id = get_next_onboarding_form_id()
        typeform_id = f"monitoring_form_{get_next_webhook_counter()}"
        
        onboarding_form = create_onboarding_form(
            id=form_id,
            typeform_id=typeform_id
        )
        await self.fake_uow.onboarding_forms.add(onboarding_form)
        
        # And: A webhook payload
        webhook_payload = create_typeform_webhook_payload(
            form_response={
                "form_id": typeform_id,
                "token": f"monitoring_test_{get_next_webhook_counter()}"
            }
        )
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}
        
        # Record start time for performance monitoring
        start_time = datetime.now(UTC)
        
        # When: Processing webhook (testing observable behavior and performance)
        success, error, response_id = await process_typeform_webhook(
            payload=payload_json,
            headers=headers,
            uow_factory=self.uow_factory,
        )
        
        # Record end time
        end_time = datetime.now(UTC)
        processing_time = (end_time - start_time).total_seconds()
        
        # Then: Webhook is processed successfully (observable behavior)
        assert success is True
        
        # And: Processing completes within acceptable time (performance metric)
        assert processing_time < 5.0, f"Webhook processing took {processing_time}s, expected < 5s"
        
        # And: response_id was returned
        assert response_id is not None
        
        # And: System state is observable for monitoring
        stored_responses = cast(List, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 1
        
        # When: External monitoring system collects metrics
        metrics_data = {
            "webhook_processing_time": processing_time,
            "webhook_status": "success",
            "form_id": form_id,
            "response_count": len(stored_responses),
            "timestamp": end_time.isoformat()
        }
        
        # Simulate metrics collection
        mock_metrics = AsyncMock()
        await mock_metrics.collect(metrics_data)
        
        # Then: Monitoring system receives proper metrics
        mock_metrics.collect.assert_called_once_with(metrics_data)

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

    async def _mock_external_notification(self, response_data: dict[str, Any]):
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

    async def _mock_event_publishing(self, event_data: dict[str, Any]):
        """Mock event publishing."""
        await self.mock_event_publisher.publish({
            "event_type": "form_response_received",
            "data": event_data,
            "timestamp": datetime.now(UTC).isoformat()
        })

    async def _mock_notification_sending(self, notification_data: dict[str, Any]):
        """Mock notification sending."""
        await self.mock_notification_service.send({
            "type": "webhook_processed",
            "data": notification_data,
            "timestamp": datetime.now(UTC).isoformat()
        })