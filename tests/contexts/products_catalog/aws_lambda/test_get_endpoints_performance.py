"""
Performance tests for migrated GET endpoints in products_catalog.

Tests validate that LambdaHelpers migration maintains acceptable performance
with response times within expected thresholds.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.contexts.products_catalog.aws_lambda import (
    get_product_by_id,
    get_product_source_name_by_id,
    fetch_product,
    search_product_similar_name,
    fetch_product_source_name
)

pytestmark = [pytest.mark.anyio]

class PerformanceTimer:
    """Helper class for measuring execution time with precision."""
    
    def __init__(self):
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.execution_time: float | None = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            self.end_time = time.perf_counter()
            self.execution_time = self.end_time - self.start_time
        else:
            self.execution_time = 0.0
    
    async def __aenter__(self):
        self.start_time = time.perf_counter()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            self.end_time = time.perf_counter()
            self.execution_time = self.end_time - self.start_time
        else:
            self.execution_time = 0.0
    
    def assert_faster_than(self, threshold_seconds: float, operation: str = "Operation"):
        """Assert that execution time is under threshold."""
        if self.execution_time is None:
            raise ValueError("Timer was not properly executed")
        assert self.execution_time < threshold_seconds, (
            f"{operation} took {self.execution_time:.6f}s, "
            f"expected < {threshold_seconds}s"
        )
    
    def get_execution_time(self) -> float:
        """Get execution time, ensuring it's not None."""
        if self.execution_time is None:
            raise ValueError("Timer was not properly executed")
        return self.execution_time


class TestGetEndpointsPerformance:
    """Performance tests for migrated GET endpoints with LambdaHelpers."""

    @pytest.fixture
    def mock_successful_auth_response(self):
        """Mock successful IAM auth response."""
        return {"statusCode": 200, "body": MagicMock()}

    @pytest.fixture  
    def mock_single_product_event(self):
        """Mock event for single product endpoints."""
        return {
            "requestContext": {
                "authorizer": {"claims": {"sub": "test-user-123"}}
            },
            "pathParameters": {"id": "product-123"},
            "queryStringParameters": None,
            "multiValueQueryStringParameters": None,
            "headers": {},
            "body": None
        }

    @pytest.fixture
    def mock_collection_event(self):
        """Mock event for collection endpoints."""
        return {
            "requestContext": {
                "authorizer": {"claims": {"sub": "test-user-123"}}
            },
            "pathParameters": None,
            "queryStringParameters": {"limit": "10", "sort": "-updated_at"},
            "multiValueQueryStringParameters": {"category": ["food", "beverage"]},
            "headers": {},
            "body": None
        }

    @pytest.fixture
    def mock_search_event(self):
        """Mock event for search endpoints.""" 
        return {
            "requestContext": {
                "authorizer": {"claims": {"sub": "test-user-123"}}
            },
            "pathParameters": {"name": "chicken"},
            "queryStringParameters": None,
            "multiValueQueryStringParameters": None,
            "headers": {},
            "body": None
        }

    async def test_get_product_by_id_performance(self, mock_single_product_event, mock_localstack_environment, performance_test_data):
        """Test get_product_by_id endpoint performance meets <100ms threshold."""
        
        # Using real data and localstack environment (no auth required)
        # performance_test_data fixture creates the product-123 that the test expects
        
        # Import the actual endpoint handler
        from src.contexts.products_catalog.aws_lambda import get_product_by_id
        
        # Performance test - single request
        async with PerformanceTimer() as timer:
            result = await get_product_by_id.async_handler(mock_single_product_event, {})
        
        # Verify response format
        assert result["statusCode"] == 200
        assert "body" in result
        assert "headers" in result
        
        # Performance assertion: Should complete in under 200ms (increased for real DB)
        timer.assert_faster_than(0.2, "get_product_by_id single request")
        
        # Bulk performance test - multiple requests
        iterations = 5  # Reduced iterations for real DB
        async with PerformanceTimer() as bulk_timer:
            for _ in range(iterations):
                result = await get_product_by_id.async_handler(mock_single_product_event, {})
                assert result["statusCode"] == 200
        
        # Bulk performance: Should average under 100ms per request for real DB
        avg_time = bulk_timer.get_execution_time() / iterations
        assert avg_time < 0.1, f"Average time per request {avg_time:.6f}s exceeds 100ms limit"

    async def test_get_product_source_name_by_id_performance(self, mock_single_product_event, mock_localstack_environment, performance_test_data):
        """Test get_product_source_name_by_id endpoint performance meets <100ms threshold."""
        
        # Using real data and localstack environment (no auth required)
        # performance_test_data fixture creates the product-123 that the test expects
        
        # Import the actual endpoint handler
        from src.contexts.products_catalog.aws_lambda import get_product_source_name_by_id
        
        # Performance test - single request
        async with PerformanceTimer() as timer:
            result = await get_product_source_name_by_id.async_handler(mock_single_product_event, {})
        
        # Verify response format
        assert result["statusCode"] == 200
        assert "body" in result
        assert "headers" in result
        
        # Performance assertion: Should complete in under 200ms (increased for real DB)
        timer.assert_faster_than(0.2, "get_product_source_name_by_id single request")
        
        # Bulk performance test
        iterations = 5  # Reduced iterations for real DB
        async with PerformanceTimer() as bulk_timer:
            for _ in range(iterations):
                result = await get_product_source_name_by_id.async_handler(mock_single_product_event, {})
                assert result["statusCode"] == 200
        
        # Performance validations
        avg_time = bulk_timer.get_execution_time() / iterations
        assert avg_time < 0.1, f"Average time per request {avg_time:.6f}s exceeds 100ms limit"

    async def test_fetch_product_collection_performance(self, mock_collection_event, mock_successful_auth_response):
        """Test fetch_product collection endpoint performance meets <200ms threshold."""
        
        with patch('src.contexts.products_catalog.aws_lambda.fetch_product.IAMProvider.get') as mock_auth, \
             patch('src.contexts.products_catalog.aws_lambda.fetch_product.Container') as mock_container:
            
            # Setup mocks for collection endpoint
            mock_auth.return_value = mock_successful_auth_response
            mock_uow = AsyncMock()
            
            # Mock multiple products for collection
            mock_products = []
            for i in range(10):
                mock_product = MagicMock()
                mock_product.id = f"product-{i}"
                mock_product.name = f"Product {i}"
                mock_products.append(mock_product)
            
            mock_uow.products.query.return_value = mock_products
            mock_bus = AsyncMock()
            mock_bus.uow = mock_uow
            mock_container.return_value.bootstrap.return_value = mock_bus
            
            # Mock TypeAdapter for product collection
            mock_type_adapter = MagicMock()
            mock_type_adapter.dump_json.return_value = b'[{"id": "product-1", "name": "Product 1"}]'
            
            with patch('src.contexts.products_catalog.aws_lambda.fetch_product.ProductListTypeAdapter', mock_type_adapter), \
                 patch('src.contexts.products_catalog.aws_lambda.fetch_product.ApiProduct.from_domain') as mock_from_domain:
                
                # Mock ApiProduct.from_domain to return simple objects
                mock_from_domain.side_effect = lambda p: MagicMock(id=p.id, name=p.name)
                
                # Performance test - single collection request
                async with PerformanceTimer() as timer:
                    result = await fetch_product.async_handler(mock_collection_event, {})
                
                # Verify response format
                assert result["statusCode"] == 200
                assert "body" in result
                assert "headers" in result
                
                # Performance assertion: Collection endpoints get higher threshold (200ms)
                timer.assert_faster_than(0.2, "fetch_product collection request")
                
                # Bulk performance test for collections
                iterations = 5  # Fewer iterations for collection endpoints
                async with PerformanceTimer() as bulk_timer:
                    for _ in range(iterations):
                        result = await fetch_product.async_handler(mock_collection_event, {})
                        assert result["statusCode"] == 200
                
                # Performance validations for collections
                avg_time = bulk_timer.get_execution_time() / iterations
                assert avg_time < 0.15, f"Average collection time {avg_time:.6f}s exceeds 150ms limit"
                
                throughput = iterations / bulk_timer.get_execution_time()
                assert throughput > 5, f"Collection throughput {throughput:.1f} req/sec is below 5 req/sec minimum"

    async def test_search_product_similar_name_performance(self, mock_search_event, mock_successful_auth_response):
        """Test search_product_similar_name endpoint performance meets <300ms threshold."""
        
        with patch('src.contexts.products_catalog.aws_lambda.search_product_similar_name.IAMProvider.get') as mock_auth, \
             patch('src.contexts.products_catalog.aws_lambda.search_product_similar_name.Container') as mock_container:
            
            # Setup mocks for search endpoint
            mock_auth.return_value = mock_successful_auth_response
            mock_uow = AsyncMock()
            
            # Mock search results
            mock_search_results = []
            for i in range(5):
                mock_product = MagicMock()
                mock_product.id = f"product-{i}"
                mock_product.name = f"Chicken Product {i}"
                mock_search_results.append(mock_product)
            
            mock_uow.products.list_top_similar_names.return_value = mock_search_results
            mock_bus = AsyncMock()
            mock_bus.uow = mock_uow
            mock_container.return_value.bootstrap.return_value = mock_bus
            
            # Mock TypeAdapter for search results
            mock_type_adapter = MagicMock()
            mock_type_adapter.dump_json.return_value = b'[{"id": "product-1", "name": "Chicken Product 1"}]'
            
            with patch('src.contexts.products_catalog.aws_lambda.search_product_similar_name.ProductListTypeAdapter', mock_type_adapter), \
                 patch('src.contexts.products_catalog.aws_lambda.search_product_similar_name.ApiProduct.from_domain') as mock_from_domain:
                
                # Mock ApiProduct.from_domain
                mock_from_domain.side_effect = lambda p: MagicMock(id=p.id, name=p.name)
                
                # Performance test - single search request
                async with PerformanceTimer() as timer:
                    result = await search_product_similar_name.async_handler(mock_search_event, {})
                
                # Verify response format
                assert result["statusCode"] == 200
                assert "body" in result
                assert "headers" in result
                
                # Performance assertion: Search endpoints get higher threshold (300ms)
                timer.assert_faster_than(0.3, "search_product_similar_name request")
                
                # Bulk performance test for search
                iterations = 3  # Fewer iterations for search endpoints
                async with PerformanceTimer() as bulk_timer:
                    for _ in range(iterations):
                        result = await search_product_similar_name.async_handler(mock_search_event, {})
                        assert result["statusCode"] == 200
                
                # Performance validations for search
                avg_time = bulk_timer.get_execution_time() / iterations
                assert avg_time < 0.25, f"Average search time {avg_time:.6f}s exceeds 250ms limit"
                
                throughput = iterations / bulk_timer.get_execution_time()
                assert throughput > 3, f"Search throughput {throughput:.1f} req/sec is below 3 req/sec minimum"

    async def test_fetch_product_source_name_collection_performance(self, mock_collection_event, mock_successful_auth_response):
        """Test fetch_product_source_name collection endpoint performance meets <200ms threshold."""
        
        with patch('src.contexts.products_catalog.aws_lambda.fetch_product_source_name.IAMProvider.get') as mock_auth, \
             patch('src.contexts.products_catalog.aws_lambda.fetch_product_source_name.Container') as mock_container:
            
            # Setup mocks for source collection endpoint
            mock_auth.return_value = mock_successful_auth_response
            mock_uow = AsyncMock()
            
            # Mock multiple sources for collection
            mock_sources = []
            for i in range(8):
                mock_source = MagicMock()
                mock_source.id = f"source-{i}"
                mock_source.name = f"Source {i}"
                mock_sources.append(mock_source)
            
            mock_uow.sources.query.return_value = mock_sources
            mock_bus = AsyncMock()
            mock_bus.uow = mock_uow
            mock_container.return_value.bootstrap.return_value = mock_bus
            
            with patch('src.contexts.products_catalog.aws_lambda.fetch_product_source_name.ApiSource.from_domain') as mock_from_domain:
                
                # Mock ApiSource.from_domain
                def mock_from_domain_side_effect(source):
                    mock_api_source = MagicMock()
                    mock_api_source.id = source.id
                    mock_api_source.name = source.name
                    return mock_api_source
                
                mock_from_domain.side_effect = mock_from_domain_side_effect
                
                # Performance test - single collection request
                async with PerformanceTimer() as timer:
                    result = await fetch_product_source_name.async_handler(mock_collection_event, {})
                
                # Verify response format
                assert result["statusCode"] == 200
                assert "body" in result
                assert "headers" in result
                
                # Performance assertion: Collection endpoints threshold (200ms)
                timer.assert_faster_than(0.2, "fetch_product_source_name collection request")
                
                # Bulk performance test
                iterations = 5
                async with PerformanceTimer() as bulk_timer:
                    for _ in range(iterations):
                        result = await fetch_product_source_name.async_handler(mock_collection_event, {})
                        assert result["statusCode"] == 200
                
                # Performance validations
                avg_time = bulk_timer.get_execution_time() / iterations
                assert avg_time < 0.15, f"Average collection time {avg_time:.6f}s exceeds 150ms limit"
                
                throughput = iterations / bulk_timer.get_execution_time()
                assert throughput > 5, f"Collection throughput {throughput:.1f} req/sec is below 5 req/sec minimum"

    async def test_lambda_helpers_overhead_benchmark(self, mock_single_product_event, mock_localstack_environment, performance_test_data):
        """Test that LambdaHelpers utilities add minimal overhead compared to direct parsing."""
        
        from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
        
        iterations = 1000
        
        # Baseline: Direct parameter parsing without helpers
        async with PerformanceTimer() as direct_timer:
            for _ in range(iterations):
                param = mock_single_product_event.get("pathParameters", {}).get("id")
                assert param == "product-123"
        
        # Test: LambdaHelpers parameter extraction
        async with PerformanceTimer() as lambda_helpers_timer:
            for _ in range(iterations):
                param = LambdaHelpers.extract_path_parameter(mock_single_product_event, "id")
                assert param == "product-123"
        
        # Calculate overhead
        lambda_helpers_avg = lambda_helpers_timer.get_execution_time() / iterations
        direct_avg = direct_timer.get_execution_time() / iterations
        overhead_ratio = lambda_helpers_avg / direct_avg if direct_avg > 0 else 1.0
        
        # LambdaHelpers should add reasonable overhead (less than 5x direct parsing)
        # Increased threshold to 5x since helper methods provide validation and error handling
        assert overhead_ratio < 5.0, f"LambdaHelpers overhead {overhead_ratio:.2f}x is too high"
        
        # Both should be very fast (under 5ms per operation)
        assert lambda_helpers_avg < 0.005, f"LambdaHelpers too slow: {lambda_helpers_avg:.6f}s per operation"
        assert direct_avg < 0.005, f"Direct parsing unexpectedly slow: {direct_avg:.6f}s per operation"

    def test_lambda_helpers_utilities_performance_suite(self, mock_collection_event, mock_single_product_event):
        """Comprehensive performance test for all LambdaHelpers utilities used in migrated endpoints."""
        from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
        
        iterations = 500
        performance_results = {}
        
        # Test extract_path_parameter performance
        with PerformanceTimer() as timer:
            for _ in range(iterations):
                param = LambdaHelpers.extract_path_parameter(mock_single_product_event, "id")
        performance_results["extract_path_parameter"] = timer.get_execution_time() / iterations
        
        # Test extract_user_id performance
        with PerformanceTimer() as timer:
            for _ in range(iterations):
                user_id = LambdaHelpers.extract_user_id(mock_single_product_event)
        performance_results["extract_user_id"] = timer.get_execution_time() / iterations
        
        # Test extract_query_parameters performance
        with PerformanceTimer() as timer:
            for _ in range(iterations):
                params = LambdaHelpers.extract_query_parameters(mock_collection_event)
        performance_results["extract_query_parameters"] = timer.get_execution_time() / iterations
        
        # Test extract_multi_value_query_parameters performance
        with PerformanceTimer() as timer:
            for _ in range(iterations):
                params = LambdaHelpers.extract_multi_value_query_parameters(mock_collection_event)
        performance_results["extract_multi_value_query_parameters"] = timer.get_execution_time() / iterations
        
        # Test is_localstack_environment performance
        with PerformanceTimer() as timer:
            for _ in range(iterations):
                is_local = LambdaHelpers.is_localstack_environment()
        performance_results["is_localstack_environment"] = timer.get_execution_time() / iterations
        
        # Validate all utilities are fast (under 0.5ms per operation)
        for utility_name, avg_time in performance_results.items():
            assert avg_time < 0.0005, f"{utility_name} too slow: {avg_time:.6f}s per operation"
        
        # Print performance summary for monitoring
        print("\n=== LambdaHelpers Performance Summary ===")
        for utility_name, avg_time in sorted(performance_results.items()):
            print(f"{utility_name}: {avg_time*1000:.3f}ms avg per operation")
        
        # Validate total utility overhead is minimal
        total_utility_time = sum(performance_results.values())
        assert total_utility_time < 0.003, f"Combined utility overhead {total_utility_time:.6f}s too high" 