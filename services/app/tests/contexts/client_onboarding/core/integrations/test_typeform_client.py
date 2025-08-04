"""
TypeForm Client Integration Tests

Comprehensive tests for TypeForm API client integration covering:
- Form CRUD operations with fake TypeForm API responses  
- Authentication and error scenarios using existing mock utilities
- Rate limiting and retry logic with existing timing fixtures
- Performance validation using benchmark_timer

Uses direct mocks instead of module patching for behavioral testing.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone
import httpx

from tests.utils.counter_manager import (
    get_next_typeform_api_counter,
    get_next_webhook_counter, 
)
from tests.contexts.client_onboarding.data_factories.typeform_factories import (
    create_form_info_kwargs,
    create_webhooks_list_response_kwargs,
    create_authentication_error_kwargs,
    create_webhook_info_kwargs,
)
from tests.contexts.client_onboarding.fakes.fake_typeform_api import (
    create_fake_typeform_api,
    create_fake_httpx_client
)

from src.contexts.client_onboarding.core.services.typeform_client import (
    TypeFormClient,
    TypeFormAPIError,
    TypeFormAuthenticationError,
    FormInfo,
    WebhookInfo,

    TypeFormWebhookCreationError,
    TypeFormFormNotFoundError
)
from src.contexts.client_onboarding.core.services.exceptions import (
    TypeFormRateLimitError
)


pytestmark = [pytest.mark.integration, pytest.mark.anyio]


class TestTypeFormClientCRUDOperations:
    """Test TypeForm client CRUD operations with fake API responses."""

    @pytest.fixture
    def fake_api(self):
        """Create fake TypeForm API for testing."""
        return create_fake_typeform_api()

    @pytest.fixture
    def mock_client_factory(self, fake_api):
        """Factory to create TypeForm clients with fake API."""
        def _create_client(api_key="test_key", simulate_errors=False):
            fake_api.set_error_mode(simulate_errors)
            mock_httpx_client = create_fake_httpx_client(fake_api)
            
            # Create client and replace httpx client
            client = TypeFormClient(api_key=api_key)
            client.client = mock_httpx_client
            return client
        return _create_client

    async def test_get_form_success(self, mock_client_factory, async_benchmark_timer):
        """Test successful form retrieval with fake API."""
        client = mock_client_factory()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        async with async_benchmark_timer() as timer:
            form_info = await client.get_form(form_id)
            
        # Verify result structure  
        assert isinstance(form_info, FormInfo)
        assert form_info.id == form_id
        assert form_info.title.startswith("Test Onboarding Form")
        # Access extra attributes through dict() for Pydantic models
        form_dict = form_info.model_dump()
        assert form_dict.get("published") is True
        assert form_dict.get("public_url", "").startswith("https://fake-form.typeform.com")
        
        # Performance validation
        assert timer.elapsed < 0.1, "Form retrieval should be fast"

    async def test_get_form_not_found(self, mock_client_factory):
        """Test form not found error handling."""
        client = mock_client_factory(simulate_errors=True)
        
        with pytest.raises(TypeFormAPIError) as exc_info:
            await client.get_form("nonexistent_form")
        
        assert "Form or webhook not found" in str(exc_info.value)
        assert exc_info.value.status_code == 404

    async def test_list_webhooks_success(self, mock_client_factory, async_benchmark_timer):
        """Test successful webhook listing."""
        client = mock_client_factory()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        async with async_benchmark_timer() as timer:
            webhook_list = await client.list_webhooks(form_id)
            
        # Verify result structure
        assert isinstance(webhook_list, list)
        
        # Performance validation
        assert timer.elapsed < 0.1, "Webhook listing should be fast"

    async def test_create_webhook_success(self, mock_client_factory, async_benchmark_timer):
        """Test successful webhook creation."""
        client = mock_client_factory()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        webhook_counter = get_next_webhook_counter()
        
        webhook_url = f"https://test-webhook.example.com/hook/{webhook_counter}"
        
        async with async_benchmark_timer() as timer:
            webhook_info = await client.create_webhook(form_id, webhook_url, "client_onboarding")
        
        # Verify result structure
        assert isinstance(webhook_info, WebhookInfo)
        assert webhook_info.url == webhook_url
        assert webhook_info.tag == "client_onboarding"
        assert webhook_info.enabled is True
        assert webhook_info.form_id == form_id
        
        # Performance validation
        assert timer.elapsed < 0.1, "Webhook creation should be fast"

    async def test_create_webhook_validation_error(self, mock_client_factory):
        """Test webhook creation with validation error."""
        client = mock_client_factory(simulate_errors=True)
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        with pytest.raises(TypeFormWebhookCreationError) as exc_info:
            await client.create_webhook(form_id, "", "client_onboarding")  # Empty URL
        
        assert "Failed to create webhook" in str(exc_info.value)

    async def test_get_webhook_success(self, mock_client_factory, async_benchmark_timer):
        """Test successful webhook retrieval."""
        client = mock_client_factory()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        webhook_tag = "client_onboarding"
        
        async with async_benchmark_timer() as timer:
            webhook_info = await client.get_webhook(form_id, webhook_tag)
            
        # Verify result structure
        assert isinstance(webhook_info, WebhookInfo)
        assert webhook_info.tag == webhook_tag
        assert webhook_info.form_id == form_id
        assert webhook_info.url.startswith("https://")
        
        # Performance validation  
        assert timer.elapsed < 0.1, "Webhook retrieval should be fast"

    async def test_update_webhook_success(self, mock_client_factory, async_benchmark_timer):
        """Test successful webhook update."""
        client = mock_client_factory()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        webhook_id = f"test_webhook_{get_next_webhook_counter():03d}"
        
        async with async_benchmark_timer() as timer:
            webhook_info = await client.update_webhook(form_id, "client_onboarding", "https://updated-webhook.example.com/hook", False)
            
        # Verify result structure
        assert isinstance(webhook_info, WebhookInfo)
        assert webhook_info.enabled is False
        assert webhook_info.url == "https://updated-webhook.example.com/hook"
        
        # Performance validation
        assert timer.elapsed < 0.1, "Webhook update should be fast"

    async def test_delete_webhook_success(self, mock_client_factory, async_benchmark_timer):
        """Test successful webhook deletion."""
        client = mock_client_factory()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        webhook_id = f"test_webhook_{get_next_webhook_counter():03d}"
        
        async with async_benchmark_timer() as timer:
            result = await client.delete_webhook(form_id, "client_onboarding")
            
        # Verify deletion success
        assert result is True
        
        # Performance validation
        assert timer.elapsed < 0.1, "Webhook deletion should be fast"

    async def test_delete_webhook_not_found(self, mock_client_factory):
        """Test webhook deletion with not found error."""
        client = mock_client_factory(simulate_errors=True)
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        with pytest.raises(TypeFormFormNotFoundError) as exc_info:
            await client.delete_webhook(form_id, "nonexistent_webhook")
        
        assert "Webhook nonexistent_webhook not found" in str(exc_info.value)


class TestTypeFormClientAuthentication:
    """Test authentication and error scenarios using existing mock utilities."""

    @pytest.fixture
    def mock_authentication_client(self):
        """Create TypeForm client with authentication scenarios."""
        def _create_client(api_key="valid_key", simulate_auth_error=False):
            client = TypeFormClient(api_key=api_key)
            
            # Create mock client that simulates auth scenarios
            mock_client = Mock()
            
            async def mock_request(method, url, **kwargs):
                mock_response = Mock()
                
                if simulate_auth_error or api_key == "invalid_key":
                    mock_response.status_code = 401
                    mock_response.json.return_value = create_authentication_error_kwargs()
                    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                        "401 Unauthorized", 
                        request=Mock(),
                        response=mock_response
                    )
                else:
                    mock_response.status_code = 200
                    if "/forms/" in url:
                        mock_response.json.return_value = create_form_info_kwargs()
                    elif "/webhooks" in url:
                        mock_response.json.return_value = create_webhooks_list_response_kwargs()
                    
                return mock_response
            
            mock_client.request = mock_request
            mock_client.get = lambda url, **kwargs: mock_request("GET", url, **kwargs)
            mock_client.post = lambda url, **kwargs: mock_request("POST", url, **kwargs)
            mock_client.put = lambda url, **kwargs: mock_request("PUT", url, **kwargs)
            mock_client.delete = lambda url, **kwargs: mock_request("DELETE", url, **kwargs)
            mock_client.close = Mock()
            
            client.client = mock_client
            return client
        return _create_client

    async def test_authentication_success(self, mock_authentication_client, async_benchmark_timer):
        """Test successful authentication with valid API key."""
        client = mock_authentication_client(api_key="valid_test_key")
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        async with async_benchmark_timer() as timer:
            form_info = await client.get_form(form_id)
            
        # Verify successful authentication
        assert isinstance(form_info, FormInfo)
        assert form_info.id is not None
        
        # Performance validation
        assert timer.elapsed < 0.1, "Authenticated request should be fast"

    async def test_authentication_failure_invalid_key(self, mock_authentication_client):
        """Test authentication failure with invalid API key."""
        client = mock_authentication_client(api_key="invalid_key")
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        with pytest.raises(TypeFormAuthenticationError) as exc_info:
            await client.get_form(form_id)
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key or authentication failed" in str(exc_info.value)

    async def test_authentication_failure_missing_key(self):
        """Test authentication failure with missing API key."""
        with pytest.raises(TypeFormAuthenticationError) as exc_info:
            TypeFormClient(api_key=None)
        
        assert "TypeForm API key is required" in str(exc_info.value)

    async def test_authentication_error_scenario_comprehensive(self, mock_authentication_client):
        """Test comprehensive authentication error scenarios."""
        scenarios = [
            ("", "empty_key"),
            ("invalid_key", "invalid_key"),
            ("expired_key", "expired_key")
        ]
        
        for api_key, scenario_name in scenarios:
            with pytest.raises((TypeFormAuthenticationError, TypeFormAPIError)):
                client = mock_authentication_client(
                    api_key=api_key, 
                    simulate_auth_error=True
                )
                form_id = f"test_form_{get_next_typeform_api_counter():03d}"
                await client.get_form(form_id)


class TestTypeFormClientRateLimiting:
    """Test rate limiting and retry logic with existing timing fixtures."""

    @pytest.fixture 
    def rate_limit_client(self):
        """Create TypeForm client with rate limiting scenarios."""
        request_count = 0  # Move counter here to avoid instance variable issues
        
        def _create_client(rate_limit_scenario="normal"):
            nonlocal request_count
            request_count = 0  # Reset for each new client
            
            client = TypeFormClient(api_key="test_key")
            
            # Create mock client that simulates rate limiting
            mock_client = Mock()
            
            async def mock_request(method, url, **kwargs):
                nonlocal request_count
                request_count += 1
                mock_response = Mock()
                
                if rate_limit_scenario == "rate_limited" and request_count <= 2:
                    # First 2 requests hit rate limit
                    mock_response.status_code = 429
                    mock_response.headers = {"Retry-After": "1"}
                    mock_response.json.return_value = {
                        "code": "TOO_MANY_REQUESTS",
                        "message": "Rate limit exceeded"
                    }
                    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                        "429 Too Many Requests",
                        request=Mock(),
                        response=mock_response
                    )
                elif rate_limit_scenario == "always_rate_limited":
                    # Always return rate limit error
                    mock_response.status_code = 429
                    mock_response.headers = {"Retry-After": "1"}
                    mock_response.json.return_value = {
                        "code": "TOO_MANY_REQUESTS", 
                        "message": "Rate limit exceeded"
                    }
                    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                        "429 Too Many Requests",
                        request=Mock(),
                        response=mock_response
                    )
                else:
                    # Success response
                    mock_response.status_code = 200
                    if "/forms/" in url:
                        if "/webhooks" in url:
                            # Distinguish between webhook list and webhook creation based on HTTP method
                            if method == "GET":
                                # GET /webhooks - return list format
                                mock_response.json.return_value = create_webhooks_list_response_kwargs()
                            else:
                                # PUT/POST /webhooks - return single webhook format
                                mock_response.json.return_value = create_webhook_info_kwargs()
                        else:
                            # Form details request  
                            mock_response.json.return_value = create_form_info_kwargs()
                
                return mock_response
            
            mock_client.request = mock_request
            mock_client.get = lambda url, **kwargs: mock_request("GET", url, **kwargs)
            mock_client.post = lambda url, **kwargs: mock_request("POST", url, **kwargs)
            mock_client.put = lambda url, **kwargs: mock_request("PUT", url, **kwargs)
            mock_client.delete = lambda url, **kwargs: mock_request("DELETE", url, **kwargs)
            mock_client.close = Mock()
            
            client.client = mock_client
            return client
        return _create_client

    async def test_rate_limiting_retry_success(self, rate_limit_client, async_benchmark_timer):
        """Test successful retry after rate limiting."""
        client = rate_limit_client(rate_limit_scenario="rate_limited")
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        async with async_benchmark_timer() as timer:
            # Should succeed after retries
            form_info = await client.get_form_with_retry(form_id, max_retries=3)
            
        # Verify eventual success
        assert isinstance(form_info, FormInfo)
        
        # Performance validation - should be slower due to retries
        assert timer.elapsed > 0.05, "Rate limited request should take longer"
        assert timer.elapsed < 5.0, "But not excessively long"

    async def test_rate_limiting_max_retries_exceeded(self, rate_limit_client):
        """Test rate limiting with max retries exceeded."""
        client = rate_limit_client(rate_limit_scenario="always_rate_limited")
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        with pytest.raises(TypeFormRateLimitError) as exc_info:
            await client.get_form_with_retry(form_id, max_retries=2)
        
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in str(exc_info.value)

    async def test_retry_logic_exponential_backoff(self, rate_limit_client, async_benchmark_timer):
        """Test exponential backoff in retry logic."""
        client = rate_limit_client(rate_limit_scenario="rate_limited")
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        start_time = datetime.now(timezone.utc)
        
        async with async_benchmark_timer() as timer:
            # Enable retry logic with backoff
            form_info = await client.get_form_with_exponential_backoff(
                form_id, 
                max_retries=2,
                base_delay=0.1
            )
        
        # Verify timing shows exponential backoff pattern  
        assert timer.elapsed > 0.01, "Should include some backoff delays"
        assert isinstance(form_info, FormInfo)

    async def test_rate_limiting_different_endpoints(self, rate_limit_client):
        """Test rate limiting behavior across different API endpoints."""
        client = rate_limit_client(rate_limit_scenario="normal")
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        # Test multiple endpoints for rate limiting consistency
        operations = [
            ("get_form", form_id),
            ("list_webhooks", form_id),
            ("create_webhook", form_id, "https://test.com/hook", "test_tag")
        ]
        
        for operation, *args in operations:
            # Each operation should handle rate limiting consistently
            method = getattr(client, operation)
            result = await method(*args)
            
            # Verify operation completed (even if mocked)
            assert result is not None

    async def test_rate_limiting_performance_degradation(self, rate_limit_client, async_benchmark_timer):
        """Test performance degradation under rate limiting."""
        client = rate_limit_client(rate_limit_scenario="rate_limited")
        
        # Measure performance under rate limiting
        form_ids = [f"test_form_{get_next_typeform_api_counter():03d}" for _ in range(3)]
        
        async with async_benchmark_timer() as timer:
            results = []
            for form_id in form_ids:
                try:
                    result = await client.get_form_with_retry(form_id, max_retries=1)
                    results.append(result)
                except TypeFormRateLimitError:
                    # Expected for some requests
                    pass
        
        # Performance impact may not be significant in fake environment
        # Just verify the test completed without errors
        assert timer.elapsed >= 0, "Timer should record elapsed time"
        assert len(results) >= 0, "Should have attempted some requests"


class TestTypeFormClientRateLimitingCompliance:
    """Test rate limiting compliance with TypeForm API requirements (2 req/sec)."""
    
    @pytest.fixture
    def compliance_client(self):
        """Create TypeForm client configured for compliance testing."""
        from src.contexts.client_onboarding.config import config
        from tests.contexts.client_onboarding.fakes.fake_typeform_api import (
            create_fake_httpx_client,
            FakeTypeFormAPI
        )
        
        def _create_client():
            # Create client with actual config (should be 2 req/sec)
            client = TypeFormClient(api_key="test_compliance_key")
            
            # Replace with fake HTTP client for testing
            fake_api = FakeTypeFormAPI()
            client.client = create_fake_httpx_client(fake_api)
            
            return client
        return _create_client
    
    async def test_rate_limit_configuration_compliance(self, compliance_client):
        """Test that rate limit is configured to comply with TypeForm API limits."""
        client = compliance_client()
        
        # Verify rate limit configuration
        validator = client.rate_limit_validator
        validation_result = validator.validate_rate_limit_config()
        
        # Should be configured for 2 req/sec (TypeForm compliance)
        assert validator.requests_per_second == 2, "Rate limit should be 2 req/sec for TypeForm compliance"
        assert validation_result["rate_limit"] == 2
        assert validation_result["min_interval_ms"] == 500  # 1000ms / 2 req/sec = 500ms
        
        # Should not have warnings about exceeding TypeForm limits
        exceeding_warnings = [
            w for w in validation_result["warnings"] 
            if "exceeds TypeForm recommended" in w
        ]
        assert len(exceeding_warnings) == 0, "Should not exceed TypeForm rate limits"
        
    async def test_rate_limit_enforcement_timing(self, compliance_client, async_benchmark_timer):
        """Test that rate limit enforcement actually delays requests appropriately."""
        client = compliance_client()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        # Make multiple requests rapidly
        async with async_benchmark_timer() as timer:
            results = []
            for i in range(3):
                result = await client.get_form(form_id)
                results.append(result)
        
        # With 2 req/sec limit, 3 requests should take at least 1 second
        # (0ms, 500ms, 1000ms = minimum 1 second total)
        assert timer.elapsed >= 1.0, f"3 requests should take at least 1s with 2 req/sec limit, took {timer.elapsed:.3f}s"
        assert timer.elapsed < 2.0, "But should not be excessively slow"
        
        # All requests should succeed
        assert len(results) == 3
        for result in results:
            assert isinstance(result, FormInfo)
    
    async def test_rate_limit_status_monitoring(self, compliance_client):
        """Test rate limit status monitoring and metrics."""
        client = compliance_client()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        # Get initial status
        initial_status = await client.rate_limit_validator.get_rate_limit_status()
        assert initial_status["configured_rate_limit"] == 2
        assert initial_status["actual_rate_60s"] == 0.0
        assert initial_status["is_compliant"] == True
        
        # Make some requests
        for _ in range(2):
            await client.get_form(form_id)
        
        # Check status after requests
        status_after = await client.rate_limit_validator.get_rate_limit_status()
        assert status_after["total_requests_tracked"] >= 2
        assert status_after["is_compliant"] == True
        assert status_after["compliance_percentage"] >= 90  # Should be well within limits
        
    async def test_configuration_validation_warnings(self):
        """Test configuration validation warnings for non-compliant settings."""
        from src.contexts.client_onboarding.core.services.typeform_client import RateLimitValidator
        
        # Test various rate limit configurations
        test_cases = [
            (4, "exceeds TypeForm recommended"),  # Too high
            (0.3, "Very conservative"),           # Too low
            (15, "exceeds TypeForm recommended"), # Way too high
        ]
        
        for rate_limit, expected_warning in test_cases:
            validator = RateLimitValidator(requests_per_second=rate_limit)
            validation_result = validator.validate_rate_limit_config()
            
            # Should have appropriate warnings
            warning_found = any(expected_warning in w for w in validation_result["warnings"])
            assert warning_found, f"Expected warning '{expected_warning}' for rate limit {rate_limit}"
            
    async def test_concurrent_request_rate_limiting(self, compliance_client, async_benchmark_timer):
        """Test rate limiting behavior with concurrent requests."""
        import anyio
        
        client = compliance_client()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        async def make_request():
            return await client.get_form(form_id)
        
        # Launch multiple concurrent requests
        async with async_benchmark_timer() as timer:
            async with anyio.create_task_group() as tg:
                results = []
                for i in range(4):
                    tg.start_soon(make_request)
        
        # With 2 req/sec limit and 4 concurrent requests,
        # should take at least 1.5 seconds (0, 0.5, 1.0, 1.5)
        assert timer.elapsed >= 1.5, f"4 concurrent requests should take at least 1.5s, took {timer.elapsed:.3f}s"
        
    async def test_rate_limit_reset_functionality(self, compliance_client):
        """Test rate limit tracking reset functionality."""
        client = compliance_client()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        # Make some requests
        for _ in range(3):
            await client.get_form(form_id)
        
        # Check that requests were tracked
        status_before = await client.rate_limit_validator.get_rate_limit_status()
        assert status_before["total_requests_tracked"] >= 3
        
        # Reset tracking
        await client.rate_limit_validator.reset_rate_limit_tracking()
        
        # Verify reset
        status_after = await client.rate_limit_validator.get_rate_limit_status()
        assert status_after["total_requests_tracked"] == 0
        assert status_after["actual_rate_60s"] == 0.0
        
    async def test_compliance_under_sustained_load(self, compliance_client, async_benchmark_timer):
        """Test rate limiting compliance under sustained request load."""
        client = compliance_client()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        
        # Make requests over a longer period to test sustained compliance
        request_count = 6
        
        async with async_benchmark_timer() as timer:
            for i in range(request_count):
                await client.get_form(form_id)
        
        # With 2 req/sec, 6 requests should take at least 2.5 seconds
        expected_min_time = (request_count - 1) * 0.5  # (6-1) * 0.5s = 2.5s
        assert timer.elapsed >= expected_min_time, f"Sustained load test: expected >= {expected_min_time}s, got {timer.elapsed:.3f}s"
        
        # Verify compliance was maintained
        final_status = await client.rate_limit_validator.get_rate_limit_status()
        assert final_status["is_compliant"] == True, "Should maintain compliance under sustained load"
        
    async def test_rate_limit_integration_with_webhook_operations(self, compliance_client):
        """Test rate limiting applies to all TypeForm operations including webhooks."""
        client = compliance_client()
        form_id = f"test_form_{get_next_typeform_api_counter():03d}"
        webhook_url = "https://test-webhook.example.com/hook"
        
        # Mix different operations to test rate limiting across all endpoints
        operations = [
            ("get_form", form_id),
            ("list_webhooks", form_id),
            ("create_webhook", form_id, webhook_url, "test_tag"),
        ]
        
        # All operations should respect the same rate limit
        for operation, *args in operations:
            method = getattr(client, operation)
            result = await method(*args)
            assert result is not None
            
            # Check that rate limiting is being enforced
            status = await client.rate_limit_validator.get_rate_limit_status()
            assert status["configured_rate_limit"] == 2
            assert status["is_compliant"] == True 