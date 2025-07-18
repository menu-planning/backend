"""
Performance validation tests for ApiUser schema validation.

Following Phase 1 patterns: behavior-focused approach, comprehensive performance testing,
and optimization validation.

Focus: Test performance behavior and validation of operation timing.
"""

import pytest
import time
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import ApiUser

# Import data factories
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_role_data_factories import create_admin_role, create_premium_user_role, create_user_role
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_user_data_factories import (
    create_api_user,
    create_test_user_dataset,
    create_role_validation_performance_dataset,
)


# =============================================================================
# PERFORMANCE VALIDATION TESTS
# =============================================================================

class TestApiUserPerformanceValidation:
    """Test comprehensive performance validation for ApiUser operations."""

    def test_four_layer_conversion_performance(self):
        """Test performance of four-layer conversion operations."""
        # Create comprehensive user with roles directly
        admin_role = create_admin_role()
        user_role = create_user_role()
        premium_role = create_premium_user_role()
        
        comprehensive_user = create_api_user(
            id=str(uuid4()),
            roles=frozenset([admin_role, user_role, premium_role])
        )
        
        # Test API → domain conversion performance
        start_time = time.perf_counter()
        for _ in range(1000):
            domain_user = comprehensive_user.to_domain()
        end_time = time.perf_counter()
        
        api_to_domain_time = (end_time - start_time) / 1000
        assert api_to_domain_time < 0.001  # Should be under 1ms per conversion
        
        # Test domain → API conversion performance
        start_time = time.perf_counter()
        for _ in range(1000):
            api_user = ApiUser.from_domain(domain_user)
        end_time = time.perf_counter()
        
        domain_to_api_time = (end_time - start_time) / 1000
        assert domain_to_api_time < 0.001  # Should be under 1ms per conversion

    def test_json_validation_performance_with_large_datasets(self):
        """Test JSON validation performance with large user datasets."""
        # Create large dataset
        dataset = create_test_user_dataset(user_count=100)
        
        start_time = time.perf_counter()
        
        # Validate each user from dataset
        for user_data in dataset["users"]:
            api_user = ApiUser.model_validate(user_data)
            assert isinstance(api_user, ApiUser)
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance requirement: < 50ms for 100 users
        assert execution_time < 50.0, f"JSON validation performance failed: {execution_time:.2f}ms > 50ms"

    def test_role_validation_performance(self):
        """Test role validation performance with complex data."""
        # Create users with complex role configurations
        complex_users = create_role_validation_performance_dataset(count=100)
        
        start_time = time.perf_counter()
        
        # Perform validation operations
        for user in complex_users:
            # JSON serialization
            json_data = user.model_dump_json()
            # JSON deserialization
            recreated = ApiUser.model_validate_json(json_data)
            assert recreated.id == user.id
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance requirement: < 100ms for 100 complex users
        assert execution_time < 100.0, f"Role validation performance failed: {execution_time:.2f}ms > 100ms"

    def test_bulk_conversion_performance(self):
        """Test performance of bulk conversion operations."""
        # Create many users directly
        users = []
        for i in range(50):
            user = create_api_user(
                id=str(uuid4()),
                roles=frozenset([create_user_role()])
            )
            users.append(user)
        
        start_time = time.perf_counter()
        
        # Perform bulk domain conversions
        domain_users = [user.to_domain() for user in users]
        
        # Perform bulk API conversions
        converted_back = [ApiUser.from_domain(domain) for domain in domain_users]
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance requirement: < 25ms for 50 users (bulk operations)
        assert execution_time < 25.0, f"Bulk conversion performance failed: {execution_time:.2f}ms > 25ms"
        
        # Verify conversion integrity
        assert len(converted_back) == len(users)
        for i, user in enumerate(converted_back):
            assert user.id == users[i].id 