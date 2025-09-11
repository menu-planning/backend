"""
Comprehensive test suite for ApiMeal following seedwork patterns.
Uses extensive data factories and realistic scenarios for complete coverage.

This test suite provides:
- Complete conversion method testing (from_domain, to_domain, from_orm_model, to_orm_kwargs)
- Comprehensive field validation testing
- Round-trip conversion validation
- Error handling and edge case scenarios
- JSON serialization/deserialization testing
- Performance testing with bulk operations
- Integration testing with base classes
- Realistic data scenario testing
- Computed property validation
- Pydantic configuration testing

All tests use deterministic data factories for consistent behavior.
Tests focus on behavior validation, not implementation details.
"""

from uuid import uuid4

import pytest
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal_with_incorrect_computed_properties,
    create_api_meal_with_max_recipes,
    create_api_meal_without_recipes,
    create_complex_api_meal,
    create_family_api_meal,
    create_high_protein_api_meal,
    create_holiday_api_meal,
    create_meal_collection,
    create_minimal_api_meal,
    create_quick_api_meal,
    create_simple_api_meal,
    create_vegetarian_api_meal,
)
from tests.contexts.recipes_catalog.data_factories.meal.meal_domain_factories import (
    create_complex_meal,
    create_meal,
)
from tests.contexts.recipes_catalog.data_factories.meal.meal_orm_factories import (
    create_meal_orm,
)

# =============================================================================
# FIXTURES AND TEST DATA
# =============================================================================


@pytest.fixture
def minimal_api_meal():
    """Minimal meal for basic testing."""
    return create_minimal_api_meal()


@pytest.fixture
def simple_api_meal():
    """Simple meal for basic testing."""
    return create_simple_api_meal()


@pytest.fixture
def complex_api_meal():
    """Complex meal with many nested objects."""
    return create_complex_api_meal()


@pytest.fixture
def domain_meal():
    """Domain meal for conversion tests - created directly from domain factories."""
    return create_meal()


@pytest.fixture
def complex_meal():
    """Complex meal with many nested objects."""
    return create_complex_meal()


@pytest.fixture
def real_orm_meal():
    """Real ORM meal for testing - no mocks needed."""
    return create_meal_orm(
        name="Test Meal for ORM Conversion",
        description="Real ORM meal for testing conversion methods",
        notes="Real notes for testing",
        author_id=str(uuid4()),
        menu_id=str(uuid4()),
    )


@pytest.fixture
def edge_case_meals():
    """Edge case meals for comprehensive testing."""
    return {
        "empty_recipes": create_api_meal_without_recipes(),
        "max_recipes": create_api_meal_with_max_recipes(),
        "incorrect_computed_properties": create_api_meal_with_incorrect_computed_properties(),
        "minimal": create_minimal_api_meal(),
        "vegetarian": create_vegetarian_api_meal(),
        "high_protein": create_high_protein_api_meal(),
        "quick": create_quick_api_meal(),
        "holiday": create_holiday_api_meal(),
        "family": create_family_api_meal(),
    }


@pytest.fixture
def meal_collection():
    """Collection of diverse meals for testing."""
    return create_meal_collection(count=10)
