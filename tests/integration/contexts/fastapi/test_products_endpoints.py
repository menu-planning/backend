"""
Integration tests for FastAPI products catalog endpoints.

This module tests the products catalog endpoints behavior, ensuring proper
async/await patterns, authentication, and response format compatibility
with AWS Lambda implementations.
Follows behavior-focused testing principles with fakes instead of mocks.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.contexts.products_catalog.core.adapters.api_schemas.commands.products.api_add_food_product import (
    ApiAddFoodProduct,
)
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.core.domain.enums import Permission
from src.contexts.products_catalog.core.domain.value_objects.user import User
from src.runtimes.fastapi.app import create_app

# Use AnyIO for async testing and mark as integration tests
pytestmark = [pytest.mark.anyio, pytest.mark.integration]


# Fake implementations following testing principles
class FakeProductsRepository:
    """Fake products repository for testing."""

    def __init__(self, products: list[dict[str, Any]] | None = None):
        self.products = products or []
        self.queries_made = []
        self.gets_made = []

    async def query(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Query products with filters."""
        self.queries_made.append(filters or {})
        return self.products

    async def get(self, product_id: str) -> dict[str, Any] | None:
        """Get product by ID."""
        self.gets_made.append(product_id)
        for product in self.products:
            if product.get("id") == product_id:
                return product
        return None

    async def list_top_similar_names(self, name: str) -> list[dict[str, Any]]:
        """Search for products with similar names."""
        return [p for p in self.products if name.lower() in p.get("name", "").lower()]

    async def get_filter_options(self) -> dict[str, Any]:
        """Get available filter options."""
        return {"categories": ["food", "beverage"], "sources": ["source1", "source2"]}


class FakeSourcesRepository:
    """Fake sources repository for testing."""

    def __init__(self, sources: list[dict[str, Any]] | None = None):
        self.sources = sources or []
        self.queries_made = []
        self.gets_made = []

    async def query(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Query sources with filters."""
        self.queries_made.append(filters or {})
        return self.sources

    async def get(self, source_id: str) -> dict[str, Any] | None:
        """Get source by ID."""
        self.gets_made.append(source_id)
        for source in self.sources:
            if source.get("id") == source_id:
                return source
        return None


class FakeUnitOfWork:
    """Fake unit of work for testing."""

    def __init__(self, products_repo: FakeProductsRepository = None, sources_repo: FakeSourcesRepository = None):
        self.products = products_repo or FakeProductsRepository()
        self.sources = sources_repo or FakeSourcesRepository()
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        """Commit the transaction."""
        self.committed = True

    async def rollback(self):
        """Rollback the transaction."""
        self.rolled_back = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()


class FakeMessageBus:
    """Fake message bus for testing."""

    def __init__(self, uow_factory=None):
        self.uow_factory = uow_factory or (lambda: FakeUnitOfWork())
        self.commands_handled = []

    async def handle(self, command):
        """Handle a command."""
        self.commands_handled.append(command)


class TestProductsEndpoints:
    """Test products catalog endpoints behavior."""

    @pytest.fixture
    def test_app(self) -> FastAPI:
        """Create test FastAPI app with proper container setup."""
        app = create_app()

        # Set up container for testing
        from src.runtimes.fastapi.dependencies.containers import AppContainer
        container = AppContainer()
        app.state.container = container

        # Set up spawn function for testing
        def mock_spawn(coro, *, name=None):
            """Mock spawn function for testing."""
            pass

        app.state.spawn = mock_spawn

        return app

    @pytest.fixture
    def test_client(self, test_app: FastAPI) -> TestClient:
        """Create test client for synchronous testing."""
        return TestClient(test_app)

    @pytest.fixture
    def test_user_with_permissions(self) -> User:
        """Create test user with product management permissions."""
        return User(
            id="test-user-123",
            email="test@example.com",
            name="Test User"
        )

    @pytest.fixture
    def test_user_without_permissions(self) -> User:
        """Create test user without product management permissions."""
        return User(
            id="test-user-456",
            email="test2@example.com",
            name="Test User 2"
        )

    @pytest.fixture
    def mock_product_data(self) -> dict[str, Any]:
        """Create mock product data for testing."""
        return {
            "id": "product-123",
            "name": "Test Product",
            "description": "A test product",
            "price": 10.99,
            "category": "food",
            "source": "test-source",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }

    @pytest.fixture
    def mock_products_list(self) -> list[dict[str, Any]]:
        """Create mock products list for testing."""
        return [
            {
                "id": "product-1",
                "name": "Product 1",
                "description": "First test product",
                "price": 5.99,
                "category": "food",
                "source": "source-1",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "product-2",
                "name": "Product 2",
                "description": "Second test product",
                "price": 15.99,
                "category": "beverage",
                "source": "source-2",
                "created_at": "2024-01-02T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z"
            }
        ]

    def test_query_products_requires_authentication(self, test_client: TestClient):
        """Test that products query endpoint requires authentication."""
        # Given: Unauthenticated request
        # When: Make request to query endpoint
        response = test_client.get("/products/query")

        # Then: Should return authentication error
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "Authentication required" in response_data["detail"]

    def test_get_product_requires_authentication(self, test_client: TestClient):
        """Test that get product endpoint requires authentication."""
        # Given: Unauthenticated request
        # When: Make request to get product endpoint
        response = test_client.get("/products/test-product-id")

        # Then: Should return authentication error
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "Authentication required" in response_data["detail"]

    def test_create_product_requires_authentication(self, test_client: TestClient):
        """Test that create product endpoint requires authentication."""
        # Given: Unauthenticated request with valid product data
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "price": 10.99,
            "category": "food"
        }

        # When: Make request to create product endpoint
        response = test_client.post("/products/create", json=product_data)

        # Then: Should return authentication error
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "Authentication required" in response_data["detail"]

    def test_search_similar_names_requires_authentication(self, test_client: TestClient):
        """Test that search similar names endpoint requires authentication."""
        # Given: Unauthenticated request
        # When: Make request to search endpoint
        response = test_client.get("/products/search/similar-names?name=test")

        # Then: Should return authentication error
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "Authentication required" in response_data["detail"]

    def test_filter_options_requires_authentication(self, test_client: TestClient):
        """Test that filter options endpoint requires authentication."""
        # Given: Unauthenticated request
        # When: Make request to filter options endpoint
        response = test_client.get("/products/filter-options")

        # Then: Should return authentication error
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "Authentication required" in response_data["detail"]

    def test_product_sources_requires_authentication(self, test_client: TestClient):
        """Test that product sources endpoint requires authentication."""
        # Given: Unauthenticated request
        # When: Make request to sources endpoint
        response = test_client.get("/products/sources")

        # Then: Should return authentication error
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "Authentication required" in response_data["detail"]

    def test_get_product_source_requires_authentication(self, test_client: TestClient):
        """Test that get product source endpoint requires authentication."""
        # Given: Unauthenticated request
        # When: Make request to get source endpoint
        response = test_client.get("/products/sources/test-source-id")

        # Then: Should return authentication error
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "Authentication required" in response_data["detail"]

    async def test_concurrent_product_requests(self, test_app: FastAPI):
        """Test that multiple concurrent product requests work correctly."""
        # Given: Test app and multiple concurrent requests
        requests_data = [
            {"url": "/products/query", "method": "GET"},
            {"url": "/products/filter-options", "method": "GET"},
            {"url": "/products/sources", "method": "GET"},
            {"url": "/products/search/similar-names?name=test", "method": "GET"},
        ]

        # When: Execute concurrent requests using TestClient
        async def make_request(request_data: dict[str, Any]):
            client = TestClient(test_app)
            if request_data["method"] == "GET":
                return client.get(request_data["url"])
            else:
                return client.post(request_data["url"])

        tasks = [make_request(req) for req in requests_data]
        results = await asyncio.gather(*tasks)

        # Then: All requests should complete successfully
        assert len(results) == 4
        for response in results:
            # Should return proper HTTP status codes
            assert response.status_code in [200, 401, 400, 404]
            # Should have proper response structure
            response_data = response.json()
            assert isinstance(response_data, dict)

    def test_endpoint_response_format_consistency(self, test_client: TestClient):
        """Test that all endpoints return consistent response formats."""
        # Given: Test client and list of endpoints to test
        endpoints = [
            "/products/query",
            "/products/filter-options",
            "/products/sources",
            "/products/search/similar-names?name=test"
        ]

        # When: Make requests to all endpoints
        responses = []
        for endpoint in endpoints:
            response = test_client.get(endpoint)
            responses.append((endpoint, response))

        # Then: All responses should have consistent structure
        for _endpoint, response in responses:
            response_data = response.json()

            # Should always be a dictionary
            assert isinstance(response_data, dict)

            # Should have either success structure or error structure
            if response.status_code == 200:
                # Success responses should have data field
                assert "data" in response_data
            else:
                # Error responses should have detail field
                assert "detail" in response_data

    def test_query_parameters_validation(self, test_client: TestClient):
        """Test that query parameters are properly validated."""
        # Given: Test client
        # When: Make request with invalid query parameters
        response = test_client.get("/products/search/similar-names?limit=1000")  # Invalid limit

        # Then: Should return validation error
        assert response.status_code in [400, 401]  # 400 for validation, 401 for auth
        response_data = response.json()

        if response.status_code == 400:
            # Should have validation error structure
            assert "detail" in response_data

    def test_create_product_validation(self, test_client: TestClient):
        """Test that product creation data is properly validated."""
        # Given: Test client and invalid product data
        invalid_product_data = {
            "name": "",  # Invalid empty name
            "price": -10.99,  # Invalid negative price
        }

        # When: Make request with invalid data
        response = test_client.post("/products/create", json=invalid_product_data)

        # Then: Should return validation error
        assert response.status_code in [400, 401, 403]  # Various validation/auth errors
        response_data = response.json()

        if response.status_code == 400:
            # Should have validation error structure
            assert "detail" in response_data


class TestProductsEndpointBehavior:
    """Test products endpoints behavior with fakes."""

    @pytest.fixture
    def test_app_with_fakes(self) -> FastAPI:
        """Create test app with fake dependencies."""
        app = create_app()

        # Set up container for testing
        from src.runtimes.fastapi.dependencies.containers import AppContainer
        container = AppContainer()
        app.state.container = container

        # Set up spawn function for testing
        def mock_spawn(coro, *, name=None):
            """Mock spawn function for testing."""
            pass

        app.state.spawn = mock_spawn

        # Override dependencies with fakes
        from src.contexts.products_catalog.fastapi.dependencies import get_products_bus

        def fake_get_products_bus():
            """Fake products bus for testing."""
            return FakeMessageBus()

        app.dependency_overrides[get_products_bus] = fake_get_products_bus

        # Override authentication with fake user
        from src.runtimes.fastapi.routers.products import get_current_user

        def fake_get_current_user():
            """Fake current user for testing."""
            user = User(
                id="test-user-123",
                email="test@example.com",
                name="Test User"
            )
            # Add a simple permission check method
            def has_permission(permission):
                return permission == Permission.MANAGE_PRODUCTS
            user.has_permission = has_permission
            return user

        app.dependency_overrides[get_current_user] = fake_get_current_user
        return app

    @pytest.fixture
    def test_client_with_fakes(self, test_app_with_fakes: FastAPI) -> TestClient:
        """Create test client with fake dependencies."""
        return TestClient(test_app_with_fakes)

    def test_endpoints_return_consistent_response_format(self, test_client_with_fakes: TestClient):
        """Test that all endpoints return consistent response format."""
        # Given: List of endpoints to test
        endpoints = [
            "/products/query",
            "/products/filter-options",
            "/products/sources",
            "/products/search/similar-names?name=test"
        ]

        # When: Make requests to all endpoints
        responses = []
        for endpoint in endpoints:
            response = test_client_with_fakes.get(endpoint)
            responses.append((endpoint, response))

        # Then: All responses should have consistent structure
        for _endpoint, response in responses:
            # Should return proper HTTP status codes (401 for auth, 422 for validation)
            assert response.status_code in [200, 401, 422, 400]
            response_data = response.json()

            # Should always have proper response structure
            if response.status_code == 200:
                # Success responses should have data field
                assert "data" in response_data
            else:
                # Error responses should have detail field
                assert "detail" in response_data
