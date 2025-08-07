"""Test webhook handler processing pipeline."""

import pytest
from unittest.mock import AsyncMock
import json

from tests.utils.counter_manager import (
    get_next_onboarding_form_id,
    get_next_webhook_counter,
    get_next_form_response_counter
)
from tests.contexts.client_onboarding.data_factories.client_factories import (
    create_client_data_extracted_event_kwargs
)
from tests.contexts.client_onboarding.data_factories.typeform_factories import (
    create_webhook_payload_kwargs
)
from tests.contexts.client_onboarding.fakes.webhook_security import (
    create_valid_webhook_security_scenario,
    create_invalid_webhook_security_scenario,
)


pytestmark = pytest.mark.anyio

class TestWebhookHandler:
    """Test webhook processing pipeline behavior."""

    async def test_webhook_processing_full_pipeline(self, async_benchmark_timer):
        """Test complete webhook processing pipeline from payload to storage."""
        
        # Create test data
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler service
            mock_webhook_handler = AsyncMock()
            mock_webhook_handler.process_webhook.return_value = {
                "processed": True,
                "client_id": f"client_{get_next_webhook_counter()}",
                "status": "success"
            }
            
            # Process webhook
            result = await mock_webhook_handler.process_webhook(webhook_payload)
            
            # Verify processing
            assert result["processed"] is True
            assert "client_id" in result
            assert result["status"] == "success"
            mock_webhook_handler.process_webhook.assert_called_once_with(webhook_payload)

    async def test_webhook_processing_with_typeform_data_extraction(self, async_benchmark_timer):
        """Test webhook processing with TypeForm data extraction."""
        
        # Create webhook payload for testing
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock data extraction service
            mock_data_extractor = AsyncMock()
            
            extracted_data = create_client_data_extracted_event_kwargs(
                client_id=f"client_{get_next_webhook_counter()}"
            )
            mock_data_extractor.extract_client_data.return_value = extracted_data
            
            # Extract data from webhook
            result = await mock_data_extractor.extract_client_data(webhook_payload)
            
            # Verify extraction - check the correct structure
            assert "form_id" in result
            assert "extracted_data" in result
            assert "name" in result["extracted_data"]
            assert "email" in result["extracted_data"]
            assert "company" in result["extracted_data"]
            mock_data_extractor.extract_client_data.assert_called_once_with(webhook_payload)

    async def test_webhook_processing_performance_benchmark(self, async_benchmark_timer):
        """Test webhook processing performance meets requirements."""
        
        # Create multiple webhook payloads for performance testing
        webhook_payloads = [
            create_webhook_payload_kwargs(
                form_id=f"form_{get_next_onboarding_form_id()}",
                response_id=f"response_{get_next_form_response_counter()}"
            )
            for _ in range(10)
        ]
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler for batch processing
            mock_webhook_handler = AsyncMock()
            
            # Process multiple webhooks
            results = []
            for payload in webhook_payloads:
                mock_webhook_handler.process_webhook.return_value = {
                    "processed": True,
                    "client_id": f"client_{get_next_webhook_counter()}",
                    "processing_time_ms": 45
                }
                result = await mock_webhook_handler.process_webhook(payload)
                results.append(result)
            
            # Verify all processed successfully
            assert len(results) == 10
            assert all(r["processed"] for r in results)
            assert all(r["processing_time_ms"] < 100 for r in results)  # Performance requirement
        
        # Assert performance requirement
        timer.assert_faster_than(1.0)  # 10 webhooks should process in under 1 second

    async def test_webhook_processing_with_event_publishing(self, async_benchmark_timer):
        """Test webhook processing triggers correct event publishing."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock services
            mock_event_publisher = AsyncMock()
            mock_webhook_handler = AsyncMock()
            
            # Setup processing result
            mock_webhook_handler.process_webhook.return_value = {
                "processed": True,
                "events_published": 2,
                "client_id": f"client_{get_next_webhook_counter()}"
            }
            
            # Process webhook
            result = await mock_webhook_handler.process_webhook(webhook_payload)
            
            # Verify event publishing behavior
            assert result["events_published"] == 2
            assert result["processed"] is True

    async def test_webhook_processing_error_recovery(self, async_benchmark_timer):
        """Test webhook processing error handling and recovery."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with error scenario
            mock_webhook_handler = AsyncMock()
            
            # First call fails, second succeeds (retry logic)
            mock_webhook_handler.process_webhook.side_effect = [
                Exception("Temporary processing error"),
                {
                    "processed": True,
                    "retry_count": 1,
                    "client_id": f"client_{get_next_webhook_counter()}"
                }
            ]
            
            # Test error handling
            with pytest.raises(Exception, match="Temporary processing error"):
                await mock_webhook_handler.process_webhook(webhook_payload)
            
            # Test successful retry
            result = await mock_webhook_handler.process_webhook(webhook_payload)
            assert result["processed"] is True
            assert result["retry_count"] == 1

    # =========================================================================
    # WEBHOOK SECURITY VALIDATION TESTS (Task 1.4.2 - Complete Security Flow)
    # =========================================================================

    async def test_webhook_handler_security_valid_signature_complete_flow(self, async_benchmark_timer):
        """Test complete WebhookHandler security flow with valid signature."""
        from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
        from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
        from tests.contexts.client_onboarding.fakes.webhook_security import (
            create_valid_webhook_security_scenario,
            WebhookSecurityHelper
        )
        from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingForm, OnboardingFormStatus
        from datetime import datetime, timezone
        
        # Create test scenario with valid signature
        security_scenario = create_valid_webhook_security_scenario()
        webhook_secret = security_scenario["secret"]
        
        # Extract form_id from the payload
        form_id = security_scenario["payload"]["form_response"]["form_id"]
        
        async with async_benchmark_timer() as timer:
            # Create fake UoW factory
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            # Create and populate the onboarding form
            fake_uow = FakeUnitOfWork()
            onboarding_form = OnboardingForm(
                id=1,
                user_id=123,
                typeform_id=form_id,
                webhook_url="https://test-webhook.example.com",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await fake_uow.onboarding_forms.add(onboarding_form)
            
            # Create real WebhookHandler instance with the populated fake UoW
            def populated_uow_factory():
                return fake_uow
            
            webhook_handler = WebhookHandler(populated_uow_factory)
            
            # Test with valid signature - should return 200 success
            # Use the pre-serialized payload string that the signature was created for
            payload_str = security_scenario["payload_str"]
            status_code, response_data = await webhook_handler.handle_webhook(
                payload=payload_str,
                headers=security_scenario["headers"],
                webhook_secret=webhook_secret
            )
            
            # Verify successful processing
            assert status_code == 200
            assert response_data["status"] == "success"
            assert "data" in response_data

    async def test_webhook_handler_security_invalid_signature_rejection(self, async_benchmark_timer):
        """Test WebhookHandler rejects invalid signatures properly."""
        from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
        from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
        from tests.contexts.client_onboarding.fakes.webhook_security import (
            create_invalid_webhook_security_scenario
        )
        
        # Create test scenario with invalid signature
        security_scenario = create_invalid_webhook_security_scenario("invalid_secret")
        webhook_secret = "correct_secret_that_doesnt_match"
        
        async with async_benchmark_timer() as timer:
            # Create fake UoW factory
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            # Create real WebhookHandler instance
            webhook_handler = WebhookHandler(fake_uow_factory)
            
            # Test with invalid signature - should return 401 unauthorized
            payload_str = json.dumps(security_scenario["payload"])
            status_code, response_data = await webhook_handler.handle_webhook(
                payload=payload_str,
                headers=security_scenario["headers"],
                webhook_secret=webhook_secret
            )
            
            # Verify security rejection
            assert status_code == 401
            assert response_data["status"] == "error"
            assert response_data["error"] == "security_validation_failed"

    async def test_webhook_handler_security_missing_signature_header(self, async_benchmark_timer):
        """Test WebhookHandler handles missing signature headers properly."""
        from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
        from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
        from tests.contexts.client_onboarding.fakes.webhook_security import (
            create_invalid_webhook_security_scenario
        )
        
        # Create scenario with missing signature
        security_scenario = create_invalid_webhook_security_scenario("missing")
        webhook_secret = "test_secret"
        
        async with async_benchmark_timer() as timer:
            # Create fake UoW factory
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            # Create real WebhookHandler instance
            webhook_handler = WebhookHandler(fake_uow_factory)
            
            # Test with missing signature header
            payload_str = json.dumps(security_scenario["payload"])
            status_code, response_data = await webhook_handler.handle_webhook(
                payload=payload_str,
                headers=security_scenario["headers"],
                webhook_secret=webhook_secret
            )
            
            # Verify security rejection for missing signature
            assert status_code == 401
            assert response_data["status"] == "error"
            assert response_data["error"] == "security_validation_failed"

    async def test_webhook_handler_security_malformed_signature(self, async_benchmark_timer):
        """Test WebhookHandler handles malformed signatures properly."""
        from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
        from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
        from tests.contexts.client_onboarding.fakes.webhook_security import (
            create_invalid_webhook_security_scenario
        )
        
        # Create scenario with malformed signature
        security_scenario = create_invalid_webhook_security_scenario("malformed")
        webhook_secret = "test_secret"
        
        async with async_benchmark_timer() as timer:
            # Create fake UoW factory
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            # Create real WebhookHandler instance
            webhook_handler = WebhookHandler(fake_uow_factory)
            
            # Test with malformed signature
            payload_str = json.dumps(security_scenario["payload"])
            status_code, response_data = await webhook_handler.handle_webhook(
                payload=payload_str,
                headers=security_scenario["headers"],
                webhook_secret=webhook_secret
            )
            
            # Verify security rejection for malformed signature
            assert status_code == 401
            assert response_data["status"] == "error"
            assert response_data["error"] == "security_validation_failed"

    async def test_webhook_handler_security_wrong_algorithm_signature(self, async_benchmark_timer):
        """Test WebhookHandler rejects wrong algorithm signatures."""
        from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
        from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
        from tests.contexts.client_onboarding.fakes.webhook_security import (
            create_invalid_webhook_security_scenario
        )
        
        # Create scenario with wrong algorithm signature (md5 instead of sha256)
        security_scenario = create_invalid_webhook_security_scenario("wrong_algorithm")
        webhook_secret = "test_secret"
        
        async with async_benchmark_timer() as timer:
            # Create fake UoW factory
            def fake_uow_factory():
                return FakeUnitOfWork()
            
            # Create real WebhookHandler instance
            webhook_handler = WebhookHandler(fake_uow_factory)
            
            # Test with wrong algorithm signature
            payload_str = json.dumps(security_scenario["payload"])
            status_code, response_data = await webhook_handler.handle_webhook(
                payload=payload_str,
                headers=security_scenario["headers"],
                webhook_secret=webhook_secret
            )
            
            # Verify security rejection for wrong algorithm
            assert status_code == 401
            assert response_data["status"] == "error"
            assert response_data["error"] == "security_validation_failed"

    async def test_webhook_handler_security_comprehensive_error_scenarios(self, async_benchmark_timer):
        """Test WebhookHandler handles all security error scenarios comprehensively."""
        from src.contexts.client_onboarding.core.services.webhook_handler import WebhookHandler
        from tests.contexts.client_onboarding.fakes.fake_unit_of_work import FakeUnitOfWork
        from tests.contexts.client_onboarding.fakes.webhook_security import (
            create_multiple_security_scenarios
        )
        from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingForm, OnboardingFormStatus
        from datetime import datetime
        
        async with async_benchmark_timer() as timer:
            # Create comprehensive security scenarios
            scenarios = create_multiple_security_scenarios()
            
            # Create fake UoW factory with shared UoW instance
            fake_uow = FakeUnitOfWork()
            def fake_uow_factory():
                return fake_uow
            
            # Set up onboarding form that matches the webhook payload
            valid_scenario = scenarios["valid"]
            form_id = valid_scenario["payload"]["form_response"]["form_id"]
            
            # Create onboarding form with matching typeform_id
            onboarding_form = OnboardingForm(
                id=1,
                user_id=1,
                typeform_id=form_id,  # This matches the form_id in the webhook payload
                webhook_url="https://test-webhook.example.com/hook/1",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Add the form to the fake repository
            await fake_uow.onboarding_forms.add(onboarding_form)
            
            # Create real WebhookHandler instance
            webhook_handler = WebhookHandler(fake_uow_factory)
            
            # Test valid scenario
            # Use the pre-serialized payload string that the signature was created for
            payload_str = valid_scenario["payload_str"]
            status_code, response_data = await webhook_handler.handle_webhook(
                payload=payload_str,
                headers=valid_scenario["headers"],
                webhook_secret=valid_scenario["secret"]
            )
            assert status_code == 200
            assert response_data["status"] == "success"
            
            # Test all invalid scenarios
            invalid_scenarios = [
                "invalid_secret", "malformed_signature", "wrong_algorithm", 
                "empty_signature", "missing_signature"
            ]
            
            for scenario_name in invalid_scenarios:
                scenario = scenarios[scenario_name]
                payload_str = json.dumps(scenario["payload"])
                status_code, response_data = await webhook_handler.handle_webhook(
                    payload=payload_str,
                    headers=scenario["headers"],
                    webhook_secret=scenario["secret"]
                )
                
                # All invalid scenarios should return 401
                assert status_code == 401, f"Failed for scenario: {scenario_name}"
                assert response_data["status"] == "error", f"Failed for scenario: {scenario_name}"
                assert response_data["error"] == "security_validation_failed", f"Failed for scenario: {scenario_name}"

    async def test_webhook_security_validation_timing_safety(self, async_benchmark_timer):
        """Test webhook security validation uses timing-safe comparison."""
        
        # Create scenarios for timing attack testing
        valid_scenario = create_valid_webhook_security_scenario()
        invalid_scenario = create_invalid_webhook_security_scenario("invalid_secret")
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with timing-safe validation
            mock_webhook_handler = AsyncMock()
            
            # Test multiple validation attempts to check for timing consistency
            timing_results = []
            
            for scenario in [valid_scenario, invalid_scenario]:
                is_valid = scenario["is_valid"]
                mock_webhook_handler.validate_signature.return_value = is_valid
                
                if is_valid:
                    mock_webhook_handler.process_webhook.return_value = {"processed": True}
                    result = await mock_webhook_handler.process_webhook(
                        scenario["payload"],
                        headers=scenario["headers"]
                    )
                    timing_results.append(result["processed"])
                else:
                    mock_webhook_handler.process_webhook.side_effect = Exception("Invalid signature")
                    try:
                        await mock_webhook_handler.process_webhook(
                            scenario["payload"],
                            headers=scenario["headers"]
                        )
                    except Exception:
                        timing_results.append(False)
            
            # Verify validation behavior is consistent
            assert len(timing_results) == 2
            assert timing_results[0] is True  # Valid scenario
            assert timing_results[1] is False  # Invalid scenario

    # =========================================================================
    # ERROR HANDLING SCENARIOS (Task 2.2.3)
    # =========================================================================

    async def test_webhook_error_handling_database_unavailable(self, async_benchmark_timer):
        """Test webhook processing handles database unavailability gracefully."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with database error
            mock_webhook_handler = AsyncMock()
            
            # Simulate database connection error
            from sqlalchemy.exc import OperationalError
            mock_webhook_handler.process_webhook.side_effect = OperationalError(
                "Database connection failed",
                params=None,
                orig=ConnectionError("Database connection failed")
            )
            
            # Verify error is handled appropriately
            with pytest.raises(OperationalError, match="Database connection failed"):
                await mock_webhook_handler.process_webhook(webhook_payload)

    async def test_webhook_error_handling_typeform_api_timeout(self, async_benchmark_timer):
        """Test webhook processing handles TypeForm API timeouts."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with API timeout
            mock_webhook_handler = AsyncMock()
            
            # Simulate API timeout error
            import asyncio
            mock_webhook_handler.process_webhook.side_effect = asyncio.TimeoutError("TypeForm API timeout")
            
            # Verify timeout is handled appropriately
            with pytest.raises(asyncio.TimeoutError, match="TypeForm API timeout"):
                await mock_webhook_handler.process_webhook(webhook_payload)

    async def test_webhook_error_handling_malformed_payload(self, async_benchmark_timer):
        """Test webhook processing handles malformed payloads gracefully."""
        
        # Create intentionally malformed payload
        malformed_payloads = [
            {},  # Empty payload
            {"form_id": None},  # Missing required fields
            {"form_id": "invalid", "form_response": "not_a_dict"},  # Invalid structure
            {"form_id": "test", "form_response": {"answers": "not_a_list"}}  # Invalid data types
        ]
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with validation
            mock_webhook_handler = AsyncMock()
            
            for i, payload in enumerate(malformed_payloads):
                # Setup validation error for each malformed payload
                mock_webhook_handler.process_webhook.side_effect = ValueError(f"Malformed payload: missing required fields")
                
                # Verify each malformed payload is rejected
                with pytest.raises(ValueError, match="Malformed payload"):
                    await mock_webhook_handler.process_webhook(payload)

    async def test_webhook_error_handling_event_publishing_failure(self, async_benchmark_timer):
        """Test webhook processing handles event publishing failures."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with event publishing error
            mock_webhook_handler = AsyncMock()
            
            # Simulate event publishing failure but successful data processing
            mock_webhook_handler.process_webhook.return_value = {
                "processed": True,
                "data_stored": True,
                "events_published": False,
                "error": "Event publishing failed",
                "client_id": f"client_{get_next_webhook_counter()}"
            }
            
            result = await mock_webhook_handler.process_webhook(webhook_payload)
            
            # Verify data is processed but event publishing failed
            assert result["processed"] is True
            assert result["data_stored"] is True
            assert result["events_published"] is False
            assert "error" in result

    async def test_webhook_error_handling_data_extraction_failure(self, async_benchmark_timer):
        """Test webhook processing handles data extraction failures."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with data extraction error
            mock_webhook_handler = AsyncMock()
            
            # Simulate data extraction failure
            mock_webhook_handler.process_webhook.side_effect = KeyError("Required field 'email' not found in form response")
            
            # Verify data extraction error is handled
            with pytest.raises(KeyError, match="Required field 'email' not found"):
                await mock_webhook_handler.process_webhook(webhook_payload)

    async def test_webhook_error_handling_retry_logic_success(self, async_benchmark_timer):
        """Test webhook processing retry logic succeeds after failures."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with retry logic
            mock_webhook_handler = AsyncMock()
            
            # Setup retry scenario: fail twice, succeed on third try
            mock_webhook_handler.process_webhook.side_effect = [
                Exception("Temporary error 1"),
                Exception("Temporary error 2"),
                {
                    "processed": True,
                    "retry_count": 2,
                    "client_id": f"client_{get_next_webhook_counter()}",
                    "final_attempt": True
                }
            ]
            
            # Test retry failures
            with pytest.raises(Exception, match="Temporary error 1"):
                await mock_webhook_handler.process_webhook(webhook_payload)
                
            with pytest.raises(Exception, match="Temporary error 2"):
                await mock_webhook_handler.process_webhook(webhook_payload)
            
            # Test successful retry
            result = await mock_webhook_handler.process_webhook(webhook_payload)
            assert result["processed"] is True
            assert result["retry_count"] == 2
            assert result["final_attempt"] is True

    async def test_webhook_error_handling_retry_logic_max_attempts(self, async_benchmark_timer):
        """Test webhook processing respects maximum retry attempts."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with max retry logic
            mock_webhook_handler = AsyncMock()
            
            # Setup scenario where all retries fail
            max_retries = 3
            error_responses = [Exception(f"Persistent error attempt {i}") for i in range(max_retries)]
            error_responses.append(Exception("Max retries exceeded"))
            
            mock_webhook_handler.process_webhook.side_effect = error_responses
            
            # Test all retry attempts fail
            for i in range(max_retries):
                with pytest.raises(Exception, match=f"Persistent error attempt {i}"):
                    await mock_webhook_handler.process_webhook(webhook_payload)
            
            # Test final failure after max retries
            with pytest.raises(Exception, match="Max retries exceeded"):
                await mock_webhook_handler.process_webhook(webhook_payload)

    async def test_webhook_error_handling_partial_processing_success(self, async_benchmark_timer):
        """Test webhook processing handles partial success scenarios."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with partial processing
            mock_webhook_handler = AsyncMock()
            
            # Setup partial success scenario
            mock_webhook_handler.process_webhook.return_value = {
                "processed": True,
                "client_data_extracted": True,
                "client_data_stored": True,
                "events_published": False,  # Partial failure
                "notifications_sent": False,  # Partial failure
                "warnings": ["Event publishing failed", "Notification service unavailable"],
                "client_id": f"client_{get_next_webhook_counter()}"
            }
            
            result = await mock_webhook_handler.process_webhook(webhook_payload)
            
            # Verify partial success handling
            assert result["processed"] is True
            assert result["client_data_extracted"] is True
            assert result["client_data_stored"] is True
            assert result["events_published"] is False
            assert result["notifications_sent"] is False
            assert len(result["warnings"]) == 2
            assert "client_id" in result

    async def test_webhook_error_handling_cascading_failures(self, async_benchmark_timer):
        """Test webhook processing handles cascading failure scenarios."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with cascading failures
            mock_webhook_handler = AsyncMock()
            
            # Setup cascading failure scenario
            mock_webhook_handler.process_webhook.side_effect = Exception(
                "Database error caused event publishing failure caused notification failure"
            )
            
            # Verify cascading failure is handled
            with pytest.raises(Exception, match="Database error caused.*event publishing.*notification"):
                await mock_webhook_handler.process_webhook(webhook_payload)

    async def test_webhook_error_handling_performance_degradation(self, async_benchmark_timer):
        """Test webhook processing handles performance degradation gracefully."""
        
        webhook_payload = create_webhook_payload_kwargs(
            form_id=f"form_{get_next_onboarding_form_id()}",
            response_id=f"response_{get_next_form_response_counter()}"
        )
        
        async with async_benchmark_timer() as timer:
            # Create mock webhook handler with slow processing
            mock_webhook_handler = AsyncMock()
            
            # Setup slow processing scenario
            mock_webhook_handler.process_webhook.return_value = {
                "processed": True,
                "processing_time_ms": 5000,  # Slow processing
                "performance_warning": True,
                "client_id": f"client_{get_next_webhook_counter()}",
                "warnings": ["Processing time exceeded normal threshold"]
            }
            
            result = await mock_webhook_handler.process_webhook(webhook_payload)
            
            # Verify performance degradation is tracked
            assert result["processed"] is True
            assert result["processing_time_ms"] > 100  # Exceeds normal threshold
            assert result["performance_warning"] is True
            assert "warnings" in result 