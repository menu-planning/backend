"""
Performance tests for FastAPI authentication system.

This module tests authentication performance characteristics including
response times, caching effectiveness, and concurrent request handling.
Follows behavior-focused testing principles with minimal mocking.
"""

import pytest
import asyncio
import anyio
import time
import statistics

from src.runtimes.fastapi.auth.strategy import FastAPIAuthenticationStrategy
from src.runtimes.fastapi.auth.jwt_validator import CognitoJWTValidator
from src.runtimes.fastapi.auth.cache import RequestScopedAuthCache, UserContextCache
from src.contexts.shared_kernel.middleware.auth.authentication import UnifiedIAMProvider

# Use AnyIO for async testing
pytestmark = pytest.mark.anyio


class TestAuthPerformance:
    """Test authentication performance characteristics."""
    
    @pytest.fixture
    def jwt_validator(self):
        """Create real JWT validator for performance testing."""
        return CognitoJWTValidator()
    
    @pytest.fixture
    def iam_provider(self):
        """Create real IAM provider for performance testing."""
        return UnifiedIAMProvider(
            logger_name="perf_test_iam",
            cache_strategy="request"
        )
    
    @pytest.fixture
    def auth_strategy(self, jwt_validator, iam_provider):
        """Create authentication strategy with real dependencies."""
        return FastAPIAuthenticationStrategy(
            iam_provider=iam_provider,
            caller_context="test_context",
            jwt_validator=jwt_validator
        )
    
    @pytest.fixture
    def test_request(self):
        """Create test FastAPI request with custom headers for performance testing."""
        from fastapi import Request
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [
                (b"x-user-id", b"perf-test-user"),
                (b"x-user-roles", b"user,perf-tester")
            ],
            "query_string": b"",
            "client": ("127.0.0.1", 8080)
        }
        
        return Request(scope, None)
    
    async def test_auth_response_time_under_200ms(self, auth_strategy, test_request):
        """Test that authentication completes within 200ms."""
        # When: Measure authentication performance
        start_time = time.time()
        auth_context = await auth_strategy.extract_auth_context(test_request)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        # Then: Should complete quickly and return valid context
        assert execution_time_ms < 200, f"Auth took {execution_time_ms:.2f}ms, expected < 200ms"
        assert auth_context.user_id == "perf-test-user"
        assert auth_context.user_roles == ["user", "perf-tester"]
        assert auth_context.is_authenticated is True
    
    async def test_concurrent_auth_requests_performance(self, auth_strategy):
        """Test performance with multiple concurrent authentication requests."""
        # Given: Multiple concurrent requests with custom headers
        def create_request(user_id: str):
            from fastapi import Request
            scope = {
                "type": "http",
                "method": "GET",
                "path": f"/api/{user_id}",
                "headers": [
                    (b"x-user-id", user_id.encode()),
                    (b"x-user-roles", b"user")
                ],
                "query_string": b"",
                "client": ("127.0.0.1", 8080)
            }
            return Request(scope, None)
        
        requests = [create_request(f"user{i}") for i in range(10)]
        
        # When: Execute concurrent authentication requests
        start_time = time.time()
        
        async def auth_request(request):
            return await auth_strategy.extract_auth_context(request)
        
        tasks = [auth_request(request) for request in requests]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        # Then: Should handle concurrent requests efficiently
        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_request = total_time_ms / len(requests)
        
        assert total_time_ms < 1000, f"10 concurrent requests took {total_time_ms:.2f}ms, expected < 1000ms"
        assert avg_time_per_request < 200, f"Average time per request was {avg_time_per_request:.2f}ms, expected < 200ms"
        assert len(results) == 10
        
        # Verify all requests completed successfully
        for i, auth_context in enumerate(results):
            assert auth_context.user_id == f"user{i}"
            assert auth_context.user_roles == ["user"]
            assert auth_context.is_authenticated is True
    
    async def test_auth_caching_performance(self):
        """Test authentication caching performance benefits."""
        # Given: Cache instance and expensive operation simulation
        cache = RequestScopedAuthCache()
        call_count = 0
        
        async def expensive_auth_operation(user_id: str):
            nonlocal call_count
            call_count += 1
            await anyio.sleep(0.1)  # 100ms operation simulation
            return {"user_id": user_id, "expensive_data": "cached_result"}
        
        # When: First call - should be expensive
        start_time = time.time()
        result1 = await cache.get_or_set(
            "user123", 
            lambda: expensive_auth_operation("user123"),
            ttl_seconds=300
        )
        first_call_time = (time.time() - start_time) * 1000
        
        # When: Second call - should be fast (cached)
        start_time = time.time()
        result2 = await cache.get_or_set(
            "user123", 
            lambda: expensive_auth_operation("user123"),
            ttl_seconds=300
        )
        second_call_time = (time.time() - start_time) * 1000
        
        # Then: Caching should provide performance benefits
        assert call_count == 1, "Expensive operation should only be called once"
        assert result1 == result2, "Cached result should match original"
        assert second_call_time < 10, f"Cached call took {second_call_time:.2f}ms, expected < 10ms"
        assert first_call_time > 90, f"First call took {first_call_time:.2f}ms, expected > 90ms"
        
        # Verify cache hit ratio
        cache_hit_ratio = cache.get_cache_stats().get("hit_ratio", 0)
        assert cache_hit_ratio > 0, "Cache should have hits"
    
    async def test_user_context_cache_performance(self):
        """Test user context caching performance."""
        # Given: User context cache and expensive operation simulation
        cache = UserContextCache(default_ttl_seconds=300)
        call_count = 0
        
        async def create_user_context(user_id: str):
            nonlocal call_count
            call_count += 1
            await anyio.sleep(0.05)  # 50ms operation simulation
            return {
                "user_id": user_id,
                "roles": ["user"],
                "permissions": ["read", "write"]
            }
        
        # When: Multiple concurrent requests for same user
        user_id = "user123"
        requests = [create_user_context(user_id) for _ in range(5)]
        
        start_time = time.time()
        results = await asyncio.gather(*requests)
        end_time = time.time()
        
        total_time_ms = (end_time - start_time) * 1000
        
        # Then: Caching should provide performance benefits
        assert call_count == 1, "User context should only be created once due to caching"
        assert total_time_ms < 100, f"5 requests took {total_time_ms:.2f}ms with caching, expected < 100ms"
        
        # Verify all results are identical
        for result in results:
            assert result["user_id"] == user_id
            assert result["roles"] == ["user"]
    
    async def test_auth_latency_percentiles(self, auth_strategy):
        """Test authentication latency percentiles under load."""
        # Given: Multiple requests with custom headers
        def create_request(user_id: str):
            from fastapi import Request
            scope = {
                "type": "http",
                "method": "GET",
                "path": f"/api/{user_id}",
                "headers": [
                    (b"x-user-id", user_id.encode()),
                    (b"x-user-roles", b"user")
                ],
                "query_string": b"",
                "client": ("127.0.0.1", 8080)
            }
            return Request(scope, None)
        
        requests = [create_request(f"user{i}") for i in range(20)]
        
        # When: Measure latencies for multiple requests
        latencies = []
        for request in requests:
            start_time = time.time()
            await auth_strategy.extract_auth_context(request)
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        # Then: Calculate and verify percentiles
        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[int(0.95 * len(latencies))]
        p99 = sorted(latencies)[int(0.99 * len(latencies))]
        
        assert p50 < 150, f"P50 latency was {p50:.2f}ms, expected < 150ms"
        assert p95 < 200, f"P95 latency was {p95:.2f}ms, expected < 200ms"
        assert p99 < 300, f"P99 latency was {p99:.2f}ms, expected < 300ms"
        
        # Log performance metrics
        print(f"\nAuth Performance Metrics:")
        print(f"P50: {p50:.2f}ms")
        print(f"P95: {p95:.2f}ms")
        print(f"P99: {p99:.2f}ms")
        print(f"Average: {statistics.mean(latencies):.2f}ms")
        print(f"Max: {max(latencies):.2f}ms")
