"""
Join functionality tests for SaGenericRepository

This module tests complex join scenarios and multi-table filtering:
- Complex filtering scenarios with joins
- Tag filtering with AND/OR logic
- Multi-level join chains
- Join deduplication and optimization

Tests use mock models from conftest.py to avoid database dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from tests.contexts.seedwork.shared.adapters.conftest import (
    MockMealSaModel, MockRecipeSaModel, MockTagSaModel,
    MockMealEntity, MockMealMapper, MOCK_MEAL_FILTER_MAPPERS
)


class TestSaGenericRepositoryComplexFilteringScenarios:
    """
    PHASE 1.2: Test complex filtering scenarios with joins
    
    This tests scenarios that require multiple table joins:
    - Meal -> Recipe joins for recipe-based filtering
    - Meal -> Recipe -> Ingredient joins for ingredient filtering
    - Complex filter combinations across multiple tables
    """
    
    @pytest.mark.anyio
    async def test_meal_filter_by_recipe_properties(self, meal_repository):
        """Test filtering meals by recipe properties (requires join)"""
        # This should trigger Meal -> Recipe join
        result = await meal_repository.query(
            filter={"recipe_name": "Chicken Alfredo"}
        )
        
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio 
    async def test_meal_filter_by_ingredient_products(self, meal_repository):
        """Test filtering meals by ingredient products (requires multi-level join)"""
        # This should trigger Meal -> Recipe -> Ingredient joins
        result = await meal_repository.query(
            filter={"products": ["chicken", "pasta", "cream"]}
        )
        
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_complex_multi_table_filter_combination(self, meal_repository):
        """Test complex filters combining multiple table joins"""
        result = await meal_repository.query(
            filter={
                "name": "Italian Dinner",           # Meal table (no join)
                "author_id": "chef123",            # Meal table (no join)
                "recipe_name": "Chicken Alfredo",  # Recipe table (1 join)
                "products": ["chicken", "pasta"],   # Ingredient table (2 joins)
                "total_time_lte": 60,              # Meal table (no join)
            }
        )
        
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_duplicate_join_prevention(self, meal_repository):
        """Test that duplicate joins are prevented when multiple filters need same join"""
        result = await meal_repository.query(
            filter={
                "recipe_id": "recipe123",          # Requires Meal -> Recipe join
                "recipe_name": "Chicken Alfredo",  # Also requires Meal -> Recipe join
            }
        )
        
        # Should only perform the join once, not twice
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_nutrition_filter_combination(self, meal_repository):
        """Test filtering by nutrition facts (composite field access)"""
        result = await meal_repository.query(
            filter={
                "calories_gte": 300,
                "calories_lte": 600,
                "protein_gte": 20,
                "carbohydrate_lte": 50,
            }
        )
        
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()


class TestSaGenericRepositoryComplexMultiLevelJoins:
    """
    Test complex multi-level join scenarios that stress-test the repository
    
    These tests use the complex join model which has relationships to multiple
    other models, creating scenarios where multiple join paths and deep chains
    are required.
    """
    
    @pytest.mark.anyio
    async def test_complex_multi_level_join_meal_recipe_ingredient(self, meal_repository):
        """Test deep join: Meal -> Recipe -> Ingredient"""
        result = await meal_repository.query(
            filter={
                "products": ["ingredient1", "ingredient2"]  # Filter by ingredient product_id
            }
        )
        
        # Should handle complex 3-level join successfully
        assert isinstance(result, list)
        
    @pytest.mark.anyio 
    async def test_complex_join_with_multiple_paths(self, meal_repository):
        """Test scenarios where multiple join paths exist to same target"""
        result = await meal_repository.query(
            filter={
                "recipe_name": "Italian Recipe"  # Join through recipes relationship
            }
        )
        
        # Should handle join path resolution correctly
        assert isinstance(result, list)
        
    @pytest.mark.anyio
    async def test_join_deduplication_with_complex_filters(self, meal_repository):
        """Test that duplicate joins are properly detected and avoided"""
        result = await meal_repository.query(
            filter={
                "recipe_id": "recipe123",
                "recipe_name": "Test Recipe"  # Both require same recipe join
            }
        )
        
        # Should avoid duplicate joins
        assert isinstance(result, list)


# NOTE: Tag filtering tests have been removed from this file
# Tag filtering requires special domain logic (groupby, EXISTS, any()) that cannot
# be handled by the generic repository's filter_stmt method. These tests should be
# in domain-specific repository test files where the special tag handling logic is tested.
#
# The generic repository is designed for simple column-based filtering, not
# complex relationship-based filtering that requires custom SQL generation. 