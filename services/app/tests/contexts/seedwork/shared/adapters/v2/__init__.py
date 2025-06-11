"""
Convenient imports for seedwork v2 test utilities

This module provides a single import point for all test utilities,
making it easy to use the organized test infrastructure components.

Usage examples:

    # Import specific components
    from tests.contexts.seedwork.shared.adapters.v2 import (
        TestMealEntity, TestRecipeEntity, create_test_meal, TEST_MEAL_FILTER_MAPPERS
    )
    
    # Import groups of related components
    from tests.contexts.seedwork.shared.adapters.v2.test_models import *
    from tests.contexts.seedwork.shared.adapters.v2.test_data_factories import *
    
    # Use in test files
    async def test_meal_repository(meal_repository):
        meal = create_test_meal(name="Test Meal")
        await meal_repository.add(meal)
        # ...

All fixtures are auto-discovered from conftest.py and don't need explicit imports.
"""

# =============================================================================
# Core Constants
# =============================================================================
from .test_models import TEST_SCHEMA

# =============================================================================
# SQLAlchemy Models
# =============================================================================
from .test_models import (
    # Composite types
    TestNutriFactsSaModel,
    
    # Association tables
    test_meals_tags_association,
    test_recipes_tags_association, 
    test_self_ref_friends_association,
    
    # Main models
    TestTagSaModel,
    TestRatingSaModel,
    TestIngredientSaModel,
    TestRecipeSaModel,
    TestMealSaModel,
    
    # Edge case models
    TestCircularModelA,
    TestCircularModelB,
    TestSelfReferentialModel,
)

# =============================================================================
# Domain Entities
# =============================================================================
from .test_entities import (
    TestMealEntity,
    TestRecipeEntity,
    TestCircularEntityA,
    TestCircularEntityB,
    TestSelfReferentialEntity,
    TestTagEntity,
    TestRatingEntity,
    TestIngredientEntity,
)

# =============================================================================
# Data Mappers
# =============================================================================
from .test_mappers import (
    TestMealMapper,
    TestRecipeMapper,
    TestCircularMapperA,
    TestCircularMapperB,
    TestSelfReferentialMapper,
    TestTagMapper,
    TestRatingMapper,
    TestIngredientMapper,
)

# =============================================================================
# Filter Column Mappers
# =============================================================================
from .test_filter_mappers import (
    # Main filter configurations
    TEST_MEAL_FILTER_MAPPERS,
    TEST_RECIPE_FILTER_MAPPERS,
    TEST_EDGE_CASE_FILTER_MAPPERS,
    
    # Specialized filter configurations
    TEST_PERFORMANCE_FILTER_MAPPERS,
    TEST_CONSTRAINT_FILTER_MAPPERS,
    TEST_UNIQUE_CONSTRAINT_FILTER_MAPPERS,
)

# =============================================================================
# Data Factory Functions
# =============================================================================
from .test_data_factories import (
    # Utility functions
    random_suffix,
    random_attr,
    check_missing_attributes,
    
    # Main entity factories
    create_test_meal_kwargs,
    create_test_meal,
    create_test_recipe_kwargs,
    create_test_recipe,
    
    # Relationship entity factories
    create_test_tag_kwargs,
    create_test_tag,
    create_test_rating_kwargs,
    create_test_rating,
    create_test_ingredient_kwargs,
    create_test_ingredient,
    
    # Edge case entity factories
    create_test_circular_a_kwargs,
    create_test_circular_a,
    create_test_circular_b_kwargs,
    create_test_circular_b,
    create_test_self_ref_kwargs,
    create_test_self_ref,
    
    # Complex data creation utilities
    create_test_meal_with_recipes,
    create_test_recipe_with_ingredients,
    create_test_recipe_with_ratings,
    create_test_self_ref_hierarchy,
    create_test_friends_network,
    
    # Performance testing utilities
    create_large_dataset,
)

# =============================================================================
# Convenience Groups for Common Usage Patterns
# =============================================================================

# All entity classes for type hints and instantiation
ALL_ENTITIES = [
    TestMealEntity,
    TestRecipeEntity,
    TestCircularEntityA,
    TestCircularEntityB,
    TestSelfReferentialEntity,
    TestTagEntity,
    TestRatingEntity,
    TestIngredientEntity,
]

# All SQLAlchemy models for ORM operations
ALL_SA_MODELS = [
    TestTagSaModel,
    TestRatingSaModel,
    TestIngredientSaModel,
    TestRecipeSaModel,
    TestMealSaModel,
    TestCircularModelA,
    TestCircularModelB,
    TestSelfReferentialModel,
]

# All data mappers for repository configuration
ALL_MAPPERS = [
    TestMealMapper,
    TestRecipeMapper,
    TestCircularMapperA,
    TestCircularMapperB,
    TestSelfReferentialMapper,
    TestTagMapper,
    TestRatingMapper,
    TestIngredientMapper,
]

# All filter configurations for different test scenarios
ALL_FILTER_MAPPERS = [
    TEST_MEAL_FILTER_MAPPERS,
    TEST_RECIPE_FILTER_MAPPERS,
    TEST_EDGE_CASE_FILTER_MAPPERS,
    TEST_PERFORMANCE_FILTER_MAPPERS,
    TEST_CONSTRAINT_FILTER_MAPPERS,
    TEST_UNIQUE_CONSTRAINT_FILTER_MAPPERS,
]

# All factory functions for data generation
ALL_FACTORIES = [
    create_test_meal,
    create_test_recipe,
    create_test_tag,
    create_test_rating,
    create_test_ingredient,
    create_test_circular_a,
    create_test_circular_b,
    create_test_self_ref,
]

# =============================================================================
# Documentation
# =============================================================================

__all__ = [
    # Constants
    "TEST_SCHEMA",
    
    # Models
    "TestNutriFactsSaModel",
    "test_meals_tags_association",
    "test_recipes_tags_association", 
    "test_self_ref_friends_association",
    "TestTagSaModel",
    "TestRatingSaModel",
    "TestIngredientSaModel",
    "TestRecipeSaModel",
    "TestMealSaModel",
    "TestCircularModelA",
    "TestCircularModelB",
    "TestSelfReferentialModel",
    
    # Entities
    "TestMealEntity",
    "TestRecipeEntity",
    "TestCircularEntityA",
    "TestCircularEntityB",
    "TestSelfReferentialEntity",
    "TestTagEntity",
    "TestRatingEntity",
    "TestIngredientEntity",
    
    # Mappers
    "TestMealMapper",
    "TestRecipeMapper",
    "TestCircularMapperA",
    "TestCircularMapperB",
    "TestSelfReferentialMapper",
    "TestTagMapper",
    "TestRatingMapper",
    "TestIngredientMapper",
    
    # Filter Configurations
    "TEST_MEAL_FILTER_MAPPERS",
    "TEST_RECIPE_FILTER_MAPPERS",
    "TEST_EDGE_CASE_FILTER_MAPPERS",
    "TEST_PERFORMANCE_FILTER_MAPPERS",
    "TEST_CONSTRAINT_FILTER_MAPPERS",
    "TEST_UNIQUE_CONSTRAINT_FILTER_MAPPERS",
    
    # Factory Functions
    "random_suffix",
    "random_attr",
    "check_missing_attributes",
    "create_test_meal_kwargs",
    "create_test_meal",
    "create_test_recipe_kwargs",
    "create_test_recipe",
    "create_test_tag_kwargs",
    "create_test_tag",
    "create_test_rating_kwargs",
    "create_test_rating",
    "create_test_ingredient_kwargs",
    "create_test_ingredient",
    "create_test_circular_a_kwargs",
    "create_test_circular_a",
    "create_test_circular_b_kwargs",
    "create_test_circular_b",
    "create_test_self_ref_kwargs",
    "create_test_self_ref",
    "create_test_meal_with_recipes",
    "create_test_recipe_with_ingredients",
    "create_test_recipe_with_ratings",
    "create_test_self_ref_hierarchy",
    "create_test_friends_network",
    "create_large_dataset",
    
    # Convenience Groups
    "ALL_ENTITIES",
    "ALL_SA_MODELS",
    "ALL_MAPPERS",
    "ALL_FILTER_MAPPERS",
    "ALL_FACTORIES",
]

# =============================================================================
# Module Info
# =============================================================================

__version__ = "2.0.0"
__author__ = "Claude Code"
__description__ = "Organized test utilities for SaGenericRepository integration testing"

# Test configuration info
TEST_INFO = {
    "schema": TEST_SCHEMA,
    "entity_count": len(ALL_ENTITIES),
    "model_count": len(ALL_SA_MODELS),
    "mapper_count": len(ALL_MAPPERS),
    "filter_config_count": len(ALL_FILTER_MAPPERS),
    "factory_count": len(ALL_FACTORIES),
    "version": __version__,
}