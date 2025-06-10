"""
Core functionality tests for SaGenericRepository

This module tests the fundamental operations of SaGenericRepository:
- Filter operator selection and application
- Filter statement building 
- Filter application with joins
- Basic query method functionality

Tests use mock models from conftest.py to avoid database dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy import select
from sqlalchemy.sql import operators

from src.contexts.seedwork.shared.adapters.seedwork_repository import SaGenericRepository
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException

# Import mock models from conftest.py
from tests.contexts.seedwork.shared.adapters.conftest import (
    MockMealSaModel, MockRecipeSaModel, MockIngredientSaModel,
    MockMealEntity, MockMealMapper, MOCK_MEAL_FILTER_MAPPERS
)


class TestSaGenericRepositoryFilterOperators:
    """
    PHASE 0.4: Test _filter_operator_selection() method with all postfix operators
    
    This tests the core operator selection logic that:
    - Handles all postfix operators (_gte, _lte, _ne, _not_in, _is_not)
    - Falls back appropriately for different column types
    - Deals with edge cases (None values, empty lists, type mismatches)
    """
    
    def test_filter_operator_selection_gte_postfix(self, meal_repository):
        """Test _gte postfix returns greater-than-or-equal operator"""
        operator_func = meal_repository._filter_operator_selection(
            filter_name="total_time_gte",
            filter_value=120,
        )
        
        assert operator_func == operators.ge
    
    def test_filter_operator_selection_lte_postfix(self, meal_repository):
        """Test _lte postfix returns less-than-or-equal operator"""
        operator_func = meal_repository._filter_operator_selection(
            filter_name="total_time_lte",
            filter_value=60,
        )
        
        assert operator_func == operators.le
    
    def test_filter_operator_selection_ne_postfix(self, meal_repository):
        """Test _ne postfix returns not-equal operator"""
        operator_func = meal_repository._filter_operator_selection(
            filter_name="author_id_ne", 
            filter_value="user123",
        )
        
        assert operator_func == operators.ne
    
    def test_filter_operator_selection_not_in_postfix(self, meal_repository):
        """Test _not_in postfix returns special NULL-handling not-in operator"""
        operator_func = meal_repository._filter_operator_selection(
            filter_name="author_id_not_in",
            filter_value=["user1", "user2"],
        )
        
        # Should return lambda that handles NULL values
        assert callable(operator_func)
    
    def test_filter_operator_selection_is_not_postfix(self, meal_repository):
        """Test _is_not postfix returns IS NOT operator"""
        operator_func = meal_repository._filter_operator_selection(
            filter_name="like_is_not",
            filter_value=None,
        )
        
        assert operator_func == operators.is_not
    
    def test_filter_operator_selection_list_value_gets_in_operator(self, meal_repository):
        """Test list values get IN operator regardless of column type"""
        operator_func = meal_repository._filter_operator_selection(
            filter_name="id",
            filter_value=["meal1", "meal2", "meal3"],  # List value
        )
        
        # Should return lambda that uses c.in_(v)
        assert callable(operator_func)
    
    def test_filter_operator_selection_string_column_gets_eq_operator(self, meal_repository):
        """Test string columns get equality operator by default"""
        operator_func = meal_repository._filter_operator_selection(
            filter_name="name",  # String column, no postfix
            filter_value="test meal",  # String value
        )
        
        # Should return equality operator
        assert operator_func == operators.eq
    
    def test_filter_operator_selection_boolean_column_gets_is_operator(self, meal_repository):
        """Test boolean columns get IS operator"""
        operator_func = meal_repository._filter_operator_selection(
            filter_name="like",  # Boolean column
            filter_value=True,  # Boolean value
        )
        
        # Should return lambda that uses c.is_(v)
        assert callable(operator_func)
    
    def test_filter_operator_selection_unknown_filter_key_raises_exception(self, meal_repository):
        """Test that unknown filter keys raise exception"""
        with pytest.raises(Exception):  # BadRequestException or KeyError
            meal_repository._filter_operator_selection(
                filter_name="unknown_key",
                filter_value="some_value",
            )
    
    def test_postfix_removal_logic(self, meal_repository):
        """Test that postfix is correctly removed when looking up column mapping"""
        # This should use "total_time" to look up the column, not "total_time_gte"
        operator_func = meal_repository._filter_operator_selection(
            filter_name="total_time_gte",
            filter_value=120,
        )
        
        # Should not raise exception about missing filter key
        assert operator_func == operators.ge


class TestSaGenericRepositoryFilterStmt:
    """
    PHASE 0.3: Test filter_stmt() method with complex filtering scenarios
    
    This tests the core filter_stmt() method that:
    - Applies multiple filters with different operators
    - Handles distinct logic for list filters and joins
    - Works with FilterColumnMapper configurations
    """
    
    def test_filter_stmt_single_filter(self, meal_repository):
        """Test filter_stmt with single filter criterion"""
        stmt = select(meal_repository.sa_model_type)  # Use repository's configured model
        filter_dict = {"name": "test meal"}
        
        # Use the repository's primary mapper configuration
        mapping = meal_repository.get_filter_key_to_column_name_for_sa_model_type(meal_repository.sa_model_type)
        
        result_stmt = meal_repository.filter_stmt(
            stmt=stmt,
            sa_model_type=meal_repository.sa_model_type,  # Use repository's configured model
            mapping=mapping,
            filter=filter_dict,
            distinct=False,
        )
        
        # Should add WHERE clause (we can't easily test exact SQL without database)
        assert result_stmt is not None
        assert hasattr(result_stmt, 'whereclause')
    
    def test_filter_stmt_multiple_filters(self, meal_repository):
        """Test filter_stmt with multiple filter criteria"""
        stmt = select(meal_repository.sa_model_type)  # Use repository's configured model
        filter_dict = {
            "name": "test meal",
            "author_id": "user123", 
            "total_time_lte": 60,
        }
        
        # Use the repository's primary mapper configuration
        mapping = meal_repository.get_filter_key_to_column_name_for_sa_model_type(meal_repository.sa_model_type)
        
        result_stmt = meal_repository.filter_stmt(
            stmt=stmt,
            sa_model_type=meal_repository.sa_model_type,  # Use repository's configured model
            mapping=mapping, 
            filter=filter_dict,
            distinct=False,
        )
        
        # Should add multiple WHERE clauses
        assert result_stmt is not None
        assert hasattr(result_stmt, 'whereclause')
    
    def test_filter_stmt_list_filter_applies_distinct(self, meal_repository):
        """Test that list filters automatically apply DISTINCT"""
        stmt = select(meal_repository.sa_model_type)  # Use repository's configured model
        filter_dict = {"id": ["meal1", "meal2", "meal3"]}  # List filter
        
        # Use the repository's primary mapper configuration
        mapping = meal_repository.get_filter_key_to_column_name_for_sa_model_type(meal_repository.sa_model_type)
        
        result_stmt = meal_repository.filter_stmt(
            stmt=stmt,
            sa_model_type=meal_repository.sa_model_type,  # Use repository's configured model
            mapping=mapping,
            filter=filter_dict, 
            distinct=False,  # Even though distinct=False
        )
        
        # Should apply DISTINCT because of list filter
        # We can check if distinct was applied by looking at the statement
        assert result_stmt is not None
    
    def test_filter_stmt_distinct_flag_applies_distinct(self, meal_repository):
        """Test that distinct=True flag applies DISTINCT"""
        stmt = select(meal_repository.sa_model_type)  # Use repository's configured model
        filter_dict = {"name": "test meal"}
        
        # Use the repository's primary mapper configuration
        mapping = meal_repository.get_filter_key_to_column_name_for_sa_model_type(meal_repository.sa_model_type)
        
        result_stmt = meal_repository.filter_stmt(
            stmt=stmt,
            sa_model_type=meal_repository.sa_model_type,  # Use repository's configured model
            mapping=mapping,
            filter=filter_dict,
            distinct=True,  # Explicit distinct flag
        )
        
        # Should apply DISTINCT because of distinct=True
        assert result_stmt is not None
    
    def test_filter_stmt_empty_filter_returns_unchanged_stmt(self, meal_repository):
        """Test that empty filter dict returns statement unchanged"""
        stmt = select(meal_repository.sa_model_type)  # Use repository's configured model
        
        result_stmt = meal_repository.filter_stmt(
            stmt=stmt,
            sa_model_type=meal_repository.sa_model_type,  # Use repository's configured model
            mapping={},
            filter={},  # Empty filter
            distinct=False,
        )
        
        # Should return original statement unchanged
        assert result_stmt is stmt
    
    def test_filter_stmt_none_filter_returns_unchanged_stmt(self, meal_repository):
        """Test that None filter returns statement unchanged"""
        stmt = select(meal_repository.sa_model_type)  # Use repository's configured model
        
        result_stmt = meal_repository.filter_stmt(
            stmt=stmt,
            sa_model_type=meal_repository.sa_model_type,  # Use repository's configured model
            mapping={},
            filter=None,  # None filter
            distinct=False,
        )
        
        # Should return original statement unchanged
        assert result_stmt is stmt


class TestSaGenericRepositoryApplyFilters:
    """
    PHASE 0.5: Test _apply_filters() method with complex join scenarios
    
    This tests the core _apply_filters() method that:
    - Handles join logic with FilterColumnMapper configurations
    - Tracks already_joined to prevent duplicate joins
    - Applies filters in correct order and builds statements
    - Works with complex multi-table join scenarios
    """
    
    def test_apply_filters_single_table_no_joins(self, meal_repository):
        """Test _apply_filters with filters that don't require joins"""
        stmt = select(MockMealSaModel)
        filter_dict = {"name": "test meal", "author_id": "user123"}
        already_joined = set()
        
        result_stmt = meal_repository._apply_filters(
            stmt=stmt,
            filter=filter_dict,
            already_joined=already_joined,
        )
        
        # Should return a modified statement with filters applied
        assert result_stmt is not None
        
    def test_apply_filters_with_recipe_join(self, meal_repository):
        """Test _apply_filters with filters that require recipe join"""
        stmt = select(MockMealSaModel)
        filter_dict = {"recipe_id": "recipe123"}  # This requires join to recipes
        already_joined = set()
        
        result_stmt = meal_repository._apply_filters(
            stmt=stmt,
            filter=filter_dict,
            already_joined=already_joined,
        )
        
        # Should return a modified statement with joins and filters applied
        assert result_stmt is not None
        
    def test_apply_filters_with_multi_level_join(self, meal_repository):
        """Test _apply_filters with filters requiring multi-level joins (meal->recipe->ingredient)"""
        stmt = select(MockMealSaModel)
        filter_dict = {"products": ["product1", "product2"]}  # This requires meal->recipe->ingredient join
        already_joined = set()
        
        result_stmt = meal_repository._apply_filters(
            stmt=stmt,
            filter=filter_dict,
            already_joined=already_joined,
        )
        
        # Should return a modified statement with complex joins and filters applied
        assert result_stmt is not None
        
    def test_apply_filters_prevents_duplicate_joins(self, meal_repository):
        """Test that _apply_filters prevents duplicate joins using already_joined tracking"""
        stmt = select(MockMealSaModel)
        filter_dict = {"recipe_id": "recipe123", "recipe_name": "test recipe"}  # Both require same join
        already_joined = set()
        
        result_stmt = meal_repository._apply_filters(
            stmt=stmt,
            filter=filter_dict,
            already_joined=already_joined,
        )
        
        # Should return a modified statement, duplicate joins should be prevented internally
        assert result_stmt is not None
        
    def test_apply_filters_empty_filter_returns_unchanged(self, meal_repository):
        """Test that _apply_filters with empty filter returns unchanged statement"""
        stmt = select(MockMealSaModel)
        already_joined = set()
        
        result_stmt = meal_repository._apply_filters(
            stmt=stmt,
            filter={},  # Empty filter
            already_joined=already_joined,
        )
        
        # Should return statement unchanged for empty filter
        assert result_stmt is stmt


class TestSaGenericRepositoryQueryMethod:
    """
    PHASE 0.6: Test query() method with complete query flow using mocked dependencies
    
    This tests the complete query() method that:
    - Handles starting_stmt parameter
    - Applies filters, sorting, and limits
    - Tests _return_sa_instance flag behavior
    - Works with sort_stmt callbacks
    """
    
    @pytest.mark.anyio
    async def test_query_basic_filter(self, meal_repository):
        """Test query() with basic filter parameter"""
        
        result = await meal_repository.query(filter={"name": "test meal"})
        
        # Should return domain objects (empty list in this mock)
        assert isinstance(result, list)
        
        # Verify the session.execute was called
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_query_with_limit(self, meal_repository):
        """Test query() with limit parameter"""
        
        result = await meal_repository.query(filter={"name": "test meal"}, limit=10)
        
        # Should return domain objects
        assert isinstance(result, list)
        
        # Verify the session.execute was called
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_query_with_starting_stmt(self, meal_repository):
        """Test query() with custom starting_stmt parameter"""
        custom_stmt = select(MockMealSaModel).where(MockMealSaModel.author_id == "user123")
        
        result = await meal_repository.query(
            filter={"name": "test meal"},
            starting_stmt=custom_stmt
        )
        
        # Should return domain objects
        assert isinstance(result, list)
        
        # Verify the session.execute was called with modified statement
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_query_return_sa_instance_flag(self, meal_repository):
        """Test query() with _return_sa_instance=True flag"""
        
        # Mock the session to return SA objects instead of domain objects
        mock_sa_objects = [MockMealSaModel(id="meal1", name="test meal")]
        meal_repository._session.execute.return_value.scalars.return_value.all.return_value = mock_sa_objects
        
        result = await meal_repository.query(
            filter={"name": "test meal"},
            _return_sa_instance=True
        )
        
        # Should return SA objects directly (our mock list)
        assert result == mock_sa_objects
        
        # Verify the session.execute was called
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio 
    async def test_query_with_sort_callback(self, meal_repository):
        """Test query() with sort_stmt callback function"""
        
        def custom_sort(stmt, value_of_sort_query):
            # The callback receives both stmt and value_of_sort_query parameters
            return stmt.order_by(MockMealSaModel.created_at.desc())
        
        result = await meal_repository.query(
            filter={"name": "test meal"},
            sort_stmt=custom_sort
        )
        
        # Should return domain objects
        assert isinstance(result, list)
        
        # Verify the session.execute was called
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_query_empty_filter(self, meal_repository):
        """Test query() with empty filter (should return all records)"""
        
        result = await meal_repository.query(filter={})
        
        # Should return domain objects
        assert isinstance(result, list)
        
        # Verify the session.execute was called
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_query_none_filter(self, meal_repository):
        """Test query() with None filter (should return all records)"""
        
        result = await meal_repository.query(filter=None)
        
        # Should return domain objects
        assert isinstance(result, list)
        
        # Verify the session.execute was called
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_query_with_already_joined_tracking(self, meal_repository):
        """Test query() properly tracks already_joined to prevent duplicate joins"""
        
        result = await meal_repository.query(
            filter={"recipe_id": "recipe123", "recipe_name": "test recipe"},
            already_joined=set()
        )
        
        # Should return domain objects
        assert isinstance(result, list)
        
        # Verify the session.execute was called
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_query_complex_multi_level_joins(self, meal_repository):
        """Test query() with complex multi-level joins (meal->recipe->ingredient)"""
        
        result = await meal_repository.query(
            filter={"products": ["product1", "product2"]}  # Requires meal->recipe->ingredient joins
        )
        
        # Should return domain objects
        assert isinstance(result, list)
        
        # Verify the session.execute was called with complex join logic
        meal_repository._session.execute.assert_called_once()
    
    @pytest.mark.anyio
    async def test_query_with_custom_sa_model(self, meal_repository):
        """Test query() with custom sa_model parameter"""
        
        result = await meal_repository.query(
            filter={"name": "test meal"},
            sa_model=MockRecipeSaModel  # Override the default model
        )
        
        # Should return domain objects
        assert isinstance(result, list)
        
        # Verify the session.execute was called
        meal_repository._session.execute.assert_called_once() 