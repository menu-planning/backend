"""
Shared test fixtures for API schemas testing.

This module provides shared test fixtures for both entities and commands
API schema testing to avoid fixture name collisions.
"""

import pytest

# Import all necessary counter reset functions
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    reset_api_recipe_counters,
)

from tests.contexts.recipes_catalog.data_factories.recipe.recipe_domain_factories import (
    reset_recipe_domain_counters,
)

from tests.contexts.recipes_catalog.data_factories.recipe.recipe_orm_factories import (
    reset_recipe_orm_counters,
)

# Import additional counter reset functions for comprehensive coverage
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import (
    reset_api_ingredient_counters,
)

from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_rating_data_factories import (
    reset_api_rating_counters,
)

from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    reset_api_meal_counters,
)

from tests.contexts.recipes_catalog.data_factories.meal.meal_domain_factories import (
    reset_meal_domain_counters,
)

from tests.contexts.recipes_catalog.data_factories.meal.meal_orm_factories import (
    reset_meal_orm_counters,
)


# =============================================================================
# SHARED TEST ISOLATION FIXTURE
# =============================================================================

@pytest.fixture(autouse=True, scope="function")
def reset_all_counters():
    """
    Reset all API, ORM, and domain counters before each test for complete isolation.
    
    This fixture ensures that all global state used by data factories is reset
    before and after each test, preventing test pollution between test files.
    """
    # Reset all counters before test execution
    reset_api_recipe_counters()
    reset_api_ingredient_counters()
    reset_api_rating_counters()
    reset_api_meal_counters()
    reset_recipe_domain_counters()
    reset_recipe_orm_counters()
    reset_meal_domain_counters()
    reset_meal_orm_counters()
    
    yield
    
    # Reset all counters after test execution for extra safety
    reset_api_recipe_counters()
    reset_api_ingredient_counters()
    reset_api_rating_counters()
    reset_api_meal_counters()
    reset_recipe_domain_counters()
    reset_recipe_orm_counters()
    reset_meal_domain_counters()
    reset_meal_orm_counters()