"""
Edge case tests for SaGenericRepository

This module tests edge cases and error conditions:
- Edge case models (circular relationships, self-referential)
- Invalid filter combinations
- Filter precedence and operator priority
- Error handling and boundary conditions

Tests use mock models from conftest.py to avoid database dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from tests.contexts.seedwork.shared.adapters.conftest import (
    MockCircularModelA, MockCircularModelB, MockSelfReferentialModel, MockComplexJoinModel,
    MockCircularEntityA, MockSelfReferentialEntity,
    MOCK_EDGE_CASE_FILTER_MAPPERS
)


class TestSaGenericRepositoryEdgeCaseModels:
    """
    PHASE 0.2.6: Test edge case models (circular relationships, self-referential joins)
    
    This test class uses the new edge case models defined in conftest.py:
    - MockCircularModelA/B for circular relationships
    - MockSelfReferentialModel for hierarchical data
    - MockComplexJoinModel for stress-testing join scenarios
    """
    
    @pytest.mark.anyio
    async def test_circular_model_a_basic_query(self, circular_repository):
        """Test basic query on circular model A"""
        result = await circular_repository.query(filter={"circular_a_name": "Test A"})
        
        assert isinstance(result, list)
        circular_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_circular_model_join_to_b(self, circular_repository):
        """Test circular model A joining to model B"""
        result = await circular_repository.query(
            filter={"circular_b_name": "Test B"}  # This requires A->B join
        )
        
        assert isinstance(result, list)
        circular_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_self_referential_model_basic_query(self, self_ref_repository):
        """Test basic query on self-referential model"""
        result = await self_ref_repository.query(filter={"self_ref_name": "Root"})
        
        assert isinstance(result, list)
        self_ref_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_self_referential_model_parent_join(self, self_ref_repository):
        """Test self-referential model joining to parent"""
        result = await self_ref_repository.query(
            filter={"parent_name": "Parent Node"}  # This requires self-join to parent
        )
        
        assert isinstance(result, list)
        self_ref_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_self_referential_hierarchy_filter(self, self_ref_repository):
        """Test filtering by hierarchy level in self-referential model"""
        result = await self_ref_repository.query(
            filter={"self_ref_level": 2}  # Filter by depth level
        )
        
        assert isinstance(result, list)
        self_ref_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_complex_join_model_multiple_paths(self, mock_session):
        """Test complex join model with multiple join paths to same target"""
        from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import SaGenericRepository
        from tests.contexts.seedwork.shared.adapters.conftest import MockCircularMapperA
        
        # Create repository for complex join model
        complex_repo = SaGenericRepository(
            db_session=mock_session,
            data_mapper=MockCircularMapperA,  # Reuse existing mapper
            domain_model_type=MockCircularEntityA,  # Reuse existing entity
            sa_model_type=MockComplexJoinModel,
            filter_to_column_mappers=MOCK_EDGE_CASE_FILTER_MAPPERS,
        )
        
        result = await complex_repo.query(
            filter={"complex_meal_name": "Complex Meal"}  # Deep join path
        )
        
        assert isinstance(result, list)
        complex_repo._session.execute.assert_called_once()


class TestSaGenericRepositoryFilterCombinations:
    """
    PHASE 2.1: Test complex filter combinations and edge cases
    
    This tests combinations that might cause conflicts or unexpected behavior:
    - Multiple postfix operators on same field
    - Conflicting filter criteria
    - Edge cases with None values and empty lists
    """
    
    @pytest.mark.anyio
    async def test_conflicting_range_filters(self, meal_repository):
        """Test conflicting range filters (e.g., min > max)"""
        result = await meal_repository.query(
            filter={
                "total_time_gte": 120,  # Greater than or equal to 120
                "total_time_lte": 60,   # Less than or equal to 60 (impossible)
            }
        )
        
        # Should return empty results but not error
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_multiple_postfix_on_same_field_different_values(self, meal_repository):
        """Test multiple postfix operators on same field with different values"""
        result = await meal_repository.query(
            filter={
                "calories": 500,           # Exact match
                "calories_gte": 400,       # Also greater than or equal
                "calories_lte": 600,       # Also less than or equal
            }
        )
        
        # Should combine all conditions with AND logic
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_list_and_scalar_filters_on_same_field(self, meal_repository):
        """Test both list and scalar filters on same field"""
        result = await meal_repository.query(
            filter={
                "id": "meal123",                    # Scalar filter
                "id": ["meal123", "meal456"],       # List filter (should override)
            }
        )
        
        # The list filter should take precedence (last wins in dict)
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_none_value_filters(self, meal_repository):
        """Test filters with None values"""
        result = await meal_repository.query(
            filter={
                "description": None,        # Should match NULL
                "menu_id_is_not": None,    # Should match NOT NULL
            }
        )
        
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_empty_list_filters(self, meal_repository):
        """Test filters with empty lists"""
        result = await meal_repository.query(
            filter={
                "id": [],                    # Empty list
                "author_id_not_in": [],     # Empty NOT IN list
            }
        )
        
        # Empty lists should be handled gracefully
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_zero_and_false_value_filters(self, meal_repository):
        """Test filters with zero and False values (truthy/falsy edge cases)"""
        result = await meal_repository.query(
            filter={
                "total_time": 0,       # Zero value (falsy but valid)
                "like": False,         # False value (falsy but valid)
                "weight_in_grams": 0,  # Zero weight (falsy but valid)
            }
        )
        
        # Zero and False should be treated as valid filter values
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once()


class TestSaGenericRepositoryInvalidFilters:
    """
    PHASE 2.2: Test invalid filter handling and error conditions
    
    This tests how the repository handles invalid or malformed filter inputs:
    - Unknown filter keys
    - Invalid postfix combinations
    - Type mismatches
    - Malformed data structures
    """
    
    @pytest.mark.anyio
    async def test_unknown_filter_key_raises_exception(self, meal_repository):
        """Test that unknown filter keys raise appropriate exceptions"""
        with pytest.raises(BadRequestException, match="Filter not allowed"):
            await meal_repository.query(
                filter={"unknown_field": "some_value"}
            )
    
    @pytest.mark.anyio
    async def test_malformed_tag_filter_raises_exception(self, meal_repository):
        """Test that malformed tag filters raise exceptions"""
        with pytest.raises(Exception):  # Some validation error
            await meal_repository.query(
                filter={"tags": "not_a_list"}  # Should be list of dicts
            )
    
    @pytest.mark.anyio
    async def test_invalid_postfix_combination(self, meal_repository):
        """Test invalid postfix operators (non-existent)"""
        with pytest.raises(BadRequestException, match="Filter not allowed"):
            await meal_repository.query(
                filter={"total_time_invalid": 120}  # Invalid postfix
            )
    
    @pytest.mark.anyio
    async def test_type_mismatch_handling(self, meal_repository):
        """Test handling of type mismatches in filter values"""
        # This might not raise an error but should be handled gracefully
        result = await meal_repository.query(
            filter={
                "total_time": "not_a_number",  # String for integer field
                "like": "not_a_boolean",       # String for boolean field
            }
        )
        
        # Should either work or raise a clear error, not crash
        assert isinstance(result, list)


class TestSaGenericRepositoryFilterPrecedence:
    """
    PHASE 2.3: Test filter operator precedence and priority
    
    This tests the order of operations and precedence rules:
    - Postfix operator precedence (exact order matters)
    - Filter application order
    - Join order dependency
    """
    
    def test_postfix_precedence_order(self, meal_repository):
        """Test that postfix operators are checked in correct precedence order"""
        # This tests the exact order: _gte, _lte, _ne, _not_in, _is_not, _not_exists
        
        # Test that _gte is checked before _lte when both could match
        operator_func = meal_repository._filter_operator_selection(
            filter_name="total_time_gte",  # Should match _gte first
            filter_value=120,
            sa_model_type=meal_repository.sa_model_type,
        )
        
        # Should be gte operator (first in precedence)
        from sqlalchemy.sql import operators
        assert operator_func == operators.ge
    
    def test_postfix_removal_only_removes_first_match(self, meal_repository):
        """Test that postfix removal only removes the first matching postfix"""
        # If there were multiple postfixes (hypothetically), only first should be removed
        # This tests the exact behavior of the remove_postfix logic
        
        operator_func = meal_repository._filter_operator_selection(
            filter_name="total_time_lte",  # Should find and remove _lte
            filter_value=60,
            sa_model_type=meal_repository.sa_model_type,
        )
        
        from sqlalchemy.sql import operators
        assert operator_func == operators.le
    
    @pytest.mark.anyio
    async def test_filter_application_order_consistency(self, meal_repository):
        """Test that filters are applied in consistent order"""
        # Run the same query multiple times to ensure consistent order
        filter_dict = {
            "name": "test",
            "author_id": "user123", 
            "total_time_lte": 60,
            "calories_gte": 300,
        }
        
        result1 = await meal_repository.query(filter=filter_dict)
        result2 = await meal_repository.query(filter=filter_dict)
        
        # Results should be identical (order consistent)
        assert result1 == result2
    
    @pytest.mark.anyio
    async def test_join_order_dependency(self, meal_repository):
        """Test that join order follows dependency rules"""
        # This tests that Recipe must be joined before Ingredient in MealRepo
        result = await meal_repository.query(
            filter={"products": ["product1"]}  # Requires Meal->Recipe->Ingredient
        )
        
        # Should not raise any join order errors
        assert isinstance(result, list)
        meal_repository._session.execute.assert_called_once() 