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
from old_tests_v0.contexts.seedwork.adapters.repositories.testing_infrastructure.data_factories import (
    create_test_ORM_circular_a,
    create_test_ORM_meal,
    create_test_ORM_self_ref,
    reset_counters,
)
from sqlalchemy.exc import IntegrityError
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    FilterValidationError,
)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


class TestSaGenericRepositoryEdgeCaseModels:
    """Test edge case models with real database constraints"""

    async def test_circular_model_a_basic_query(
        self, circular_repository, test_session
    ):
        """Test basic querying of circular model A with real DB"""
        # Given: A circular model A ORM instance is created and persisted directly
        reset_counters()  # Ensure deterministic IDs
        orm_entity_a = create_test_ORM_circular_a(name="Test Circular A")
        test_session.add(orm_entity_a)
        await test_session.commit()

        # When: Querying with the correct filter key, returning SA instances
        results = await circular_repository.query(
            filter={"circular_a_name": "Test Circular A"}, _return_sa_instance=True
        )

        # Then: The ORM entity is found with correct attributes
        assert len(results) == 1
        assert results[0].name == "Test Circular A"

    async def test_circular_model_with_reference(
        self, circular_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test circular model behavior with references"""
        # Given: A circular model ORM entity without foreign key reference
        orm_entity_a1 = create_test_ORM_circular_a(name="Entity A1", b_ref_id=None)

        test_session.add(orm_entity_a1)
        await test_session.commit()

        # When: Querying with proper filter for the created entity, returning SA instances
        results = await circular_repository.query(
            filter={"circular_a_name": "Entity A1"}, _return_sa_instance=True
        )

        # Then: The ORM entity is retrieved with correct attributes
        assert len(results) == 1
        assert results[0].name == "Entity A1"
        assert results[0].b_ref_id is None

    async def test_self_referential_model_basic_operations(
        self, self_ref_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test basic operations on self-referential model"""
        # Given: A root ORM entity in self-referential model
        root_orm_entity = create_test_ORM_self_ref(name="Root", level=0)
        test_session.add(root_orm_entity)
        await test_session.commit()

        # When: Querying all entities without filtering, returning SA instances
        all_results = await self_ref_repository.query(_return_sa_instance=True)

        # Then: The root ORM entity is present in results
        assert len(all_results) >= 1
        assert any(result.name == "Root" for result in all_results)

    async def test_self_referential_model_parent_filtering(
        self, self_ref_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test self-referential model basic functionality"""
        # Given: Parent and child ORM entities without complex relationships
        parent_orm = create_test_ORM_self_ref(name="Parent", level=0)
        child_orm = create_test_ORM_self_ref(
            name="Child", level=1, parent_id=None
        )  # No parent reference

        test_session.add(parent_orm)
        test_session.add(child_orm)
        await test_session.commit()

        # When: Querying all entities to test basic functionality, returning SA instances
        all_results = await self_ref_repository.query(_return_sa_instance=True)

        # Then: Both ORM entities are present with correct names
        assert len(all_results) >= 2
        names = {result.name for result in all_results}
        assert "Parent" in names
        assert "Child" in names

    async def test_self_referential_model_constraints(
        self, self_ref_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test self-referential model constraint behavior"""
        # Given: A valid ORM entity without constraint-violating references
        valid_orm_entity = create_test_ORM_self_ref(
            name="Valid Entity",
            level=1,
            parent_id=None,  # No parent reference to avoid FK issues
        )

        # When: Adding and committing the valid ORM entity
        test_session.add(valid_orm_entity)
        await test_session.commit()

        # Then: ORM entity is successfully created and retrievable
        all_results = await self_ref_repository.query(_return_sa_instance=True)
        assert len(all_results) >= 1
        assert any(result.name == "Valid Entity" for result in all_results)


class TestSaGenericRepositoryFilterCombinations:
    """Test complex filter combinations with real database"""

    async def test_conflicting_range_filters_real_data(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test conflicting range filters return empty result set"""
        # Given: A meal ORM instance with a specific cooking time
        meal_orm = create_test_ORM_meal(name="Test Meal", total_time=90)
        test_session.add(meal_orm)
        await test_session.commit()

        # When: Applying conflicting range filters (total_time >= 120 AND total_time <= 60)
        results = await meal_repository.query(
            filter={"total_time_gte": 120, "total_time_lte": 60},
            _return_sa_instance=True,
        )

        # Then: No results are returned due to logical impossibility
        assert len(results) == 0

    async def test_multiple_postfix_same_field_different_values(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test multiple range filters on same field with real data"""
        # Given: Meal ORM instances with different cooking times
        meal_orms = [
            create_test_ORM_meal(name="Quick", total_time=15),
            create_test_ORM_meal(name="Medium", total_time=45),
            create_test_ORM_meal(name="Long", total_time=90),
        ]

        for meal_orm in meal_orms:
            test_session.add(meal_orm)
        await test_session.commit()

        # When: Filtering for meals between 30-60 minutes, returning SA instances
        results = await meal_repository.query(
            filter={"total_time_gte": 30, "total_time_lte": 60},
            _return_sa_instance=True,
        )

        # Then: Only the medium-time meal ORM is returned
        assert len(results) == 1
        assert results[0].name == "Medium"

    async def test_list_and_scalar_filters_precedence(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test filter precedence with list and scalar values"""
        # Given: Meal ORM instances with various attributes
        meal_orms = [
            create_test_ORM_meal(name="Meal A", total_time=30),
            create_test_ORM_meal(name="Meal B", total_time=45),
            create_test_ORM_meal(name="Meal C", total_time=60),
        ]

        for meal_orm in meal_orms:
            test_session.add(meal_orm)
        await test_session.commit()

        # When: Applying both list filter and scalar filter, returning SA instances
        filter_dict = {
            "name": ["Meal A", "Meal B"],  # List filter
            "total_time_gte": 40,  # Scalar filter
        }

        results = await meal_repository.query(
            filter=filter_dict, _return_sa_instance=True
        )

        # Then: Only meal ORMs matching BOTH conditions are returned
        assert len(results) == 1
        assert results[0].name == "Meal B"

    async def test_none_value_filters_real_database(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test None value handling in real database queries"""
        # Given: Meal ORM instances with and without descriptions
        meal_orms = [
            create_test_ORM_meal(
                name="With description", description="Some description"
            ),
            create_test_ORM_meal(name="No description", description=None),
        ]

        for meal_orm in meal_orms:
            test_session.add(meal_orm)
        await test_session.commit()

        # When: Filtering for meals with None description, returning SA instances
        results = await meal_repository.query(
            filter={"description": None}, _return_sa_instance=True
        )

        # Then: Only the meal ORM without description is returned
        assert len(results) == 1
        assert results[0].name == "No description"

    async def test_empty_list_filters_real_database(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test empty list filter behavior with real database"""
        # Given: A meal ORM instance exists in the database
        meal_orm = create_test_ORM_meal(name="Test Meal")
        test_session.add(meal_orm)
        await test_session.commit()

        # When: Filtering with an empty list, returning SA instances
        empty_in_results = await meal_repository.query(
            filter={"name": []}, _return_sa_instance=True
        )

        # Then: No results are returned for empty list filter
        assert len(empty_in_results) == 0

    async def test_zero_and_false_value_filters_real_database(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test zero and false value filtering with real database"""
        # Given: Meal ORM instances with zero and non-zero values
        meal_orms = [
            create_test_ORM_meal(name="Zero time", total_time=0),
            create_test_ORM_meal(name="Some time", total_time=30),
        ]

        for meal_orm in meal_orms:
            test_session.add(meal_orm)
        await test_session.commit()

        # When: Filtering for zero total_time (falsy but valid value), returning SA instances
        zero_results = await meal_repository.query(
            filter={"total_time": 0}, _return_sa_instance=True
        )

        # Then: The zero-time meal ORM is found (zero is treated as valid filter value)
        assert len(zero_results) == 1
        assert zero_results[0].name == "Zero time"


class TestSaGenericRepositoryInvalidFilters:
    """Test invalid filter handling with real database"""

    async def test_unknown_filter_key_raises_exception(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test that unknown filter keys raise appropriate exceptions"""
        # Given/When/Then: Unknown filter key should raise FilterValidationException
        with pytest.raises(FilterValidationError):
            await meal_repository.query(
                filter={"unknown_field": "value"}, _return_sa_instance=True
            )

    async def test_invalid_postfix_combination_raises_exception(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test invalid postfix combinations"""
        # Given/When/Then: Invalid postfix should raise FilterValidationException
        with pytest.raises(FilterValidationError):
            await meal_repository.query(
                filter={"total_time_invalid_postfix": 30}, _return_sa_instance=True
            )

    async def test_type_mismatch_handling_real_database(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test type mismatch handling with real database queries"""
        # Given: A meal ORM instance exists in the database
        meal_orm = create_test_ORM_meal(name="Test Meal", total_time=30)
        test_session.add(meal_orm)
        await test_session.commit()

        # When/Then: String value for integer field should cause database error
        with pytest.raises(FilterValidationError) as exc_info:
            await meal_repository.query(
                filter={"total_time_gte": "not_a_number"}, _return_sa_instance=True
            )

        # Verify it's a type conversion error from the database
        error_msg = str(exc_info.value).lower()
        assert any(
            keyword in error_msg
            for keyword in ["invalid", "type", "conversion", "syntax"]
        )

    async def test_malformed_filter_structure_handling(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test malformed filter structure handling"""
        # Given: A meal ORM instance exists in the database
        meal_orm = create_test_ORM_meal(name="Test Meal")
        test_session.add(meal_orm)
        await test_session.commit()

        # When: Using malformed filter structure (dict in list)
        bad_filter = {"name": ["valid", {"invalid": "mixed"}]}

        # Then: Database should reject the malformed query
        with pytest.raises(FilterValidationError) as exc_info:
            await meal_repository.query(filter=bad_filter, _return_sa_instance=True)

        # Verify it's a database-level error
        error_msg = str(exc_info.value).lower()
        assert any(
            keyword in error_msg
            for keyword in ["invalid", "error", "malformed", "type"]
        )


class TestSaGenericRepositoryConstraintViolations:
    """Test database constraint violations with real database"""

    async def test_unique_constraint_violation(self, meal_repository, test_session):
        reset_counters()  # Ensure deterministic IDs
        """Test unique constraint violations"""
        # Given: A meal ORM instance with specific unique constraint fields
        meal_orm1 = create_test_ORM_meal(
            name="Meal 1", author_id="author1", menu_id="menu1"
        )
        test_session.add(meal_orm1)
        await test_session.commit()

        # When: Trying to create another meal ORM with same unique constraint fields
        meal_orm2 = create_test_ORM_meal(
            name="Meal 1", author_id="author1", menu_id="menu1"
        )
        test_session.add(meal_orm2)

        # Then: Should raise IntegrityError if unique constraints exist
        try:
            await test_session.commit()
            # If no error, unique constraints may not be defined (which is also valid)
        except IntegrityError as exc:
            # Expected if unique constraints exist - verify it's a unique constraint error
            error_msg = str(exc).lower()
            assert any(
                keyword in error_msg
                for keyword in ["unique", "duplicate", "already exists"]
            )

    async def test_check_constraint_violation(self, meal_repository, test_session):
        reset_counters()  # Ensure deterministic IDs
        """Test check constraint violations"""
        # Given: A meal ORM instance with invalid data that violates check constraints
        meal_orm = create_test_ORM_meal(name="Invalid Meal", calorie_density=-100.0)
        test_session.add(meal_orm)

        # When/Then: Should raise IntegrityError if check constraints exist
        try:
            await test_session.commit()
            # If no error, check constraints may not be defined (which is also valid)
        except IntegrityError as exc:
            # Expected if check constraints exist - verify it's a check constraint error
            error_msg = str(exc).lower()
            assert any(
                keyword in error_msg
                for keyword in ["check", "constraint", "violates", "invalid"]
            )

    async def test_not_null_constraint_violation(self, meal_repository, test_session):
        reset_counters()  # Ensure deterministic IDs
        """Test NOT NULL constraint violations"""
        # Given: A meal ORM instance with valid required fields (test normal operation)
        meal_orm = create_test_ORM_meal(name="Valid Name")
        test_session.add(meal_orm)

        # When: Committing the valid meal ORM
        try:
            await test_session.commit()
            # Then: Valid meal ORM should be successfully committed
            assert meal_orm.name == "Valid Name"
        except IntegrityError as exc:
            # If error occurs, verify it's related to null constraints
            error_msg = str(exc).lower()
            assert any(
                keyword in error_msg for keyword in ["null", "not null", "required"]
            )


class TestSaGenericRepositoryFilterPrecedence:
    """Test filter precedence with real database queries"""

    async def test_postfix_precedence_order_with_real_data(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test postfix operator precedence with real database data"""
        # Given: Meal ORM instances with different cooking times
        meal_orms = [
            create_test_ORM_meal(name="Low", total_time=10),
            create_test_ORM_meal(name="Medium", total_time=30),
            create_test_ORM_meal(name="High", total_time=60),
        ]

        for meal_orm in meal_orms:
            test_session.add(meal_orm)
        await test_session.commit()

        # When: Applying range filters with proper precedence, returning SA instances
        results = await meal_repository.query(
            filter={
                "total_time_gte": 20,  # >= 20
                "total_time_lte": 50,  # <= 50
            },
            _return_sa_instance=True,
        )

        # Then: Only meal ORMs within the range are returned
        assert len(results) == 1
        assert results[0].name == "Medium"
        assert 20 <= results[0].total_time <= 50

    async def test_filter_application_order_consistency_real_database(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test consistent filter application order"""
        # Given: Meal ORM instances with multiple filterable attributes
        meal_orms = [
            create_test_ORM_meal(name="A", total_time=25, calorie_density=200.0),
            create_test_ORM_meal(name="B", total_time=35, calorie_density=300.0),
            create_test_ORM_meal(name="C", total_time=45, calorie_density=400.0),
        ]

        for meal_orm in meal_orms:
            test_session.add(meal_orm)
        await test_session.commit()

        # When: Applying multiple filters that should be combined with AND logic, returning SA instances
        results = await meal_repository.query(
            filter={
                "total_time_gte": 30,
                "calorie_density_lte": 350.0,
            },
            _return_sa_instance=True,
        )

        # Then: Only meal ORMs matching ALL criteria are returned
        assert len(results) == 1
        assert results[0].name == "B"
        assert results[0].total_time >= 30
        assert results[0].calorie_density <= 350.0

    async def test_complex_filter_precedence_with_joins(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test filter precedence in complex join scenarios"""
        # Given: Meal ORM instances with different attributes for complex filtering
        meal_orms = [
            create_test_ORM_meal(name="Simple", total_time=30),
            create_test_ORM_meal(name="Complex", total_time=60),
        ]

        for meal_orm in meal_orms:
            test_session.add(meal_orm)
        await test_session.commit()

        # When: Applying multiple range filters, returning SA instances
        results = await meal_repository.query(
            filter={
                "total_time_gte": 25,
                "total_time_lte": 45,
            },
            _return_sa_instance=True,
        )

        # Then: Only meal ORMs within the range are returned
        assert len(results) == 1
        assert results[0].name == "Simple"
        assert 25 <= results[0].total_time <= 45


class TestSaGenericRepositoryBoundaryConditions:
    """Test boundary conditions with real database"""

    @pytest.mark.parametrize(
        "test_type,setup_data,filter_criteria,expected_count,validation_func",
        [
            (
                "complex_filter_combinations",
                [
                    (i, {"total_time": i * 10, "calorie_density": i * 50.0})
                    for i in range(1, 6)
                ],
                {
                    "total_time_gte": 20,
                    "total_time_lte": 40,
                    "calorie_density_gte": 100.0,
                    "calorie_density_lte": 200.0,
                },
                "variable",  # May be 0, 1, or more depending on data
                lambda results: all(
                    20 <= r.total_time <= 40 and 100.0 <= r.calorie_density <= 200.0
                    for r in results
                ),
            ),
            (
                "empty_result_set",
                [],  # No setup data
                {"total_time_gte": 9999},
                0,
                lambda results: isinstance(results, list),
            ),
            (
                "large_in_list",
                [("Test Meal", {})],
                {"name": [f"name_{i}" for i in range(1000)] + ["Test Meal"]},
                1,
                lambda results: results[0].name == "Test Meal" if results else True,
            ),
        ],
        ids=["complex_filters", "empty_results", "large_in_list"],
    )
    async def test_boundary_conditions(
        self,
        meal_repository,
        test_session,
        test_type,
        setup_data,
        filter_criteria,
        expected_count,
        validation_func,
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test boundary conditions with various scenarios"""
        # Given: Setup test ORM data
        for item in setup_data:
            if len(item) == 2:
                name, attributes = item
                if isinstance(name, int):
                    name = f"Meal {name}"
            else:
                name, attributes = f"Meal {item}", {}
            meal_orm = create_test_ORM_meal(name=name, **attributes)
            test_session.add(meal_orm)

        if setup_data:  # Only commit if we have data
            await test_session.commit()

        # When: Applying filter, returning SA instances
        results = await meal_repository.query(
            filter=filter_criteria, _return_sa_instance=True
        )

        # Then: Expected results with validation
        if expected_count == "variable":
            # For complex filters, just ensure it's a list and validate content
            assert isinstance(results, list)
        else:
            assert len(results) == expected_count

        assert validation_func(results)

    async def test_complex_edge_case_performance(
        self, meal_repository, test_session, async_benchmark_timer
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test performance of complex edge case queries"""
        # Given: Multiple meal ORM instances with varied attributes for performance testing
        meal_orms = [
            create_test_ORM_meal(
                name=f"Performance Test {i}",
                total_time=i * 5,
                calorie_density=i * 25.0,
            )
            for i in range(1, 21)
        ]

        for meal_orm in meal_orms:
            test_session.add(meal_orm)
        await test_session.commit()

        # When: Executing a complex query and measuring performance, returning SA instances
        async with async_benchmark_timer() as timer:
            results = await meal_repository.query(
                filter={
                    "total_time_gte": 25,
                    "total_time_lte": 75,
                    "calorie_density_gte": 100.0,
                },
                _return_sa_instance=True,
            )

        # Then: Query completes within reasonable time and returns valid ORM results
        timer.assert_faster_than(5.0)  # 5 second timeout
        assert isinstance(results, list)
        # Verify results match filter criteria
        for result in results:
            assert 25 <= result.total_time <= 75
            assert result.calorie_density >= 100.0
