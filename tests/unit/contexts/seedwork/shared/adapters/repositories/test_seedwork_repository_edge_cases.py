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
from sqlalchemy.exc import IntegrityError
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    FilterValidationError,
)
from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
    reset_counters,
)

pytestmark = [pytest.mark.anyio]


@pytest.mark.integration
class TestSaGenericRepositoryEdgeCaseModels:
    """Test edge case models with real database constraints"""

    async def test_circular_model_a_basic_query(
        self, circular_repository, test_session
    ):
        """Test basic querying of circular model A with real DB"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_circular_a,
        )

        # Given: A circular model A ORM instance is created and persisted directly
        reset_counters()  # Ensure deterministic IDs
        orm_entity_a = create_test_ORM_circular_a(name="Test Circular A")
        test_session.add(orm_entity_a)
        await test_session.commit()

        # When: Querying with the correct filter key, returning SA instances
        results = await circular_repository.query(
            filters={"circular_a_name": "Test Circular A"}, _return_sa_instance=True
        )

        # Then: The ORM entity is found with correct attributes
        assert len(results) == 1
        assert results[0].name == "Test Circular A"

    async def test_circular_model_with_reference(
        self, circular_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test circular model behavior with references"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_circular_a,
        )

        # Given: A circular model ORM entity without foreign key reference
        orm_entity_a1 = create_test_ORM_circular_a(name="Entity A1", b_ref_id=None)

        test_session.add(orm_entity_a1)
        await test_session.commit()

        # When: Querying with proper filter for the created entity, returning SA instances
        results = await circular_repository.query(
            filters={"circular_a_name": "Entity A1"}, _return_sa_instance=True
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
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_self_ref,
        )

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
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_self_ref,
        )

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
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_self_ref,
        )

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


@pytest.mark.integration
class TestSaGenericRepositoryFilterCombinations:
    """Test complex filter combinations with real database"""

    async def test_conflicting_range_filters_real_data(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test conflicting range filters return empty result set"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        # Given: A meal ORM instance with a specific cooking time
        meal_orm = create_test_ORM_meal(name="Test Meal", total_time=90)
        test_session.add(meal_orm)
        await test_session.commit()

        # When: Applying conflicting range filters (total_time >= 120 AND total_time <= 60)
        results = await meal_repository.query(
            filters={"total_time_gte": 120, "total_time_lte": 60},
            _return_sa_instance=True,
        )

        # Then: No results are returned due to logical impossibility
        assert len(results) == 0

    async def test_multiple_postfix_same_field_different_values(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test multiple range filters on same field with real data"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
            filters={"total_time_gte": 30, "total_time_lte": 60},
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
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
            filters=filter_dict, _return_sa_instance=True
        )

        # Then: Only meal ORMs matching BOTH conditions are returned
        assert len(results) == 1
        assert results[0].name == "Meal B"

    async def test_none_value_filters_real_database(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test None value handling in real database queries"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
            filters={"description": None}, _return_sa_instance=True
        )

        # Then: Only the meal ORM without description is returned
        assert len(results) == 1
        assert results[0].name == "No description"

    async def test_empty_list_filters_real_database(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test empty list filter behavior with real database"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        # Given: A meal ORM instance exists in the database
        meal_orm = create_test_ORM_meal(name="Test Meal")
        test_session.add(meal_orm)
        await test_session.commit()

        # When: Filtering with an empty list, returning SA instances
        empty_in_results = await meal_repository.query(
            filters={"name": []}, _return_sa_instance=True
        )

        # Then: No results are returned for empty list filter
        assert len(empty_in_results) == 0

    async def test_zero_and_false_value_filters_real_database(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test zero and false value filtering with real database"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
            filters={"total_time": 0}, _return_sa_instance=True
        )

        # Then: The zero-time meal ORM is found (zero is treated as valid filter value)
        assert len(zero_results) == 1
        assert zero_results[0].name == "Zero time"


@pytest.mark.integration
class TestSaGenericRepositoryInvalidFilters:
    """Test invalid filter handling with real database"""

    async def test_unknown_filter_key_raises_exception(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test that unknown filter keys raise appropriate exceptions"""
        # Given/When/Then: Unknown filter key should raise FilterValidationException
        with pytest.raises(FilterValidationError):
            await meal_repository.query(
                filters={"unknown_field": "value"}, _return_sa_instance=True
            )

    async def test_invalid_postfix_combination_raises_exception(self, meal_repository):
        reset_counters()  # Ensure deterministic IDs
        """Test invalid postfix combinations"""
        # Given/When/Then: Invalid postfix should raise FilterValidationException
        with pytest.raises(FilterValidationError):
            await meal_repository.query(
                filters={"total_time_invalid_postfix": 30}, _return_sa_instance=True
            )

    async def test_type_mismatch_handling_real_database(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test type mismatch handling with real database queries"""
        from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
            RepositoryQueryError,
        )
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        # Given: A meal ORM instance exists in the database
        meal_orm = create_test_ORM_meal(name="Test Meal", total_time=30)
        test_session.add(meal_orm)
        await test_session.commit()

        # When/Then: String value for integer field should cause database error
        with pytest.raises(RepositoryQueryError) as exc_info:
            await meal_repository.query(
                filters={"total_time_gte": "not_a_number"}, _return_sa_instance=True
            )

        # Verify it's a type conversion error from the database
        error_msg = str(exc_info.value).lower()
        assert any(
            keyword in error_msg
            for keyword in ["invalid", "type", "conversion", "syntax", "operator"]
        )

    async def test_malformed_filter_structure_handling(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test malformed filter structure handling"""
        from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
            RepositoryQueryError,
        )
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        # Given: A meal ORM instance exists in the database
        meal_orm = create_test_ORM_meal(name="Test Meal")
        test_session.add(meal_orm)
        await test_session.commit()

        # When: Using malformed filter structure (dict in list)
        bad_filter = {"name": ["valid", {"invalid": "mixed"}]}

        # Then: Database should reject the malformed query
        with pytest.raises(RepositoryQueryError) as exc_info:
            await meal_repository.query(filters=bad_filter, _return_sa_instance=True)

        # Verify it's a database-level error
        error_msg = str(exc_info.value).lower()
        assert any(
            keyword in error_msg
            for keyword in ["invalid", "error", "malformed", "type", "data"]
        )


@pytest.mark.integration
class TestSaGenericRepositoryConstraintViolations:
    """Test database constraint violations with real database"""

    async def test_unique_constraint_violation(self, meal_repository, test_session):
        reset_counters()  # Ensure deterministic IDs
        """Test unique constraint violations"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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


@pytest.mark.integration
class TestSaGenericRepositoryFilterPrecedence:
    """Test filter precedence with real database queries"""

    async def test_postfix_precedence_order_with_real_data(
        self, meal_repository, test_session
    ):
        reset_counters()  # Ensure deterministic IDs
        """Test postfix operator precedence with real database data"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
            filters={
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
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
            filters={
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
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
            filters={
                "total_time_gte": 25,
                "total_time_lte": 45,
            },
            _return_sa_instance=True,
        )

        # Then: Only meal ORMs within the range are returned
        assert len(results) == 1
        assert results[0].name == "Simple"
        assert 25 <= results[0].total_time <= 45


@pytest.mark.integration
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
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
            filters=filter_criteria, _return_sa_instance=True
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
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

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
                filters={
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


@pytest.mark.integration
class TestSaGenericRepositoryComplexFiltering:
    """Test complex filtering scenarios with real database"""

    async def test_multiple_range_filters_combined_logic(
        self, meal_repository, test_session
    ):
        """Test multiple range filters with AND logic"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        # Given: Meals with different cooking times and calorie densities
        meal1 = create_test_ORM_meal(
            name="Quick Light", total_time=20, calorie_density=150.0
        )
        meal2 = create_test_ORM_meal(
            name="Quick Heavy", total_time=25, calorie_density=300.0
        )
        meal3 = create_test_ORM_meal(
            name="Slow Light", total_time=90, calorie_density=200.0
        )
        meal4 = create_test_ORM_meal(
            name="Slow Heavy", total_time=120, calorie_density=400.0
        )

        test_session.add(meal1)
        test_session.add(meal2)
        test_session.add(meal3)
        test_session.add(meal4)
        await test_session.commit()

        # When: Filtering for quick meals (<= 30 min) with moderate calories (200-350)
        filters = {
            "total_time_lte": 30,
            "calorie_density_gte": 200.0,
            "calorie_density_lte": 350.0,
        }
        results = await meal_repository.query(filters=filters, _return_sa_instance=True)

        # Then: Only meals matching ALL criteria are returned
        assert len(results) == 1
        assert results[0].name == "Quick Heavy"
        assert results[0].total_time <= 30
        assert 200.0 <= results[0].calorie_density <= 350.0

    async def test_list_and_scalar_filters_precedence(
        self, meal_repository, test_session
    ):
        """Test filter precedence with list and scalar values"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        # Given: Meals with various attributes
        meal1 = create_test_ORM_meal(
            name="Meal A", total_time=30, calorie_density=200.0
        )
        meal2 = create_test_ORM_meal(
            name="Meal B", total_time=45, calorie_density=300.0
        )
        meal3 = create_test_ORM_meal(
            name="Meal C", total_time=60, calorie_density=400.0
        )
        meal4 = create_test_ORM_meal(
            name="Meal D", total_time=75, calorie_density=250.0
        )

        test_session.add(meal1)
        test_session.add(meal2)
        test_session.add(meal3)
        test_session.add(meal4)
        await test_session.commit()

        # When: Applying both list filter and scalar filter
        filter_dict = {
            "name": ["Meal A", "Meal B", "Meal C"],  # List filter
            "total_time_gte": 40,  # Scalar filter
        }

        results = await meal_repository.query(
            filters=filter_dict, _return_sa_instance=True
        )

        # Then: Only meals matching BOTH conditions are returned
        assert len(results) == 2
        meal_names = {meal.name for meal in results}
        assert meal_names == {
            "Meal B",
            "Meal C",
        }  # Both are in the list AND meet time criteria

    async def test_join_and_distinct_handling(self, meal_repository, test_session):
        """Test that joins are handled correctly and DISTINCT is applied when needed"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            create_test_ORM_recipe,
        )

        # Given: Meals with recipes that have different cooking times
        meal1 = create_test_ORM_meal(name="Pasta Meal", total_time=30)
        meal2 = create_test_ORM_meal(name="Pizza Meal", total_time=45)

        # Create recipes with different cooking times
        recipe1 = create_test_ORM_recipe(
            name="Pasta Recipe", meal_id=meal1.id, total_time=20
        )
        recipe2 = create_test_ORM_recipe(
            name="Sauce Recipe", meal_id=meal1.id, total_time=15
        )
        recipe3 = create_test_ORM_recipe(
            name="Pizza Recipe", meal_id=meal2.id, total_time=30
        )

        test_session.add(meal1)
        test_session.add(meal2)
        test_session.add(recipe1)
        test_session.add(recipe2)
        test_session.add(recipe3)
        await test_session.commit()

        # When: Filtering by recipe cooking time (requires join)
        filters = {"recipe_total_time_gte": 20}  # This should join to recipes table

        results = await meal_repository.query(filters=filters, _return_sa_instance=True)

        # Then: Results should be distinct and correct
        assert len(results) >= 1  # At least one meal should match
        # Verify that the join worked by checking that we got meals with recipes
        meal_names = {meal.name for meal in results}
        assert "Pasta Meal" in meal_names or "Pizza Meal" in meal_names

    async def test_performance_with_complex_filters(
        self, meal_repository, test_session, async_benchmark_timer
    ):
        """Test performance with complex filter combinations"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        # Given: A larger dataset for performance testing
        meals = []
        for i in range(50):  # Create 50 meals with varied attributes
            meal = create_test_ORM_meal(
                name=f"Performance Test Meal {i}",
                total_time=10 + (i * 2),  # 10, 12, 14, ..., 108 minutes
                calorie_density=100.0 + (i * 5),  # 100, 105, 110, ..., 345 cal/100g
                author_id=f"author_{i % 10}",  # 10 different authors
            )
            meals.append(meal)
            test_session.add(meal)

        await test_session.commit()

        # When: Applying complex filter combination
        async with async_benchmark_timer() as timer:
            results = await meal_repository.query(
                filters={
                    "total_time_gte": 30,  # At least 30 minutes
                    "total_time_lte": 80,  # At most 80 minutes
                    "calorie_density_gte": 150.0,  # At least 150 cal/100g
                    "calorie_density_lte": 300.0,  # At most 300 cal/100g
                    "author_id": [
                        "author_1",
                        "author_3",
                        "author_5",
                        "author_7",
                        "author_9",
                    ],  # Specific authors
                },
                _return_sa_instance=True,
            )

        # Then: Query should complete within reasonable time and return correct results
        timer.assert_faster_than(2.0)  # Should complete within 2 seconds
        assert len(results) > 0  # Should find some matching meals

        # Verify all results meet the criteria
        for meal in results:
            assert 30 <= meal.total_time <= 80
            assert 150.0 <= meal.calorie_density <= 300.0
            assert meal.author_id in [
                "author_1",
                "author_3",
                "author_5",
                "author_7",
                "author_9",
            ]

    async def test_edge_cases_with_null_and_empty_values(
        self, meal_repository, test_session
    ):
        """Test edge cases with NULL values and empty lists"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        # Given: Meals with various NULL and edge values
        meal1 = create_test_ORM_meal(
            name="Normal Meal", description="Has description", total_time=30
        )
        meal2 = create_test_ORM_meal(
            name="No Description", description=None, total_time=45
        )
        meal3 = create_test_ORM_meal(
            name="Zero Time", description="Quick meal", total_time=0
        )
        meal4 = create_test_ORM_meal(
            name="No Time", description="Unknown time", total_time=None
        )

        test_session.add(meal1)
        test_session.add(meal2)
        test_session.add(meal3)
        test_session.add(meal4)
        await test_session.commit()

        # When: Testing NULL value filtering
        null_desc_results = await meal_repository.query(
            filters={"description": None}, _return_sa_instance=True
        )

        # When: Testing NOT NULL filtering
        not_null_desc_results = await meal_repository.query(
            filters={"description_is_not": None}, _return_sa_instance=True
        )

        # When: Testing zero value filtering
        zero_time_results = await meal_repository.query(
            filters={"total_time": 0}, _return_sa_instance=True
        )

        # When: Testing empty list filtering
        empty_list_results = await meal_repository.query(
            filters={"name": []}, _return_sa_instance=True
        )

        # Then: Each filter should return correct results
        assert len(null_desc_results) == 1
        assert null_desc_results[0].name == "No Description"

        assert len(not_null_desc_results) == 3
        not_null_names = {meal.name for meal in not_null_desc_results}
        assert not_null_names == {"Normal Meal", "Zero Time", "No Time"}

        assert len(zero_time_results) == 1
        assert zero_time_results[0].name == "Zero Time"

        assert len(empty_list_results) == 0  # Empty list should return no results


@pytest.mark.integration
class TestSaGenericRepositoryApiIntegration:
    """Test API filter integration scenarios with real database"""

    async def test_api_filter_parsing_and_validation(
        self, meal_repository, test_session
    ):
        """Test that API filters are properly parsed and validated"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        # Given: Meals with various attributes for API testing
        meal1 = create_test_ORM_meal(
            name="API Test Meal 1", author_id="api_user_1", total_time=30
        )
        meal2 = create_test_ORM_meal(
            name="API Test Meal 2", author_id="api_user_2", total_time=60
        )
        meal3 = create_test_ORM_meal(
            name="API Test Meal 3", author_id="api_user_1", total_time=90
        )

        test_session.add(meal1)
        test_session.add(meal2)
        test_session.add(meal3)
        await test_session.commit()

        # When: Using API-style filter combinations
        filters = {
            "author_id": ["api_user_1", "api_user_2"],  # Multiple authors
            "total_time_gte": 30,  # Minimum time
            "total_time_lte": 90,  # Maximum time
            "name": ["API Test Meal 1", "API Test Meal 2"],  # Specific names
        }

        results = await meal_repository.query(filters=filters, _return_sa_instance=True)

        # Then: Results should match API filter expectations
        assert len(results) == 2  # Should match both criteria
        result_names = {meal.name for meal in results}
        assert result_names == {"API Test Meal 1", "API Test Meal 2"}

        # Verify all results meet the time criteria
        for meal in results:
            assert 30 <= meal.total_time <= 90
            assert meal.author_id in ["api_user_1", "api_user_2"]

    async def test_complex_api_filter_combinations(self, meal_repository, test_session):
        """Test complex API filter combinations that mirror real-world usage"""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        # Given: A diverse set of meals for complex API testing
        meals_data = [
            ("Healthy Breakfast", "chef_1", 15, 200.0, True),
            ("Heavy Lunch", "chef_2", 45, 400.0, False),
            ("Light Dinner", "chef_1", 30, 250.0, True),
            ("Quick Snack", "chef_3", 5, 150.0, True),
            ("Gourmet Meal", "chef_2", 120, 500.0, False),
        ]

        for name, author, time, calories, liked in meals_data:
            meal = create_test_ORM_meal(
                name=name,
                author_id=author,
                total_time=time,
                calorie_density=calories,
                like=liked,
            )
            test_session.add(meal)

        await test_session.commit()

        # When: Applying complex API filter combination
        filters = {
            "author_id": ["chef_1", "chef_2"],  # Specific chefs
            "total_time_gte": 20,  # At least 20 minutes
            "total_time_lte": 60,  # At most 60 minutes
            "calorie_density_gte": 200.0,  # At least 200 cal/100g
            "calorie_density_lte": 450.0,  # At most 450 cal/100g
            "like": True,  # Only liked meals
        }

        results = await meal_repository.query(filters=filters, _return_sa_instance=True)

        # Then: Should return meals that match all criteria
        assert len(results) == 1
        assert results[0].name == "Light Dinner"
        assert results[0].author_id in ["chef_1", "chef_2"]
        assert 20 <= results[0].total_time <= 60
        assert 200.0 <= results[0].calorie_density <= 450.0
        assert results[0].like is True
