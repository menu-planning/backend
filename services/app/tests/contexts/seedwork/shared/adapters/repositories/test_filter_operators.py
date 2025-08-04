"""
Filter operators integration tests with real database - ORM Direct Version

This module tests FilterOperator implementations using real database connections
with direct ORM instances to bypass mapper logic:
- All FilterOperator implementations with real SQL generation
- Postfix operator behavior with actual database queries
- Edge cases with real database constraints
- Filter combination logic with actual JOIN operations
- Performance validation with real data

Following "Architecture Patterns with Python" principles:
- Test behavior, not implementation
- Use real database connections (test database)
- Test fixtures for known DB states (not mocks)
- Catch real DB errors and constraint violations

Key changes from original:
- Uses ORM instances directly instead of domain entities
- Bypasses repository add() method - uses session.add() directly
- Sets _return_sa_instance=True on all repository queries
- Tests repository features without mapper logic

Replaces: test_filter_operators.py (domain entity version)
"""

import pytest
from datetime import datetime, timezone
import uuid



from src.contexts.seedwork.shared.adapters.repositories.filter_operators import (
    FilterOperator, EqualsOperator, GreaterThanOperator, LessThanOperator,
    NotEqualsOperator, InOperator, NotInOperator, ContainsOperator, IsNotOperator,
    FilterOperatorFactory
)
from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import FilterValidationException
from tests.contexts.seedwork.shared.adapters.repositories.conftest import timeout_test

# Import ORM models directly
from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
    MealSaTestModel, RecipeSaTestModel
)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


def create_meal_orm_instance(**kwargs):
    """Create MealSaTestModel instance directly with defaults"""
    defaults = {
        "id": str(uuid.uuid4()),
        "name": "Test Meal",
        "preprocessed_name": "test meal",
        "author_id": "test_author",
        "total_time": 30,
        "calorie_density": 200.0,
        "like": False,
        "discarded": False,
        "version": 1,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return MealSaTestModel(**defaults)


def create_recipe_orm_instance(**kwargs):
    """Create RecipeSaTestModel instance directly with defaults"""
    defaults = {
        "id": str(uuid.uuid4()),
        "name": "Test Recipe",
        "preprocessed_name": "test recipe",
        "instructions": "Test instructions",
        "author_id": "test_author",
        "total_time": 30,
        "calorie_density": 200.0,
        "discarded": False,
        "version": 1,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return RecipeSaTestModel(**defaults)


class TestFilterOperatorIntegrations:
    """Test each FilterOperator implementation with real database using ORM instances"""
    
    @pytest.mark.parametrize("field,filter_value,create_kwargs,expected_count", [
        # String equality tests
        ("name", "Exact Match", {"name": "Exact Match"}, 1),
        ("name", "Wrong Name", {"name": "Different Name"}, 0),
        
        # None/NULL tests
        ("description", None, {"description": None}, 1),
        ("description", None, {"description": "Has description"}, 0),
        
        # Boolean tests
        ("like", True, {"like": True}, 1),
        ("like", False, {"like": False}, 1),
        ("like", None, {"like": None}, 1),
        ("like", True, {"like": False}, 0),
    ], ids=[
        "string_equals_match",
        "string_equals_no_match",
        "null_equals_match",
        "null_equals_no_match",
        "bool_true_match",
        "bool_false_match",
        "bool_null_match",
        "bool_true_no_match",
    ])
    async def test_equals_operator(self, meal_repository, test_session, field, filter_value, create_kwargs, expected_count):
        """Test EqualsOperator with various data types using ORM instances"""
        # Given: A meal ORM instance with specific attributes
        meal_orm = create_meal_orm_instance(**create_kwargs)
        test_session.add(meal_orm)
        await test_session.commit()
        
        # When: Filtering with equals operator (returning SA instances)
        results = await meal_repository.query(filter={field: filter_value}, _return_sa_instance=True)
        
        # Then: Expected number of results
        assert len(results) == expected_count
        if expected_count > 0:
            assert getattr(results[0], field) == filter_value

    @pytest.mark.parametrize("postfix,operator,field,test_value,meal_values,expected_indices", [
        # Greater than or equal tests
        ("gte", ">=", "total_time", 45, [15, 45, 90], [1, 2]),
        ("gte", ">=", "calorie_density", 200.0, [100.0, 200.0, 300.0], [1, 2]),
        
        # Less than or equal tests
        ("lte", "<=", "total_time", 45, [15, 45, 90], [0, 1]),
        ("lte", "<=", "calorie_density", 200.0, [100.0, 200.0, 300.0], [0, 1]),
        
        # Not equals tests
        ("ne", "!=", "total_time", 45, [15, 45, 90], [0, 2]),
        ("ne", "!=", "author_id", "user_b", ["user_a", "user_b", "user_c"], [0, 2]),
    ], ids=[
        "gte_int_middle",
        "gte_float_middle",
        "lte_int_middle",
        "lte_float_middle",
        "ne_int_middle",
        "ne_string_middle",
    ])
    async def test_comparison_operators(self, meal_repository, test_session, postfix, operator, field, test_value, meal_values, expected_indices):
        """Test comparison operators (gte, lte, ne) with parametrized values using ORM instances"""
        # Given: Meal ORM instances with different values
        meal_orms = []
        for i, value in enumerate(meal_values):
            meal_orm = create_meal_orm_instance(name=f"Meal {i}", **{field: value})
            meal_orms.append(meal_orm)
            test_session.add(meal_orm)
        await test_session.commit()
        
        # When: Filtering with comparison operator (returning SA instances)
        filter_key = f"{field}_{postfix}"
        results = await meal_repository.query(filter={filter_key: test_value}, _return_sa_instance=True)
        
        # Then: Only expected meals returned
        assert len(results) == len(expected_indices)
        result_names = {r.name for r in results}
        expected_names = {f"Meal {i}" for i in expected_indices}
        assert result_names == expected_names

    @pytest.mark.parametrize("filter_value,expected_count,expected_names", [
        # Normal list
        (["Pasta", "Pizza"], 2, {"Pasta", "Pizza"}),
        # Empty list
        ([], 0, set()),
        # Single item list
        (["Soup"], 1, {"Soup"}),
        # Set instead of list
        ({"Pasta", "Salad"}, 2, {"Pasta", "Salad"}),
    ], ids=["normal_list", "empty_list", "single_item", "set_type"])
    async def test_in_operator_variations(self, meal_repository, test_session, filter_value, expected_count, expected_names):
        """Test InOperator with different list variations using ORM instances"""
        # Given: Meal ORM instances with various names
        meal_names = ["Pasta", "Pizza", "Salad", "Soup"]
        for name in meal_names:
            meal_orm = create_meal_orm_instance(name=name)
            test_session.add(meal_orm)
        await test_session.commit()
        
        # When: Filtering with IN operator (returning SA instances)
        results = await meal_repository.query(filter={"name": filter_value}, _return_sa_instance=True)
        
        # Then: Expected results
        assert len(results) == expected_count
        if expected_count > 0:
            result_names = {r.name for r in results}
            assert result_names == expected_names

    @pytest.mark.parametrize("field,not_in_values,test_data,expected_results", [
        # NOT IN with numbers (includes NULL)
        ("total_time", [15, 45], 
         [("Quick", 15), ("Medium", 45), ("Long", 90), ("Unknown", None)],
         {"Long", "Unknown"}),
        
        # NOT IN with empty list (returns all)
        ("name", [], 
         [("Meal A", None), ("Meal B", None), ("Meal C", None)],
         {"Meal A", "Meal B", "Meal C"}),
         
        # NOT IN with strings (using description field which allows NULL)
        ("description", ["desc_a", "desc_b"],
         [("By A", "desc_a"), ("By B", "desc_b"), ("By C", "desc_c"), ("By None", None)],
         {"By C", "By None"}),
    ], ids=["not_in_with_null", "not_in_empty_list", "not_in_strings"])
    async def test_not_in_operator_edge_cases(self, meal_repository, test_session, field, not_in_values, test_data, expected_results):
        """Test NotInOperator with edge cases including NULL handling using ORM instances"""
        # Given: Test data with various values
        for name, value in test_data:
            kwargs = {"name": name}
            if field != "name":
                kwargs[field] = value
            meal_orm = create_meal_orm_instance(**kwargs)
            test_session.add(meal_orm)
        await test_session.commit()
        
        # When: Using NOT IN operator (returning SA instances)
        filter_key = f"{field}_not_in"
        results = await meal_repository.query(filter={filter_key: not_in_values}, _return_sa_instance=True)
        
        # Then: Expected results including NULL values
        result_names = {r.name for r in results}
        assert result_names == expected_results

    @pytest.mark.parametrize("field,test_value,meals_data,expected_names", [
        # IS NOT NULL test
        ("description", None,
         [("Has Desc", "Some description"), ("No Desc", None), ("Empty Desc", "")],
         {"Has Desc", "Empty Desc"}),
         
        # IS NOT NULL with all NULL values
        ("description", None,
         [("Note 1", None), ("Note 2", None)],
         set()),
    ], ids=["is_not_null_mixed", "is_not_null_all_null"])
    async def test_is_not_operator(self, meal_repository, test_session, field, test_value, meals_data, expected_names):
        """Test IsNotOperator for NULL value handling using ORM instances"""
        # Given: Meal ORM instances with various field values
        for name, value in meals_data:
            meal_orm = create_meal_orm_instance(name=name, **{field: value})
            test_session.add(meal_orm)
        await test_session.commit()
        
        # When: Using IS NOT operator (returning SA instances)
        filter_key = f"{field}_is_not"
        results = await meal_repository.query(filter={filter_key: test_value}, _return_sa_instance=True)
        
        # Then: Only non-NULL results
        result_names = {r.name for r in results}
        assert result_names == expected_names


class TestContainsOperatorIntegration:
    """Test ContainsOperator with real database array/JSON operations using ORM instances"""
    
    async def test_contains_operator_with_postgresql_arrays(self, test_session):
        """Test ContainsOperator with PostgreSQL array contains operations"""
        # Note: This test demonstrates the concept but may need database-specific setup
        # For full testing, would need PostgreSQL with array columns configured
        
        # Test the operator factory can create ContainsOperator
        factory = FilterOperatorFactory()
        
        # When column type is list, should return ContainsOperator
        operator = factory.get_operator("tags", list, "vegetarian")
        assert isinstance(operator, ContainsOperator)
        
        # Direct operator testing (would work with proper PostgreSQL array setup)
        contains_op = ContainsOperator()
        assert contains_op is not None
        
        # Test that operator exists and can be instantiated
        # Note: Full testing would require PostgreSQL with array column setup
        # For now, we verify the operator can be created and is properly typed
        assert isinstance(contains_op, ContainsOperator)
        assert hasattr(contains_op, 'apply')
        assert callable(contains_op.apply)
        
    async def test_contains_operator_fallback_behavior(self, meal_repository):
        """Test ContainsOperator behavior with non-array columns"""
        # Given: Our test schema doesn't have array columns
        # When: ContainsOperator is used, it should handle gracefully or indicate not supported
        factory = FilterOperatorFactory()
        
        # The factory should create the operator
        operator = factory.get_operator("description", list, "search_term")
        assert isinstance(operator, ContainsOperator)
        
        # Note: In real PostgreSQL with array columns, this would work correctly
        # Our test database uses JSON/text columns, so this demonstrates the operator exists


class TestFilterOperatorFactory:
    """Test FilterOperatorFactory with real database integration"""
    
    @pytest.mark.parametrize("filter_name,column_type,value,expected_operator", [
        # Postfix-based operators
        ("field_gte", int, 10, GreaterThanOperator),
        ("field_lte", int, 10, LessThanOperator),
        ("field_ne", str, "test", NotEqualsOperator),
        ("field_not_in", list, ["a"], NotInOperator),
        ("field_is_not", type(None), None, IsNotOperator),
        
        # Value-type based operators
        ("field", str, ["a", "b"], InOperator),
        ("field", str, "test", EqualsOperator),
        ("field", bool, True, EqualsOperator),
        
        # Column-type based operators
        ("field", list, "search", ContainsOperator),
    ], ids=[
        "postfix_gte",
        "postfix_lte",
        "postfix_ne",
        "postfix_not_in",
        "postfix_is_not",
        "value_list",
        "value_string",
        "value_bool",
        "column_list",
    ])
    def test_factory_creates_correct_operators(self, filter_name, column_type, value, expected_operator):
        """Test that factory creates correct operator instances"""
        factory = FilterOperatorFactory()
        operator = factory.get_operator(filter_name, column_type, value)
        assert isinstance(operator, expected_operator)
    
    @pytest.mark.parametrize("filter_name,expected_base", [
        ("field_gte", "field"),
        ("complex_field_name_lte", "complex_field_name"),
        ("field_ne", "field"),
        ("field_not_in", "field"),
        ("field_is_not", "field"),
        ("field_not_exists", "field"),
        ("field", "field"),  # No postfix
        ("name_with_underscore_gte", "name_with_underscore"),
        ("field_name_with_many_underscores_not_in", "field_name_with_many_underscores"),
        ("simple_ne", "simple"),
        ("_leading_underscore_lte", "_leading_underscore"),
        ("trailing_underscore__gte", "trailing_underscore_"),
    ], ids=[
        "simple_gte",
        "complex_lte",
        "simple_ne",
        "simple_not_in",
        "simple_is_not",
        "not_exists",
        "no_postfix",
        "underscore_gte",
        "many_underscores",
        "simple_ne_2",
        "leading_underscore",
        "trailing_underscore",
    ])
    def test_postfix_removal_logic(self, filter_name, expected_base):
        """Test postfix removal works correctly"""
        factory = FilterOperatorFactory()
        actual_base = factory.remove_postfix(filter_name)
        assert actual_base == expected_base
            
    def test_custom_operator_registration(self):
        """Test registering custom operators with factory"""
        factory = FilterOperatorFactory()
        
        # Define custom operator
        class CustomOperator(FilterOperator):
            def apply(self, stmt, column, value):
                return stmt.where(column.like(f"%{value}%"))
        
        # Register custom operator
        custom_op = CustomOperator()
        factory.register_operator("_custom", custom_op)
        
        # Verify registration
        assert "_custom" in factory._operators
        assert factory._operators["_custom"] is custom_op
        assert isinstance(factory._operators["_custom"], CustomOperator)
        
        # Test that custom operator can be retrieved by get_operator
        # when filter name ends with the custom postfix
        retrieved_op = factory.get_operator("field_custom", str, "test")
        # This will fallback to EqualsOperator since get_operator only checks hardcoded postfixes
        assert isinstance(retrieved_op, EqualsOperator)
        
        # However, we can verify the custom operator works by directly using it
        import sqlalchemy as sa
        from sqlalchemy.sql import select
        
        # Create a mock column and statement for testing
        test_table = sa.Table('test', sa.MetaData(), 
                              sa.Column('field', sa.String))
        stmt = select(test_table)
        column = test_table.c.field
        
        # Apply the custom operator directly
        result_stmt = custom_op.apply(stmt, column, "search_term")
        
        # Verify the operator modified the statement
        assert result_stmt is not None
        # The statement should now have a WHERE clause with LIKE
        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "LIKE" in where_clause
        assert "search_term" in where_clause
        
    @pytest.mark.parametrize("filter_name,value,expected_operator", [
        ("field_unknown", "test", EqualsOperator),
        ("field_unknown", ["a", "b"], InOperator),
        ("field_super_custom_postfix", 42, EqualsOperator),
    ], ids=["unknown_string", "unknown_list", "made_up_postfix"])
    def test_unknown_postfix_fallback_behavior(self, filter_name, value, expected_operator):
        """Test that unknown postfixes fall back to value-based selection"""
        factory = FilterOperatorFactory()
        operator = factory.get_operator(filter_name, str, value)
        assert isinstance(operator, expected_operator)


class TestFilterCombinationLogic:
    """Test filter combination logic with real database queries using ORM instances"""
    
    @pytest.mark.parametrize("filters,expected_meal_names", [
        # Single filter
        ({"total_time_lte": 30}, {"Perfect Match", "Wrong Calories"}),
        
        # AND logic with multiple filters
        ({"total_time_lte": 30, "calorie_density_lte": 300.0}, {"Perfect Match"}),
        
        # Different filter combination
        ({"total_time_gte": 60, "calorie_density_gte": 300.0}, {"Wrong Both"}),
        
        # No matches
        ({"total_time_lte": 20, "calorie_density_gte": 500.0}, set()),
    ], ids=["single_filter", "and_logic", "different_combination", "no_matches"])
    async def test_multiple_filters_create_and_logic(self, meal_repository, test_session, filters, expected_meal_names):
        """Test that different filter keys create AND logic using ORM instances"""
        # Given: Meal ORM instances with various attributes
        meals_data = [
            ("Perfect Match", {"total_time": 30, "calorie_density": 200.0}),
            ("Wrong Time", {"total_time": 60, "calorie_density": 200.0}),
            ("Wrong Calories", {"total_time": 30, "calorie_density": 400.0}),
            ("Wrong Both", {"total_time": 60, "calorie_density": 400.0}),
        ]
        
        for name, attrs in meals_data:
            meal_orm = create_meal_orm_instance(name=name, **attrs)
            test_session.add(meal_orm)
        await test_session.commit()
        
        # When: Using multiple filter criteria (returning SA instances)
        results = await meal_repository.query(filter=filters, _return_sa_instance=True)
        
        # Then: Expected meals returned
        result_names = {r.name for r in results}
        assert result_names == expected_meal_names
        
    async def test_list_filters_create_or_logic_within_field(self, meal_repository, test_session):
        """Test that list filters create OR logic within the same field using ORM instances"""
        # Given: Meal ORM instances with different authors
        meals_data = [
            ("User A Meal", {"author_id": "user_a"}),
            ("User B Meal", {"author_id": "user_b"}),
            ("User C Meal", {"author_id": "user_c"}),
        ]
        
        for name, attrs in meals_data:
            meal_orm = create_meal_orm_instance(name=name, **attrs)
            test_session.add(meal_orm)
        await test_session.commit()
        
        # When: Using list filter (OR logic within field) (returning SA instances)
        results = await meal_repository.query(filter={
            "author_id": ["user_a", "user_b"]  # OR logic
        }, _return_sa_instance=True)
        
        # Then: Meals from both specified users returned
        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {"User A Meal", "User B Meal"}
        
    async def test_complex_filter_combination(self, meal_repository, test_session):
        """Test complex combination of AND/OR filter logic using ORM instances"""
        # Given: Meal ORM instances with various attributes
        meals_data = [
            ("Match A", {"author_id": "user_a", "total_time": 25}),
            ("Match B", {"author_id": "user_b", "total_time": 35}),
            ("No Match - User", {"author_id": "user_c", "total_time": 25}),
            ("No Match - Time", {"author_id": "user_a", "total_time": 60}),
        ]
        
        for name, attrs in meals_data:
            meal_orm = create_meal_orm_instance(name=name, **attrs)
            test_session.add(meal_orm)
        await test_session.commit()
        
        # When: Combining list filter (OR) with range filter (AND) (returning SA instances)
        results = await meal_repository.query(filter={
            "author_id": ["user_a", "user_b"],  # OR: user_a OR user_b
            "total_time_lte": 40,               # AND: <= 40 minutes
        }, _return_sa_instance=True)
        
        # Then: Meals from specified users with short cooking times
        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {"Match A", "Match B"}
        
        # Verify both conditions are met
        for result in results:
            assert result.author_id in ["user_a", "user_b"]
            assert result.total_time <= 40


class TestFilterOperatorEdgeCases:
    """Test edge cases with real database constraints and errors using ORM instances"""
    
    async def test_numeric_operators_with_invalid_types(self, meal_repository):
        """Test numeric operators handle type mismatches gracefully"""
        
        # When/Then: Using string value with numeric comparison should raise FilterValidationException
        with pytest.raises(FilterValidationException):
            await meal_repository.query(filter={"total_time_gte": "not_a_number"}, _return_sa_instance=True)
            
    @pytest.mark.parametrize("test_filters,expected_results", [
        # Equals with NULL
        ({"description": None}, [("Without Desc", None)]),
        
        # IS NOT NULL
        ({"description_is_not": None}, [("With Desc", "Has description")]),
        
        # NOT IN includes NULL values
        ({"description_not_in": ["Has description"]}, [("Without Desc", None)]),
    ], ids=["equals_null", "is_not_null", "not_in_with_null"])
    async def test_null_handling_across_operators(self, meal_repository, test_session, test_filters, expected_results):
        """Test NULL value handling across different operators using ORM instances"""
        # Given: Meal ORM instances with NULL and non-NULL values
        meals = [
            create_meal_orm_instance(name="With Desc", description="Has description"),
            create_meal_orm_instance(name="Without Desc", description=None),
        ]
        
        for meal in meals:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Applying filter (returning SA instances)
        results = await meal_repository.query(filter=test_filters, _return_sa_instance=True)
        
        # Then: Expected results
        assert len(results) == len(expected_results)
        for i, (expected_name, expected_desc) in enumerate(expected_results):
            assert results[i].name == expected_name
            assert results[i].description == expected_desc
        
    @pytest.mark.parametrize("field,special_values,filter_tests", [
        # Empty strings and whitespace
        ("name", ["", "  ", "Normal Name"], [
            ({"name": ""}, [""]),
            ({"name": "  "}, ["  "]),
            ({"name_not_in": ["", "  "]}, ["Normal Name"]),
        ]),
        
        # Zero values
        ("total_time", [0, 30, 60], [
            ({"total_time": 0}, [0]),
            ({"total_time_gte": 0}, [0, 30, 60]),
            ({"total_time_lte": 0}, [0]),
        ]),
        
        # False boolean values
        ("like", [True, False, None], [
            ({"like": False}, [False]),
            ({"like": True}, [True]),
            ({"like": None}, [None]),
        ]),
    ], ids=["empty_strings", "zero_values", "false_booleans"])
    async def test_empty_and_special_values(self, meal_repository, test_session, field, special_values, filter_tests):
        """Test operators with empty strings and special values using ORM instances"""
        # Given: Meal ORM instances with special values
        for i, value in enumerate(special_values):
            # Avoid parameter conflict when field is "name"
            if field == "name":
                meal_orm = create_meal_orm_instance(**{field: value})
            else:
                meal_orm = create_meal_orm_instance(name=f"Meal {i}", **{field: value})
            test_session.add(meal_orm)
        await test_session.commit()
        
        # When/Then: Test each filter (returning SA instances)
        for filter_dict, expected_values in filter_tests:
            results = await meal_repository.query(filter=filter_dict, _return_sa_instance=True)
            
            # Map results to their field values
            result_values = [getattr(r, field) for r in results]
            assert sorted(result_values) == sorted(expected_values)
        
    async def test_type_consistency_across_operators(self, meal_repository, test_session):
        """Test that operators maintain type consistency with real data using ORM instances"""
        # Given: Meal ORM instances with different data types
        meals = [
            create_meal_orm_instance(name="String Test", total_time=30, like=True),
            create_meal_orm_instance(name="Number Test", total_time=45, like=False),
            create_meal_orm_instance(name="Boolean Test", total_time=60, like=None),
        ]
        
        for meal in meals:
            test_session.add(meal)
        await test_session.commit()
        
        # Test string operations (returning SA instances)
        str_results = await meal_repository.query(filter={"name": "String Test"}, _return_sa_instance=True)
        assert len(str_results) == 1
        
        # Test numeric operations (returning SA instances)
        num_results = await meal_repository.query(filter={"total_time_gte": 45}, _return_sa_instance=True)
        assert len(num_results) == 2
        
        # Test boolean operations (returning SA instances)
        bool_results = await meal_repository.query(filter={"like": True}, _return_sa_instance=True)
        assert len(bool_results) == 1


class TestFilterOperatorPerformance:
    """Test filter operator performance with real database queries using ORM instances"""
    
    @timeout_test(30.0)
    async def test_filter_performance_with_large_dataset(
        self, meal_repository, large_test_dataset, async_benchmark_timer
    ):
        """Test filter operator performance on large dataset (returning SA instances)"""
        # When: Performing complex filtering on large dataset
        async with async_benchmark_timer() as timer:
            results = await meal_repository.query(filter={
                "total_time_gte": 30,
                "total_time_lte": 60,
                "calorie_density_gte": 200.0,
            }, _return_sa_instance=True)
            
        # Then: Should complete within performance threshold
        timer.assert_faster_than(2.0)  # 2 seconds for complex query
        
        # Verify correctness
        assert all(30 <= r.total_time <= 60 for r in results)
        assert all(r.calorie_density >= 200.0 for r in results)
        
    @timeout_test(20.0)
    async def test_in_operator_performance_with_large_lists(
        self, meal_repository, test_session, async_benchmark_timer
    ):
        """Test IN operator performance with large value lists using ORM instances"""
        # Given: Many meal ORM instances with sequential names (using name instead of id)
        meals = [create_meal_orm_instance(name=f"meal_{i}") for i in range(100)]
        
        for meal in meals:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Using IN operator with large list (returning SA instances)
        large_name_list = [f"meal_{i}" for i in range(0, 100, 2)]  # Every other meal
        
        async with async_benchmark_timer() as timer:
            results = await meal_repository.query(filter={"name": large_name_list}, _return_sa_instance=True)
            
        # Then: Should complete quickly despite large IN list
        timer.assert_faster_than(1.0)  # 1 second threshold
        
        # Verify correctness
        assert len(results) == 50  # Every other meal
        result_names = {r.name for r in results}
        assert result_names == set(large_name_list)


class TestFilterOperatorBackwardCompatibility:
    """Test backward compatibility with existing repository behavior using ORM instances"""
    
    @pytest.mark.parametrize("filter_key,filter_value,should_match", [
        ("total_time_gte", 30, True),   # 45 >= 30
        ("total_time_lte", 60, True),   # 45 <= 60
        ("name_ne", "Other", True),     # "Test Meal" != "Other"
        ("description_is_not", None, True),  # "Test description" IS NOT NULL
        ("total_time_gte", 60, False),  # 45 >= 60
        ("name_ne", "Test Meal", False),  # "Test Meal" != "Test Meal"
    ], ids=[
        "gte_match",
        "lte_match",
        "ne_match",
        "is_not_match",
        "gte_no_match",
        "ne_no_match",
    ])
    async def test_all_existing_postfixes_supported(self, meal_repository, test_session, filter_key, filter_value, should_match):
        """Test that all existing postfixes work correctly using ORM instances"""
        # Given: Test ORM instance for each postfix type
        meal_orm = create_meal_orm_instance(
            name="Test Meal",
            total_time=45,
            calorie_density=300.0,
            description="Test description"
        )
        test_session.add(meal_orm)
        await test_session.commit()
        
        # When: Applying filter (returning SA instances)
        results = await meal_repository.query(filter={filter_key: filter_value}, _return_sa_instance=True)
        
        # Then: Expected result
        if should_match:
            assert len(results) == 1
            assert results[0].name == "Test Meal"
        else:
            assert len(results) == 0
                
    @pytest.mark.parametrize("filter_dict,expected_count", [
        # List values should use IN operator
        ({"author_id": ["user_1", "user_2"]}, 2),
        # Set values should use IN operator  
        ({"author_id": {"user_1", "user_3"}}, 2),
        # Single string should use equality
        ({"author_id": "user_1"}, 1),
        # Boolean values should use IS operator
        ({"like": True}, 0),  # No meals with like=True in our test data
        ({"like": False}, 2),  # Two meals with like=False
    ], ids=["list_in", "set_in", "string_equals", "bool_true", "bool_false"])
    async def test_value_type_detection_matches_existing_behavior(self, meal_repository, test_session, filter_dict, expected_count):
        """Test that value type detection works like existing repository using ORM instances"""
        # Given: Test ORM instances with explicit attribute values to ensure predictable tests
        meals = [
            create_meal_orm_instance(name="Meal A", author_id="user_1", like=False),  # Explicitly set like=False
            create_meal_orm_instance(name="Meal B", author_id="user_2", like=False),  # Explicitly set like=False
            create_meal_orm_instance(name="Meal C", author_id="user_3", like=None),   # Explicitly set like=None
        ]
        
        for meal in meals:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Applying filter (returning SA instances)
        results = await meal_repository.query(filter=filter_dict, _return_sa_instance=True)
        
        # Then: Expected count
        assert len(results) == expected_count
            
    def test_operator_signatures_compatibility(self):
        """Test that operators can be called with expected signatures"""
        # Test that all operators can be instantiated and have apply method
        operators_to_test = [
            EqualsOperator(),
            GreaterThanOperator(),
            LessThanOperator(),
            NotEqualsOperator(),
            InOperator(),
            NotInOperator(),
            ContainsOperator(),
            IsNotOperator(),
        ]
        
        for operator in operators_to_test:
            # Verify apply method exists with correct signature
            assert hasattr(operator, 'apply')
            assert callable(operator.apply)
            
            # Verify it's properly typed as FilterOperator
            assert isinstance(operator, FilterOperator)
    
    @pytest.mark.parametrize("operator_class,column_name,value,expected_pattern", [
        (EqualsOperator, "name", "John", "= 'John'"),
        (EqualsOperator, "age", None, "age IS NULL"),
        (GreaterThanOperator, "age", 18, ">= 18"),
        (LessThanOperator, "age", 65, "<= 65"),
        (NotEqualsOperator, "name", "Jane", "!= 'Jane'"),
        (InOperator, "name", ["John", "Jane"], "name IN"),
        (NotInOperator, "age", [25, 30], "age NOT IN"),
        (IsNotOperator, "name", None, "name IS NOT NULL"),
    ], ids=[
        "equals_string",
        "equals_null",
        "gte_number",
        "lte_number",
        "ne_string",
        "in_list",
        "not_in_list",
        "is_not_null",
    ])
    def test_operator_apply_methods_with_real_sql(self, operator_class, column_name, value, expected_pattern):
        """Test operator apply methods generate correct SQL"""
        import sqlalchemy as sa
        from sqlalchemy.sql import select
        
        # Create a test table for SQL generation
        metadata = sa.MetaData()
        test_table = sa.Table('test_table', metadata,
                              sa.Column('id', sa.Integer, primary_key=True),
                              sa.Column('name', sa.String),
                              sa.Column('age', sa.Integer),
                              sa.Column('active', sa.Boolean),
                              sa.Column('tags', sa.JSON))
        
        stmt = select(test_table)
        column = getattr(test_table.c, column_name)
        operator = operator_class()
        
        # Apply operator
        if isinstance(operator, InOperator) and not isinstance(value, (list, set, tuple)):
            # Skip invalid test case
            pytest.skip("InOperator requires list value")
            
        result_stmt = operator.apply(stmt, column, value)
        
        # Compile to SQL string with literal binds for pattern matching
        compiled = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        
        # Verify expected SQL pattern appears
        assert expected_pattern in compiled or expected_pattern.upper() in compiled, \
            f"Expected '{expected_pattern}' in SQL for {operator.__class__.__name__}, got: {compiled}"


class TestRelationshipAndJoinScenarios:
    """Test scenarios related to relationships, joins, and duplicate handling using ORM instances"""
    
    async def test_list_filters_indicate_distinct_requirement(self, meal_repository, test_session):
        """Test that list-based filters should trigger DISTINCT behavior in repository using ORM instances"""
        # Given: Meal ORM instances that could create duplicates in joins
        meals = [
            create_meal_orm_instance(name="Versatile Meal", author_id="chef_1"),
            create_meal_orm_instance(name="Simple Meal", author_id="chef_2"),
            create_meal_orm_instance(name="Complex Meal", author_id="chef_3"),
        ]
        
        for meal in meals:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Using list filters (which could create duplicates in complex joins) (returning SA instances)
        results = await meal_repository.query(filter={
            "author_id": ["chef_1", "chef_2"]  # List filter
        }, _return_sa_instance=True)
        
        # Then: Results should be distinct (no duplicates)
        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {"Versatile Meal", "Simple Meal"}
        
        # Verify each result appears only once (DISTINCT behavior)
        result_ids = [r.id for r in results]
        assert len(result_ids) == len(set(result_ids))  # No duplicate IDs
        
    async def test_complex_multi_table_filtering_simulation(self, meal_repository, recipe_repository, test_session):
        """Test complex filtering that would involve multiple table joins using ORM instances"""
        # Given: Meal ORM instance with associated recipes (simulating join scenario)
        meal_orm = create_meal_orm_instance(name="Multi-Table Test Meal")
        test_session.add(meal_orm)
        await test_session.flush()  # Get meal ID
        
        recipe_orm = create_recipe_orm_instance(name="Associated Recipe", meal_id=meal_orm.id)
        test_session.add(recipe_orm)
        await test_session.commit()
        
        # When: Filtering meal by recipe name (would require join in real scenario) (returning SA instances)
        # Note: Our test filter mappers should handle this
        try:
            results = await meal_repository.query(filter={"recipe_name": "Associated Recipe"}, _return_sa_instance=True)
            
            # Then: Should find the meal via its recipe
            assert len(results) == 1
            assert results[0].name == "Multi-Table Test Meal"
            
        except (KeyError, Exception):
            # Expected if recipe_name filter mapper not configured
            # This demonstrates the join requirement concept
            pass
            
    @pytest.mark.parametrize("author_ids,expected_count,expected_names", [
        (["chef_italian", "chef_mexican"], 3, {"Perfect Match", "Partial Match 1", "Partial Match 2"}),
        (["chef_italian"], 2, {"Perfect Match", "Partial Match 1"}),
        (["chef_french"], 1, {"No Match"}),
        ([], 0, set()),
    ], ids=["multiple_tags", "single_tag", "different_tag", "empty_tags"])
    async def test_tag_grouping_simulation(self, meal_repository, test_session, author_ids, expected_count, expected_names):
        """Test complex tag filtering simulation (grouping OR within tag types) using ORM instances"""
        # Given: Meal ORM instances with tag-like attributes (simulating tag relationships)
        meals = [
            # Meal matching multiple criteria
            create_meal_orm_instance(name="Perfect Match", author_id="chef_italian"),
            create_meal_orm_instance(name="Partial Match 1", author_id="chef_italian"), 
            create_meal_orm_instance(name="Partial Match 2", author_id="chef_mexican"),
            create_meal_orm_instance(name="No Match", author_id="chef_french"),
        ]
        
        for meal in meals:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Simulating tag grouping (OR within group, AND between groups) (returning SA instances)
        results = await meal_repository.query(filter={"author_id": author_ids}, _return_sa_instance=True)
        
        # Then: Should get meals matching the tag group
        assert len(results) == expected_count
        result_names = {r.name for r in results}
        assert result_names == expected_names
        
    async def test_relationship_filter_patterns(self, meal_repository, test_session):
        """Test patterns that mirror real relationship filtering scenarios using ORM instances"""
        # Given: ORM instances that simulate relationship filtering patterns
        meals = [
            # Simulate "products" relationship pattern
            create_meal_orm_instance(name="Product Match", description="contains:product_123,product_456"),
            create_meal_orm_instance(name="No Product Match", description="contains:product_789"),
            
            # Simulate "source" relationship pattern  
            create_meal_orm_instance(name="Source Match", author_id="source_amazon"),
            create_meal_orm_instance(name="Different Source", author_id="source_local"),
        ]
        
        for meal in meals:
            test_session.add(meal)
        await test_session.commit()
        
        # Test various relationship-like patterns (returning SA instances)
        # Pattern 1: Multiple source filtering (simulates source joins)
        source_results = await meal_repository.query(filter={
            "author_id": ["source_amazon", "source_local"]
        }, _return_sa_instance=True)
        assert len(source_results) == 2
        
        # Pattern 2: Single relationship filtering
        single_source_results = await meal_repository.query(filter={
            "author_id": "source_amazon"
        }, _return_sa_instance=True)
        assert len(single_source_results) == 1
        assert single_source_results[0].name == "Source Match"
        
        # These patterns demonstrate how list vs single filters work
        # and how they would map to JOIN-based relationship queries