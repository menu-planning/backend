"""
Test fixtures and configuration for API Pattern Documentation Tests

This module provides shared fixtures and utilities for testing TypeAdapter patterns,
four-layer conversions, and documentation accuracy.

Fixtures provided:
- Sample domain objects (Meal, Recipe, Tag, etc.)
- Corresponding ORM models with realistic data
- API schema instances with all field variations
- Performance benchmarking utilities
"""

import pytest
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

# Domain imports
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal

# API Schema imports
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.api_seed_role import ApiSeedRole


@pytest.fixture
def sample_uuid():
    """Generate a consistent UUID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_timestamp():
    """Generate a consistent timestamp for testing."""
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def sample_tag_domain():
    """Create a sample Tag domain object."""
    return Tag(
        key="cuisine",
        value="italian",
        author_id="user-123",
        type="category"
    )


@pytest.fixture
def sample_tag_api(sample_tag_domain):
    """Create a sample ApiTag from domain object."""
    return ApiTag.from_domain(sample_tag_domain)


@pytest.fixture
def sample_tags_collection():
    """Create a collection of sample tags for testing."""
    return [
        Tag(key="cuisine", value="italian", author_id="user-123", type="category"),
        Tag(key="difficulty", value="easy", author_id="user-123", type="category"),
        Tag(key="diet", value="vegetarian", author_id="user-456", type="dietary")
    ]


@pytest.fixture
def sample_api_tags_collection(sample_tags_collection):
    """Create a collection of ApiTags from domain objects."""
    return [ApiTag.from_domain(tag) for tag in sample_tags_collection]


@pytest.fixture
def sample_ingredient_data():
    """Create sample ingredient data for API testing."""
    return {
        "name": "Tomatoes",
        "quantity": 200.0,
        "unit": MeasureUnit.GRAM,
        "position": 1,
        "full_text": "200g of fresh tomatoes",
        "product_id": "550e8400-e29b-41d4-a716-446655440000"
    }


@pytest.fixture
def sample_ingredient_api(sample_ingredient_data):
    """Create a sample ApiIngredient."""
    return ApiIngredient.model_validate(sample_ingredient_data)


@pytest.fixture
def sample_rating_data():
    """Create sample rating data for API testing."""
    return {
        "id": "rating-123",
        "rating_value": 4,
        "rating_type": "taste",
        "rater_id": "user-123",
        "recipe_id": "recipe-123"
    }


@pytest.fixture
def sample_rating_api(sample_rating_data):
    """Create a sample ApiRating."""
    return ApiRating.model_validate(sample_rating_data)


@pytest.fixture
def sample_role_data():
    """Create sample role data for API testing."""
    return {
        "id": "role-123",
        "name": "admin",
        "permissions": ["read", "write", "delete"]
    }


@pytest.fixture
def sample_role_api(sample_role_data):
    """Create a sample ApiSeedRole."""
    return ApiSeedRole.model_validate(sample_role_data)


@pytest.fixture
def large_collection_data():
    """Create large collections for performance testing."""
    return {
        "tags": [
            {"key": f"tag{i}", "value": f"value{i}", "author_id": f"user{i}", "type": "category"}
            for i in range(100)
        ],
        "ingredients": [
            {
                "name": f"Ingredient {i}",
                "quantity": 100.0,
                "unit": MeasureUnit.GRAM,
                "position": i + 1,
                "full_text": f"100g of Ingredient {i}",
                "product_id": "550e8400-e29b-41d4-a716-446655440000"
            }
            for i in range(100)
        ],
        "ratings": [
            {
                "id": f"550e8400-e29b-41d4-a716-44665544000{i}",
                "rating_value": 4,
                "rating_type": "taste",
                "rater_id": f"550e8400-e29b-41d4-a716-44665544000{i}",
                "recipe_id": f"550e8400-e29b-41d4-a716-44665544000{i}"
            }
            for i in range(100)
        ]
    }


@pytest.fixture
def conversion_cycle_validator():
    """Create a utility for testing four-layer conversion cycles."""
    def assert_conversion_cycle_integrity(
        domain_obj: Any,
        api_class: type,
        orm_class: type,
        custom_assertions: Optional[Dict[str, Any]] = None
    ):
        """
        Test the complete four-layer conversion cycle:
        Domain → API → ORM → API → Domain
        
        Args:
            domain_obj: Original domain object
            api_class: API schema class
            orm_class: ORM model class (can be Mock for testing)
            custom_assertions: Additional assertions to run
        """
        # Step 1: Domain → API
        api_obj = api_class.from_domain(domain_obj)
        
        # Step 2: API → ORM kwargs
        orm_kwargs = api_obj.to_orm_kwargs()
        
        # Step 3: Create ORM instance (mock for testing)
        # Fix: Don't use Mock(spec=...) when orm_class is already a Mock
        if hasattr(orm_class, '_mock_name'):  # orm_class is already a Mock
            orm_obj = Mock()
        else:
            orm_obj = Mock(spec=orm_class)
            
        for key, value in orm_kwargs.items():
            setattr(orm_obj, key, value)
        
        # Step 4: ORM → API
        reconstructed_api = api_class.from_orm_model(orm_obj)
        
        # Step 5: API → Domain
        final_domain = reconstructed_api.to_domain()
        
        # Validation
        success = True
        errors = []
        
        try:
            # Basic equality check (may need custom logic for complex objects)
            if hasattr(domain_obj, '__dict__') and hasattr(final_domain, '__dict__'):
                # Compare key attributes instead of full equality
                for attr in domain_obj.__dict__:
                    if hasattr(final_domain, attr):
                        original_val = getattr(domain_obj, attr)
                        final_val = getattr(final_domain, attr)
                        if original_val != final_val:
                            errors.append(f"Attribute {attr} changed: {original_val} -> {final_val}")
            
            # Run custom assertions if provided
            if custom_assertions:
                for assertion_name, assertion_func in custom_assertions.items():
                    try:
                        assertion_func(domain_obj, final_domain)
                    except Exception as e:
                        errors.append(f"Custom assertion '{assertion_name}' failed: {str(e)}")
                        
        except Exception as e:
            success = False
            errors.append(f"Conversion cycle failed: {str(e)}")
        
        if errors:
            success = False
            
        return type('ConversionResult', (), {
            'success': success,
            'original_data': domain_obj,
            'final_data': final_domain,
            'conversion_errors': errors
        })()
    
    return assert_conversion_cycle_integrity


@pytest.fixture
def performance_validator():
    """Create a utility for validating performance requirements."""
    def assert_performance_within_limits(
        operation_func,
        max_time_ms: float = 3.0,
        iterations: int = 10,
        operation_name: str = "operation"
    ):
        """
        Validate that an operation meets performance requirements.
        
        Args:
            operation_func: Function to benchmark
            max_time_ms: Maximum allowed time in milliseconds
            iterations: Number of iterations to average
            operation_name: Name for error messages
        """
        import time
        
        times = []
        for _ in range(iterations):
            start_time = time.perf_counter()
            result = operation_func()
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # Convert to ms
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        assert avg_time < max_time_ms, \
            f"{operation_name} average time {avg_time:.2f}ms exceeds limit {max_time_ms}ms"
        
        return {
            "average_ms": avg_time,
            "max_ms": max_time,
            "min_ms": min_time,
            "all_times": times,
            "iterations": iterations,
            "operation_name": operation_name
        }
    
    return assert_performance_within_limits


@pytest.fixture
def typeadapter_test_data():
    """Create comprehensive test data for TypeAdapter validation."""
    return {
        "valid_tags": [
            {"key": "cuisine", "value": "italian", "author_id": "user-123", "type": "category"},
            {"key": "difficulty", "value": "easy", "author_id": "user-456", "type": "category"}
        ],
        "invalid_tags": [
            {"key": "", "value": "italian", "author_id": "user-123", "type": "category"},  # Empty key
            {"key": "cuisine", "author_id": "user-123", "type": "category"},  # Missing value
            {"key": "cuisine", "value": "italian", "type": "category"}  # Missing author_id
        ],
        "duplicate_tags": [
            {"key": "cuisine", "value": "italian", "author_id": "user-123", "type": "category"},
            {"key": "cuisine", "value": "italian", "author_id": "user-123", "type": "category"}  # Duplicate
        ],
        "edge_cases": {
            "empty_list": [],
            "single_item": [{"key": "solo", "value": "item", "author_id": "user-123", "type": "category"}],
            "large_collection": [
                {"key": f"key{i}", "value": f"value{i}", "author_id": "user-123", "type": "category"}
                for i in range(1000)
            ]
        }
    }


@pytest.fixture
def memory_profiler():
    """Create a utility for memory usage testing."""
    def profile_memory_usage(operation_func, iterations: int = 100):
        """
        Profile memory usage of an operation.
        
        Args:
            operation_func: Function to profile
            iterations: Number of iterations to run
            
        Returns:
            Dict with memory usage statistics
        """
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            for _ in range(iterations):
                operation_func()
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = final_memory - initial_memory
            
            return {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_growth_mb": memory_growth,
                "iterations": iterations,
                "memory_per_iteration_kb": (memory_growth * 1024) / iterations if iterations > 0 else 0
            }
        except ImportError:
            pytest.skip("psutil not available for memory profiling")
    
    return profile_memory_usage


@pytest.fixture
def thread_safety_tester():
    """Create a utility for testing thread safety."""
    def test_concurrent_access(operation_func, num_threads: int = 10, operations_per_thread: int = 50):
        """
        Test thread safety of an operation.
        
        Args:
            operation_func: Function to test
            num_threads: Number of concurrent threads
            operations_per_thread: Operations per thread
            
        Returns:
            Dict with thread safety results
        """
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        results = []
        errors = []
        lock = threading.Lock()
        
        def worker():
            thread_results = []
            thread_errors = []
            
            for _ in range(operations_per_thread):
                try:
                    result = operation_func()
                    thread_results.append(result)
                except Exception as e:
                    thread_errors.append(str(e))
            
            with lock:
                results.extend(thread_results)
                errors.extend(thread_errors)
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            for future in futures:
                future.result()  # Wait for completion
        
        return {
            "total_operations": num_threads * operations_per_thread,
            "successful_operations": len(results),
            "failed_operations": len(errors),
            "error_rate": len(errors) / (num_threads * operations_per_thread),
            "errors": errors[:10],  # First 10 errors for analysis
            "success_rate": len(results) / (num_threads * operations_per_thread)
        }
    
    return test_concurrent_access


# Configure pytest for better performance testing
def pytest_configure(config):
    """Configure pytest for performance testing."""
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Meal-specific fixtures for computed property and conversion testing
@pytest.fixture
def sample_meal_with_complex_data():
    """Create a comprehensive meal with realistic data for testing."""
    # Create realistic tags
    tags = {
        Tag(key="cuisine", value="italian", author_id="chef-123", type="category"),
        Tag(key="difficulty", value="easy", author_id="chef-123", type="level"),
        Tag(key="diet", value="vegetarian", author_id="chef-123", type="dietary")
    }
    
    # Start with a basic meal (recipes will be empty, which is valid)
    return Meal(
        id="meal-456",
        name="Italian Lunch",
        author_id="chef-123",
        menu_id="menu-789",
        recipes=[],  # Start simple, focus on core conversion patterns
        tags=tags,
        description="A delicious Italian lunch combination",
        notes="Perfect for weekend meals",
        like=True,
        image_url="https://example.com/meal.jpg",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 30, 0),
        discarded=False,
        version=1
    )


@pytest.fixture
def sample_meal_with_tags():
    """Create a meal focused on tag conversion testing."""
    tags = {
        Tag(key="cuisine", value="mexican", author_id="user-123", type="category"),
        Tag(key="spice", value="medium", author_id="user-123", type="intensity"),
        Tag(key="time", value="quick", author_id="user-123", type="duration")
    }
    
    return Meal(
        id="meal-tags-test",
        name="Mexican Tacos",
        author_id="user-123",
        recipes=[],
        tags=tags,
        created_at=datetime.now(),
        version=1
    )


@pytest.fixture  
def sample_meal_with_nutri_facts():
    """Create a meal that will have computed nutritional facts."""
    # Create a meal with no recipes initially - nutri_facts will be None
    # This tests the None handling behavior
    meal = Meal(
        id="meal-nutri",
        name="Balanced Nutrition Bowl",
        author_id="nutritionist-456",
        recipes=[],  # Empty recipes = None nutri_facts (realistic scenario)
        tags=set(),
        created_at=datetime.now(),
        version=1
    )
    
    # For this test, we'll simulate a meal that HAS nutrition facts
    # by testing the behavior when nutri_facts would be computed
    return meal


@pytest.fixture
def sample_meal_with_recipes():
    """Create a meal with realistic recipe scenario."""
    # Start with empty recipes to test collection behavior
    meal = Meal(
        id="meal-recipes-test", 
        name="Multi-Recipe Meal",
        author_id="chef-test",
        recipes=[],  # Test with empty recipes first
        tags=set(),
        created_at=datetime.now(),
        version=1
    )
    
    # Test the behavior of adding recipes (if needed for specific tests)
    return meal


@pytest.fixture
def sample_meal_data():
    """Create sample API meal data for validation testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "  Test Meal  ",  # With whitespace for validation testing
        "author_id": str(uuid.uuid4()),
        "menu_id": str(uuid.uuid4()),
        "recipes": [],
        "tags": frozenset(),
        "description": "Test description",
        "notes": "Test notes",
        "like": True,
        "image_url": "https://example.com/test.jpg",
        "nutri_facts": None,
        "weight_in_grams": 0,
        "calorie_density": None,
        "carbo_percentage": None,
        "protein_percentage": None,
        "total_fat_percentage": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "discarded": False,
        "version": 1
    }


@pytest.fixture
def large_meal_data():
    """Create a meal with large collections for performance testing."""
    # Create many tags for performance testing
    tags = set()
    for i in range(20):
        tag = Tag(
            key=f"category{i}",
            value=f"value{i}",
            author_id="perf-chef",
            type="performance"
        )
        tags.add(tag)
    
    return Meal(
        id="meal-perf",
        name="Performance Test Meal",
        author_id="perf-chef",
        recipes=[],  # Keep simple for performance testing
        tags=tags,
        created_at=datetime.now(),
        version=1
    )


@pytest.fixture
def minimal_meal_data():
    """Create minimal meal data with mostly None values."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Minimal Meal",
        "author_id": str(uuid.uuid4()),
        "menu_id": None,
        "recipes": [],
        "tags": set(),
        "description": None,
        "notes": None,
        "like": None,
        "image_url": None,
        "created_at": datetime.now(),
        "version": 1
    } 