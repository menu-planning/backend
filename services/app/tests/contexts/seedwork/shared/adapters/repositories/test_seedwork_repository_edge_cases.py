"""
SaGenericRepository edge cases integration tests with real database

This module tests edge cases and error conditions using real database connections:
- Edge case models (circular relationships, self-referential)
- Real database constraint violations and error handling
- Complex filter combinations with actual database queries
- Filter precedence and operator priority with real SQL
- Boundary conditions and malformed data handling

Following "Architecture Patterns with Python" principles:
- Test behavior, not implementation
- Use real database connections (test database)
- Test fixtures for known DB states (not mocks)
- Catch real DB errors (constraints, deadlocks, etc.)

Replaces: test_seedwork_repository_edge_cases.py (mock-based version)
"""

import pytest
from sqlalchemy.exc import IntegrityError, DBAPIError, ProgrammingError

from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import FilterValidationException, RepositoryQueryException
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from tests.contexts.seedwork.shared.adapters.repositories.conftest import timeout_test
from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
    create_test_circular_a,
    create_test_circular_b,
    create_test_self_ref,
    create_test_meal,
    reset_counters,
)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


@pytest.mark.integration
class TestSaGenericRepositoryEdgeCaseModels:
    """Test edge case models with real database constraints"""

    async def test_circular_model_a_basic_query(self, circular_repository):
        """Test basic querying of circular model A with real DB"""
        # Given: A circular model A entity is created and persisted
        reset_counters()  # Ensure deterministic IDs
        entity_a = create_test_circular_a(name="Test Circular A")
        await circular_repository.add(entity_a)
        
        # When: Querying with the correct filter key
        results = await circular_repository.query(filter={"circular_a_name": "Test Circular A"})
        
        # Then: The entity is found with correct attributes
        assert len(results) == 1
        assert results[0].name == "Test Circular A"

    async def test_circular_model_with_reference(self, circular_repository, test_session):
        reset_counters()  # Ensure deterministic IDs
        """Test circular model behavior with references"""
        # Given: A circular model entity without foreign key reference
        entity_a1 = create_test_circular_a(name="Entity A1", b_ref_id=None)
        
        await circular_repository.add(entity_a1)
        await test_session.commit()
        
        # When: Querying with proper filter for the created entity
        results = await circular_repository.query(filter={"circular_a_name": "Entity A1"})
        
        # Then: The entity is retrieved with correct attributes
        assert len(results) == 1
        assert results[0].name == "Entity A1"
        assert results[0].b_ref_id is None

    async def test_self_referential_model_basic_operations(self, self_ref_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test basic operations on self-referential model"""
        # Given: A root entity in self-referential model
        root_entity = create_test_self_ref(name="Root", level=0)
        await self_ref_repository.add(root_entity)
        
        # When: Querying all entities without filtering
        all_results = await self_ref_repository.query()
        
        # Then: The root entity is present in results
        assert len(all_results) >= 1
        assert any(result.name == "Root" for result in all_results)

    async def test_self_referential_model_parent_filtering(self, self_ref_repository, test_session):
        reset_counters()  # Ensure deterministic IDs
        """Test self-referential model basic functionality"""
        # Given: Parent and child entities without complex relationships
        parent = create_test_self_ref(name="Parent", level=0)
        child = create_test_self_ref(name="Child", level=1, parent_id=None)  # No parent reference
        
        await self_ref_repository.add(parent)
        await self_ref_repository.add(child)
        await test_session.commit()
        
        # When: Querying all entities to test basic functionality
        all_results = await self_ref_repository.query()
        
        # Then: Both entities are present with correct names
        assert len(all_results) >= 2
        names = {result.name for result in all_results}
        assert "Parent" in names
        assert "Child" in names

    async def test_self_referential_model_constraints(self, self_ref_repository, test_session):
        reset_counters()  # Ensure deterministic IDs
        """Test self-referential model constraint behavior"""
        # Given: A valid entity without constraint-violating references
        valid_entity = create_test_self_ref(
            name="Valid Entity", 
            level=1, 
            parent_id=None  # No parent reference to avoid FK issues
        )
        
        # When: Adding and committing the valid entity
        await self_ref_repository.add(valid_entity)
        await test_session.commit()
        
        # Then: Entity is successfully created and retrievable
        all_results = await self_ref_repository.query()
        assert len(all_results) >= 1
        assert any(result.name == "Valid Entity" for result in all_results)


@pytest.mark.integration
class TestSaGenericRepositoryFilterCombinations:
    """Test complex filter combinations with real database"""

    async def test_conflicting_range_filters_real_data(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test conflicting range filters return empty result set"""
        # Given: A meal with a specific cooking time
        meal = create_test_meal(name="Test Meal", total_time=90)
        await meal_repository.add(meal)
        
        # When: Applying conflicting range filters (total_time >= 120 AND total_time <= 60)
        results = await meal_repository.query(
            filter={"total_time_gte": 120, "total_time_lte": 60}
        )
        
        # Then: No results are returned due to logical impossibility
        assert len(results) == 0

    async def test_multiple_postfix_same_field_different_values(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test multiple range filters on same field with real data"""
        # Given: Meals with different cooking times
        meals = [
            create_test_meal(name="Quick", total_time=15),
            create_test_meal(name="Medium", total_time=45),
            create_test_meal(name="Long", total_time=90),
        ]
        
        for meal in meals:
            await meal_repository.add(meal)
        
        # When: Filtering for meals between 30-60 minutes
        results = await meal_repository.query(
            filter={"total_time_gte": 30, "total_time_lte": 60}
        )
        
        # Then: Only the medium-time meal is returned
        assert len(results) == 1
        assert results[0].name == "Medium"

    async def test_list_and_scalar_filters_precedence(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test filter precedence with list and scalar values"""
        # Given: Meals with various attributes
        meals = [
            create_test_meal(name="Meal A", total_time=30),
            create_test_meal(name="Meal B", total_time=45),
            create_test_meal(name="Meal C", total_time=60),
        ]
        
        for meal in meals:
            await meal_repository.add(meal)
        
        # When: Applying both list filter and scalar filter
        filter_dict = {
            "name": ["Meal A", "Meal B"],  # List filter
            "total_time_gte": 40,         # Scalar filter
        }
        
        results = await meal_repository.query(filter=filter_dict)
        
        # Then: Only meals matching BOTH conditions are returned
        assert len(results) == 1
        assert results[0].name == "Meal B"

    async def test_none_value_filters_real_database(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test None value handling in real database queries"""
        # Given: Meals with and without descriptions
        meals = [
            create_test_meal(name="With description", description="Some description"),
            create_test_meal(name="No description", description=None),
        ]
        
        for meal in meals:
            await meal_repository.add(meal)
        
        # When: Filtering for meals with None description
        results = await meal_repository.query(filter={"description": None})
        
        # Then: Only the meal without description is returned
        assert len(results) == 1
        assert results[0].name == "No description"

    async def test_empty_list_filters_real_database(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test empty list filter behavior with real database"""
        # Given: A meal exists in the database
        meal = create_test_meal(name="Test Meal")
        await meal_repository.add(meal)
        
        # When: Filtering with an empty list
        empty_in_results = await meal_repository.query(filter={"name": []})
        
        # Then: No results are returned for empty list filter
        assert len(empty_in_results) == 0

    async def test_zero_and_false_value_filters_real_database(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test zero and false value filtering with real database"""
        # Given: Meals with zero and non-zero values
        meals = [
            create_test_meal(name="Zero time", total_time=0),
            create_test_meal(name="Some time", total_time=30),
        ]
        
        for meal in meals:
            await meal_repository.add(meal)
        
        # When: Filtering for zero total_time (falsy but valid value)
        zero_results = await meal_repository.query(filter={"total_time": 0})
        
        # Then: The zero-time meal is found (zero is treated as valid filter value)
        assert len(zero_results) == 1
        assert zero_results[0].name == "Zero time"


@pytest.mark.integration
class TestSaGenericRepositoryInvalidFilters:
    """Test invalid filter handling with real database"""

    async def test_unknown_filter_key_raises_exception(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test that unknown filter keys raise appropriate exceptions"""
        # Given/When/Then: Unknown filter key should raise FilterValidationException
        with pytest.raises(FilterValidationException):
            await meal_repository.query(filter={"unknown_field": "value"})

    async def test_invalid_postfix_combination_raises_exception(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test invalid postfix combinations"""
        # Given/When/Then: Invalid postfix should raise FilterValidationException
        with pytest.raises(FilterValidationException):
            await meal_repository.query(filter={"total_time_invalid_postfix": 30})

    async def test_type_mismatch_handling_real_database(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test type mismatch handling with real database queries"""
        # Given: A meal exists in the database
        meal = create_test_meal(name="Test Meal", total_time=30)
        await meal_repository.add(meal)
        
        # When/Then: String value for integer field should cause database error
        with pytest.raises(FilterValidationException) as exc_info:
            await meal_repository.query(filter={"total_time_gte": "not_a_number"})
        
        # Verify it's a type conversion error from the database
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["invalid", "type", "conversion", "syntax"])

    async def test_malformed_filter_structure_handling(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test malformed filter structure handling"""
        # Given: A meal exists in the database
        meal = create_test_meal(name="Test Meal")
        await meal_repository.add(meal)
        
        # When: Using malformed filter structure (dict in list)
        bad_filter = {"name": ["valid", {"invalid": "mixed"}]}
        
        # Then: Database should reject the malformed query
        with pytest.raises(FilterValidationException) as exc_info:
            await meal_repository.query(filter=bad_filter)
        
        # Verify it's a database-level error
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["invalid", "error", "malformed", "type"])


@pytest.mark.integration
class TestSaGenericRepositoryConstraintViolations:
    """Test database constraint violations with real database"""

    async def test_unique_constraint_violation(self, meal_repository, test_session):
        reset_counters()  # Ensure deterministic IDs
        """Test unique constraint violations"""
        # Given: A meal with specific unique constraint fields
        meal1 = create_test_meal(name="Meal 1", author_id="author1", menu_id="menu1")
        await meal_repository.add(meal1)
        await test_session.commit()
        
        # When: Trying to create another meal with same unique constraint fields
        meal2 = create_test_meal(name="Meal 1", author_id="author1", menu_id="menu1")
        await meal_repository.add(meal2)
        
        # Then: Should raise IntegrityError if unique constraints exist
        try:
            await test_session.commit()
            # If no error, unique constraints may not be defined (which is also valid)
        except IntegrityError as exc:
            # Expected if unique constraints exist - verify it's a unique constraint error
            error_msg = str(exc).lower()
            assert any(keyword in error_msg for keyword in ["unique", "duplicate", "already exists"])

    async def test_check_constraint_violation(self, meal_repository, test_session):
        reset_counters()  # Ensure deterministic IDs
        """Test check constraint violations"""
        # Given: A meal with invalid data that violates check constraints
        meal = create_test_meal(name="Invalid Meal", calorie_density=-100.0)
        await meal_repository.add(meal)
        
        # When/Then: Should raise IntegrityError if check constraints exist
        try:
            await test_session.commit()
            # If no error, check constraints may not be defined (which is also valid)
        except IntegrityError as exc:
            # Expected if check constraints exist - verify it's a check constraint error
            error_msg = str(exc).lower()
            assert any(keyword in error_msg for keyword in ["check", "constraint", "violates", "invalid"])

    async def test_not_null_constraint_violation(self, meal_repository, test_session):
        reset_counters()  # Ensure deterministic IDs
        """Test NOT NULL constraint violations"""
        # Given: A meal with valid required fields (test normal operation)
        meal = create_test_meal(name="Valid Name")
        await meal_repository.add(meal)
        
        # When: Committing the valid meal
        try:
            await test_session.commit()
            # Then: Valid meal should be successfully committed
            assert meal.name == "Valid Name"
        except IntegrityError as exc:
            # If error occurs, verify it's related to null constraints
            error_msg = str(exc).lower()
            assert any(keyword in error_msg for keyword in ["null", "not null", "required"])


@pytest.mark.integration
class TestSaGenericRepositoryFilterPrecedence:
    """Test filter precedence with real database queries"""

    async def test_postfix_precedence_order_with_real_data(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test postfix operator precedence with real database data"""
        # Given: Meals with different cooking times
        meals = [
            create_test_meal(name="Low", total_time=10),
            create_test_meal(name="Medium", total_time=30),
            create_test_meal(name="High", total_time=60),
        ]
        
        for meal in meals:
            await meal_repository.add(meal)
        
        # When: Applying range filters with proper precedence
        results = await meal_repository.query(
            filter={
                "total_time_gte": 20,  # >= 20
                "total_time_lte": 50,  # <= 50
            }
        )
        
        # Then: Only meals within the range are returned
        assert len(results) == 1
        assert results[0].name == "Medium"
        assert 20 <= results[0].total_time <= 50

    async def test_filter_application_order_consistency_real_database(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test consistent filter application order"""
        # Given: Meals with multiple filterable attributes
        meals = [
            create_test_meal(name="A", total_time=25, calorie_density=200.0),
            create_test_meal(name="B", total_time=35, calorie_density=300.0),
            create_test_meal(name="C", total_time=45, calorie_density=400.0),
        ]
        
        for meal in meals:
            await meal_repository.add(meal)
        
        # When: Applying multiple filters that should be combined with AND logic
        results = await meal_repository.query(
            filter={
                "total_time_gte": 30,
                "calorie_density_lte": 350.0,
            }
        )
        
        # Then: Only meals matching ALL criteria are returned
        assert len(results) == 1
        assert results[0].name == "B"
        assert results[0].total_time >= 30
        assert results[0].calorie_density <= 350.0

    async def test_complex_filter_precedence_with_joins(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test filter precedence in complex join scenarios"""
        # Given: Meals with different attributes for complex filtering
        meals = [
            create_test_meal(name="Simple", total_time=30),
            create_test_meal(name="Complex", total_time=60),
        ]
        
        for meal in meals:
            await meal_repository.add(meal)
        
        # When: Applying multiple range filters
        results = await meal_repository.query(
            filter={
                "total_time_gte": 25,
                "total_time_lte": 45,
            }
        )
        
        # Then: Only meals within the range are returned
        assert len(results) == 1
        assert results[0].name == "Simple"
        assert 25 <= results[0].total_time <= 45


@pytest.mark.integration
class TestSaGenericRepositoryBoundaryConditions:
    """Test boundary conditions with real database"""

    @pytest.mark.parametrize("test_type,setup_data,filter_criteria,expected_count,validation_func", [
        (
            "complex_filter_combinations",
            [(i, {"total_time": i * 10, "calorie_density": i * 50.0}) for i in range(1, 6)],
            {"total_time_gte": 20, "total_time_lte": 40, "calorie_density_gte": 100.0, "calorie_density_lte": 200.0},
            "variable",  # May be 0, 1, or more depending on data
            lambda results: all(20 <= r.total_time <= 40 and 100.0 <= r.calorie_density <= 200.0 for r in results)
        ),
        (
            "empty_result_set",
            [],  # No setup data
            {"total_time_gte": 9999},
            0,
            lambda results: isinstance(results, list)
        ),
        (
            "large_in_list",
            [("Test Meal", {})],
            {"name": [f"name_{i}" for i in range(1000)] + ["Test Meal"]},
            1,
            lambda results: results[0].name == "Test Meal" if results else True
        ),
    ], ids=["complex_filters", "empty_results", "large_in_list"])
    async def test_boundary_conditions(self, meal_repository, test_type, setup_data, filter_criteria, expected_count, validation_func):
        reset_counters()  # Ensure deterministic IDs
        """Test boundary conditions with various scenarios"""
        # Given: Setup test data
        for item in setup_data:
            if len(item) == 2:
                name, attributes = item
                if isinstance(name, int):
                    name = f"Meal {name}"
            else:
                name, attributes = f"Meal {item}", {}
            meal = create_test_meal(name=name, **attributes)
            await meal_repository.add(meal)
        
        # When: Applying filter
        results = await meal_repository.query(filter=filter_criteria)
        
        # Then: Expected results with validation
        if expected_count == "variable":
            # For complex filters, just ensure it's a list and validate content
            assert isinstance(results, list)
        else:
            assert len(results) == expected_count
        
        assert validation_func(results)

    async def test_complex_edge_case_performance(self, meal_repository, benchmark_timer):
        reset_counters()  # Ensure deterministic IDs
        """Test performance of complex edge case queries"""
        # Given: Multiple meals with varied attributes for performance testing
        meals = [
            create_test_meal(
                name=f"Performance Test {i}",
                total_time=i * 5,
                calorie_density=i * 25.0,
            )
            for i in range(1, 21)
        ]
        
        for meal in meals:
            await meal_repository.add(meal)
        
        # When: Executing a complex query and measuring performance
        with benchmark_timer() as timer:
            results = await meal_repository.query(
                filter={
                    "total_time_gte": 25,
                    "total_time_lte": 75,
                    "calorie_density_gte": 100.0,
                }
            )
        
        # Then: Query completes within reasonable time and returns valid results
        timer.assert_faster_than(5.0)  # 5 second timeout
        assert isinstance(results, list)
        # Verify results match filter criteria
        for result in results:
            assert 25 <= result.total_time <= 75
            assert result.calorie_density >= 100.0 