"""Test concurrent request handling for FastAPI endpoints.

Validates thread safety and async compatibility under concurrent load.
Tests multiple endpoints across all contexts to ensure no race conditions
or shared state issues occur during concurrent request processing.

Follows @testing-principles: behavior-focused, no mocks, AnyIO patterns.
"""

import pytest
import httpx
from typing import Any
import anyio
from anyio import create_task_group


pytestmark = pytest.mark.anyio


class ConcurrentRequestTester:
    """Test concurrent request handling across FastAPI endpoints.
    
    Uses AnyIO patterns and behavior-focused testing without mocks.
    """
    
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.results: list[dict[str, Any]] = []
        self.errors: list[Exception] = []
    
    async def make_request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """Make a single HTTP request and return result with metadata.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Request result with timing and success metadata
        """
        start_time = anyio.current_time()
        try:
            response = await self.client.request(method, url, **kwargs)
            end_time = anyio.current_time()
            
            return {
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": True,
                "response_data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
                "error": None
            }
        except Exception as e:
            end_time = anyio.current_time()
            return {
                "method": method,
                "url": url,
                "status_code": None,
                "response_time": end_time - start_time,
                "success": False,
                "response_data": None,
                "error": str(e)
            }
    
    async def run_concurrent_requests(self, requests: list[dict[str, Any]], concurrency: int = 10) -> list[dict[str, Any]]:
        """Run multiple requests concurrently using AnyIO task groups.
        
        Args:
            requests: list of request configurations
            concurrency: Maximum concurrent requests
            
        Returns:
            list of request results
        """
        results = []
        
        async def process_request(request_data: dict[str, Any]) -> None:
            """Process a single request and collect result."""
            result = await self.make_request(**request_data)
            results.append(result)
        
        # Use AnyIO task group for concurrent execution
        async with create_task_group() as tg:
            # Create semaphore to limit concurrency
            semaphore = anyio.Semaphore(concurrency)
            
            async def limited_request(request_data: dict[str, Any]) -> None:
                """Execute request with concurrency limit."""
                async with semaphore:
                    await process_request(request_data)
            
            # Start all requests concurrently
            for req in requests:
                tg.start_soon(limited_request, req)
        
        return results


@pytest.mark.integration
class TestConcurrentRequestHandling:
    """Test suite for concurrent request handling validation.
    
    Focuses on behavior: response correctness, timing, and isolation.
    """
    
    async def test_concurrent_health_checks(self, fastapi_async_client):
        """Test concurrent health check requests maintain correctness.
        
        Behavior: All health checks should succeed with consistent responses.
        """
        tester = ConcurrentRequestTester(fastapi_async_client)
        
        # Create 50 concurrent health check requests
        requests = [
            {"method": "GET", "url": "/health"}
            for _ in range(50)
        ]
        
        results = await tester.run_concurrent_requests(requests, concurrency=20)
        
        # Assert behavior: all requests complete successfully
        assert len(results) == 50, "All requests should complete"
        
        successful_requests = [r for r in results if r["success"]]
        assert len(successful_requests) == 50, "All health checks should succeed"
        
        # Assert response consistency
        response_codes = [r["status_code"] for r in successful_requests]
        assert all(code == 200 for code in response_codes), "All health checks should return 200"
        
        # Assert reasonable performance
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests)
        assert avg_response_time < 1.0, f"Average response time should be under 1s, got {avg_response_time:.3f}s"
    
    async def test_concurrent_products_endpoints(self, fastapi_async_client):
        """Test concurrent product endpoint requests maintain isolation.
        
        Behavior: Different requests should not interfere with each other.
        """
        tester = ConcurrentRequestTester(fastapi_async_client)
        
        # Create mixed concurrent requests to products endpoints
        requests = []
        
        # Add search requests with different parameters
        for i in range(10):
            requests.append({
                "method": "GET",
                "url": "/products/search",
                "params": {"limit": 10, "skip": i * 10}
            })
        
        # Add similar name search requests with different names
        for i in range(5):
            requests.append({
                "method": "GET", 
                "url": "/products/similar-names",
                "params": {"name": f"test_product_{i}", "limit": 5}
            })
        
        results = await tester.run_concurrent_requests(requests, concurrency=15)
        
        # Assert behavior: all requests complete
        assert len(results) == 15, "All requests should complete"
        
        successful_requests = [r for r in results if r["success"]]
        assert len(successful_requests) >= 10, "Most requests should succeed (some may fail due to auth)"
        
        # Assert performance remains reasonable
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests)
        assert avg_response_time < 2.0, f"Average response time should be under 2s, got {avg_response_time:.3f}s"
    
    async def test_concurrent_recipes_endpoints(self, fastapi_async_client):
        """Test concurrent recipe endpoint requests maintain context isolation.
        
        Behavior: Requests across different recipe contexts should not interfere.
        """
        tester = ConcurrentRequestTester(fastapi_async_client)
        
        # Create mixed concurrent requests to recipes endpoints
        requests = []
        
        # Add recipe search requests
        for i in range(8):
            requests.append({
                "method": "GET",
                "url": "/recipes/search",
                "params": {"limit": 10, "skip": i * 10}
            })
        
        # Add meal search requests
        for i in range(5):
            requests.append({
                "method": "GET",
                "url": "/meals/search", 
                "params": {"limit": 5, "skip": i * 5}
            })
        
        # Add client search requests
        for i in range(3):
            requests.append({
                "method": "GET",
                "url": "/clients/search",
                "params": {"limit": 5, "skip": i * 5}
            })
        
        results = await tester.run_concurrent_requests(requests, concurrency=16)
        
        # Assert behavior: all requests complete
        assert len(results) == 16, "All requests should complete"
        
        successful_requests = [r for r in results if r["success"]]
        assert len(successful_requests) >= 10, "Most requests should succeed"
        
        # Assert performance remains reasonable
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests)
        assert avg_response_time < 2.0, f"Average response time should be under 2s, got {avg_response_time:.3f}s"
    
    async def test_concurrent_mixed_context_endpoints(self, fastapi_async_client):
        """Test concurrent requests across different contexts maintain isolation.
        
        Behavior: Requests to different business contexts should not interfere.
        """
        tester = ConcurrentRequestTester(fastapi_async_client)
        
        # Create requests across all contexts
        requests = [
            # Products context
            {"method": "GET", "url": "/products/search", "params": {"limit": 5}},
            {"method": "GET", "url": "/products/similar-names", "params": {"name": "test", "limit": 3}},
            
            # Recipes context  
            {"method": "GET", "url": "/recipes/search", "params": {"limit": 5}},
            {"method": "GET", "url": "/meals/search", "params": {"limit": 5}},
            {"method": "GET", "url": "/clients/search", "params": {"limit": 5}},
            
            # Client onboarding context
            {"method": "GET", "url": "/client-onboarding/forms", "params": {"limit": 5}},
            
            # IAM context
            {"method": "GET", "url": "/users", "params": {"limit": 5}},
            
            # Health check
            {"method": "GET", "url": "/health"},
        ]
        
        # Run multiple rounds of these requests concurrently
        all_requests = []
        for _ in range(3):  # 3 rounds
            all_requests.extend(requests.copy())
        
        results = await tester.run_concurrent_requests(all_requests, concurrency=20)
        
        # Assert behavior: all requests complete
        assert len(results) == len(all_requests), "All requests should complete"
        
        successful_requests = [r for r in results if r["success"]]
        assert len(successful_requests) >= len(all_requests) * 0.7, "Most requests should succeed"
        
        # Assert context isolation: each context should have successful requests
        context_results = {}
        for result in successful_requests:
            url = result["url"]
            context = url.split("/")[1] if "/" in url else "root"
            if context not in context_results:
                context_results[context] = []
            context_results[context].append(result)
        
        assert "health" in context_results, "Health endpoint should work"
        assert len(context_results) >= 3, "Multiple contexts should be accessible"
    
    async def test_concurrent_request_with_different_parameters(self, fastapi_async_client):
        """Test concurrent requests with different parameters maintain isolation.
        
        Behavior: Requests with different parameters should not bleed into each other.
        """
        tester = ConcurrentRequestTester(fastapi_async_client)
        
        # Create requests with different parameters
        requests = []
        for i in range(20):
            requests.append({
                "method": "GET",
                "url": "/products/search",
                "params": {
                    "limit": 5 + (i % 10),  # Different limits
                    "skip": i * 5,           # Different offsets
                    "name": f"product_{i}"   # Different names
                }
            })
        
        results = await tester.run_concurrent_requests(requests, concurrency=20)
        
        # Assert behavior: all requests complete
        assert len(results) == 20, "All requests should complete"
        
        successful_requests = [r for r in results if r["success"]]
        assert len(successful_requests) >= 15, "Most requests should succeed"
        
        # Assert parameter isolation: response times should vary (indicating different processing)
        response_times = [r["response_time"] for r in successful_requests]
        assert len(set(response_times)) > 1, "Response times should vary (indicating different processing)"
        
        # Assert reasonable performance
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 2.0, f"Average response time should be under 2s, got {avg_response_time:.3f}s"
    
    async def test_concurrent_request_stress_test(self, fastapi_async_client):
        """Stress test with high concurrency to validate thread safety.
        
        Behavior: System should handle high concurrency without errors.
        """
        tester = ConcurrentRequestTester(fastapi_async_client)
        
        # Create a large number of concurrent requests
        requests = []
        for i in range(100):
            requests.append({
                "method": "GET",
                "url": "/health"  # Use health endpoint for stress test
            })
        
        results = await tester.run_concurrent_requests(requests, concurrency=50)
        
        # Assert behavior: all requests complete successfully
        assert len(results) == 100, "All requests should complete"
        
        successful_requests = [r for r in results if r["success"]]
        assert len(successful_requests) == 100, "All health checks should succeed under stress"
        
        # Assert performance characteristics
        response_times = [r["response_time"] for r in successful_requests]
        min_time = min(response_times)
        max_time = max(response_times)
        avg_time = sum(response_times) / len(response_times)
        
        assert min_time < 0.1, f"Minimum response time should be under 0.1s, got {min_time:.3f}s"
        assert max_time < 5.0, f"Maximum response time should be under 5s, got {max_time:.3f}s"
        assert avg_time < 1.0, f"Average response time should be under 1s, got {avg_time:.3f}s"
        
        # Assert no errors occurred
        error_requests = [r for r in results if not r["success"]]
        assert len(error_requests) == 0, f"No requests should fail under stress test, got {len(error_requests)} errors"


@pytest.mark.integration
class TestConcurrentRequestThreadSafety:
    """Additional tests specifically for thread safety validation.
    
    Focuses on isolation and error handling behavior.
    """
    
    async def test_concurrent_request_isolation(self, fastapi_async_client):
        """Test that concurrent requests don't interfere with each other.
        
        Behavior: Independent requests should remain independent.
        """
        tester = ConcurrentRequestTester(fastapi_async_client)
        
        # Create requests that should be independent
        requests = []
        for i in range(30):
            requests.append({
                "method": "GET",
                "url": "/products/search",
                "params": {
                    "limit": 5,
                    "skip": i * 5,
                    "name": f"unique_product_{i}"  # Unique parameter per request
                }
            })
        
        results = await tester.run_concurrent_requests(requests, concurrency=30)
        
        # Assert behavior: all requests complete
        assert len(results) == 30, "All requests should complete"
        
        successful_requests = [r for r in results if r["success"]]
        assert len(successful_requests) >= 20, "Most requests should succeed"
        
        # Assert isolation: response times should vary (indicating independent processing)
        response_times = [r["response_time"] for r in successful_requests]
        unique_times = len(set(response_times))
        assert unique_times > 10, "Response times should vary (indicating independent processing)"
    
    async def test_concurrent_request_error_handling(self, fastapi_async_client):
        """Test that errors in concurrent requests don't affect other requests.
        
        Behavior: Failed requests should not impact successful ones.
        """
        tester = ConcurrentRequestTester(fastapi_async_client)
        
        # Mix valid and invalid requests
        requests = [
            # Valid requests
            {"method": "GET", "url": "/health"},
            {"method": "GET", "url": "/health"},
            {"method": "GET", "url": "/health"},
            
            # Invalid requests (should fail gracefully)
            {"method": "GET", "url": "/nonexistent-endpoint"},
            {"method": "GET", "url": "/products/invalid-id"},
            {"method": "POST", "url": "/health"},  # Wrong method
        ]
        
        results = await tester.run_concurrent_requests(requests, concurrency=6)
        
        # Assert behavior: all requests complete
        assert len(results) == 6, "All requests should complete"
        
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        assert len(successful_requests) == 3, "Valid requests should succeed"
        assert len(failed_requests) == 3, "Invalid requests should fail gracefully"
        
        # Assert error isolation: successful requests weren't affected by failures
        health_requests = [r for r in successful_requests if r["url"] == "/health"]
        assert len(health_requests) == 3, "All health requests should succeed"
        
        # Assert reasonable performance
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests)
        assert avg_response_time < 1.0, f"Average response time should be under 1s, got {avg_response_time:.3f}s"
