"""
Comprehensive test suite for UserRepository following seedwork patterns.
Uses real database testing with deterministic data factories.

Following user requirements:
- Create ORM models directly using data factories
- Use db session directly instead of repository for add/update operations
- Always use _return_sa_model = True when querying the repository
- Use get_sa_instance instead of get method
- Goal: bypass mapper logic that converts between domain and ORM models

Test classes:
- TestUserRepositoryCore: Basic CRUD operations with real database
- TestUserRepositoryRoles: Role relationship testing
- TestUserRepositoryFiltering: Filter operations and complex queries
- TestUserRepositoryErrorHandling: Constraint violations and edge cases
- TestUserRepositoryPerformance: Performance benchmarks and bulk operations
- TestSpecializedUserFactories: Tests for specialized user types
"""

import time
from typing import Any

import pytest
from sqlalchemy.exc import IntegrityError
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.adapters.repositories.user_repository import UserRepo

# Import all data factories
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    EntityNotFoundError,
    FilterValidationError,
)
from tests.contexts.iam.core.adapters.repositories.user_data_factories import (
    create_admin_user_orm,
    create_basic_user_orm,
    create_discarded_user_orm,
    create_multi_role_user_orm,
    create_role_orm,
    create_user,
    create_user_manager_orm,
    create_user_orm,
    get_performance_test_scenarios,
    get_permission_scenarios_orm,
    get_role_relationship_scenarios_orm,
    get_user_filter_scenarios_orm,
)

# =============================================================================
# TEST CLASSES
# =============================================================================


class TestUserRepositoryCore:
    """Test basic CRUD operations using real database and bypassing mapper logic"""

    async def test_get_user_by_id(self, user_repository: UserRepo, test_session):
        """Test getting user by ID using get_sa_instance to bypass mapper logic"""
        # Create user ORM directly and add to database
        user_orm = create_user_orm(id="test_user_001")
        role_orm = create_role_orm(name="user", context="IAM", permissions="read")
        user_orm.roles = [role_orm]

        # Add directly to database session, bypassing repository
        test_session.add(role_orm)
        test_session.add(user_orm)
        await test_session.commit()

        # Query using repository with sa_model return to bypass mapper
        result = await user_repository.get_sa_instance("test_user_001")

        # Verify result is ORM model, not domain model
        assert isinstance(result, UserSaModel)
        assert result.id == "test_user_001"
        assert result.discarded is False
        assert result.version == 1
        assert len(result.roles) == 1
        assert result.roles[0].name == "user"
        assert result.roles[0].context == "IAM"

    async def test_get_sa_instance(self, user_repository: UserRepo, test_session):
        """Test get_sa_instance method returns ORM model directly"""
        # Create and persist user directly to database
        user_orm = create_user_orm(id="test_sa_user")
        admin_role = create_role_orm(
            name="administrator",
            context="IAM",
            permissions="read, write, delete, admin",
        )
        user_orm.roles = [admin_role]

        test_session.add(admin_role)
        test_session.add(user_orm)
        await test_session.commit()

        # Use get_sa_instance to bypass mapper
        result = await user_repository.get_sa_instance("test_sa_user")

        # Verify we get ORM model with all attributes
        assert isinstance(result, UserSaModel)
        assert result.id == "test_sa_user"
        assert result.version == 1
        assert not result.discarded
        assert len(result.roles) == 1
        assert result.roles[0].name == "administrator"

    async def test_persist_user_fails_without_add(self, user_repository: UserRepo):
        """Test that persist fails when user hasn't been added to repository first"""
        user = create_user(id="not_added_user")

        with pytest.raises(
            Exception
        ):  # Should fail because user not in repository.seen
            await user_repository.persist(user)

    async def test_persist_all_users_fails_without_add(self, user_repository: UserRepo):
        """Test that persist_all fails when users haven't been added to repository first"""
        users = [create_user(id="not_added_1"), create_user(id="not_added_2")]

        with pytest.raises(
            Exception
        ):  # Should fail because users not in repository.seen
            await user_repository.persist_all(users)

    @pytest.mark.parametrize("user_count", [1, 5, 10, 25])
    async def test_query_all_users(self, user_repository: UserRepo, user_count: int):
        """Test querying all users with _return_sa_model=True to bypass mapper"""
        async_session = user_repository._session

        # Create roles once and reuse them to avoid unique constraint violations
        admin_role = create_role_orm(
            name="administrator",
            context="IAM",
            permissions="read, write, delete, admin",
        )
        basic_role = create_role_orm(name="user", context="IAM", permissions="read")
        async_session.add(admin_role)
        async_session.add(basic_role)

        # Create varied users directly in database
        for i in range(user_count):
            if i % 2 == 0:
                user_orm = create_user_orm(id=f"user_{i+1:03d}")
                user_orm.roles = [admin_role]
            else:
                user_orm = create_user_orm(id=f"user_{i+1:03d}")
                user_orm.roles = [basic_role]

            async_session.add(user_orm)

        await async_session.commit()

        # Query with _return_sa_model=True to bypass mapper
        results = await user_repository.query(_return_sa_instance=True)

        assert len(results) == user_count
        for result in results:
            assert isinstance(result, UserSaModel)
            assert result.id.startswith("user_")
            assert len(result.roles) >= 1

    async def test_query_with_filters(self, user_repository: UserRepo):
        """Test query filtering using _return_sa_model=True"""
        # Create users with different roles directly in database
        admin_user = create_admin_user_orm(id="admin_001")
        basic_user = create_basic_user_orm(id="basic_001")
        manager_user = create_user_manager_orm(id="manager_001")

        async_session = user_repository._session

        # Add all roles first
        for user_orm in [admin_user, basic_user, manager_user]:
            for role in user_orm.roles:
                async_session.add(role)

        # Add users
        async_session.add(admin_user)
        async_session.add(basic_user)
        async_session.add(manager_user)
        await async_session.commit()

        # Filter by role context and name - should return admin only
        admin_results = await user_repository.query(
            filters={"context": "IAM", "name": "administrator"},
            _return_sa_instance=True,
        )

        assert len(admin_results) == 1
        assert isinstance(admin_results[0], UserSaModel)
        assert admin_results[0].id == "admin_001"
        assert any(role.name == "administrator" for role in admin_results[0].roles)

    async def test_roles_are_persisted_after_user_creation(
        self, user_repository: UserRepo, test_session
    ):
        """Test that user roles are properly persisted in database"""
        # Create user with multiple roles using ORM factory
        multi_role_user = create_multi_role_user_orm(id="multi_role_test")

        # Add roles first, then user to database
        for role in multi_role_user.roles:
            test_session.add(role)
        test_session.add(multi_role_user)
        await test_session.commit()

        # Query back using get_sa_instance to bypass mapper
        result = await user_repository.get_sa_instance("multi_role_test")

        assert isinstance(result, UserSaModel)
        assert len(result.roles) == 3  # user, user_manager, auditor
        role_names = [role.name for role in result.roles]
        assert "user" in role_names
        assert "user_manager" in role_names
        assert "auditor" in role_names

    async def test_role_update_through_user_modification(
        self, user_repository: UserRepo, test_session
    ):
        """Test updating user roles through direct database manipulation"""
        # Create user with basic role
        user_orm = create_basic_user_orm(id="role_update_test")

        # Add to database
        for role in user_orm.roles:
            test_session.add(role)
        test_session.add(user_orm)
        await test_session.commit()

        # Verify initial state
        initial_result = await user_repository.get_sa_instance("role_update_test")
        assert len(initial_result.roles) == 1
        assert initial_result.roles[0].name == "user"

        # Add admin role directly through database session
        admin_role = create_role_orm(
            name="administrator",
            context="IAM",
            permissions="read, write, delete, admin",
        )
        test_session.add(admin_role)

        # Update user's roles
        initial_result.roles.append(admin_role)
        await test_session.commit()

        # Query again to verify update
        updated_result = await user_repository.get_sa_instance("role_update_test")
        assert len(updated_result.roles) == 2
        role_names = [role.name for role in updated_result.roles]
        assert "user" in role_names
        assert "administrator" in role_names

    async def test_relationship_queries_no_duplicate_rows(
        self, user_repository: UserRepo, test_session
    ):
        """Test that role relationships don't cause duplicate user rows"""
        # Create user with multiple roles
        user_orm = create_multi_role_user_orm(id="no_duplicate_test")

        # Add roles and user to database
        for role in user_orm.roles:
            test_session.add(role)
        test_session.add(user_orm)
        await test_session.commit()

        # Query with role filter - should return single user despite multiple roles
        results = await user_repository.query(
            filters={"context": "IAM"}, _return_sa_instance=True
        )

        # Should find exactly one user, not duplicated per role
        user_ids = [user.id for user in results]
        assert user_ids.count("no_duplicate_test") == 1

        # Verify the returned user has all expected roles
        user_result = next(user for user in results if user.id == "no_duplicate_test")
        assert len(user_result.roles) == 3


class TestUserRepositoryRoles:
    """Test role relationship functionality with real database"""

    @pytest.mark.parametrize("scenario", get_role_relationship_scenarios_orm())
    async def test_role_relationship_scenarios_with_real_data(
        self, user_repository: UserRepo, test_session, scenario
    ):
        """Test various role relationship scenarios using factory scenarios"""
        # Create user with specified roles using ORM factory
        user_kwargs = scenario["user_kwargs"]
        user_orm = create_user_orm(**user_kwargs)

        # Add roles first, then user
        for role in user_orm.roles:
            test_session.add(role)
        test_session.add(user_orm)
        await test_session.commit()

        # Test the filter
        filter_params = scenario["filter"]
        results = await user_repository.query(
            filters=filter_params, _return_sa_instance=True
        )

        if scenario["should_match"]:
            assert (
                len(results) >= 1
            ), f"Scenario {scenario['scenario_id']} should match but didn't"
            assert user_orm.id in [user.id for user in results]
        else:
            user_ids = [user.id for user in results]
            assert (
                user_orm.id not in user_ids
            ), f"Scenario {scenario['scenario_id']} should not match but did"

    @pytest.mark.parametrize("scenario", get_permission_scenarios_orm())
    async def test_permission_validation_scenarios_with_real_data(
        self, user_repository: UserRepo, test_session, scenario
    ):
        """Test permission validation scenarios"""
        # Create user based on scenario
        user_kwargs = scenario["user_kwargs"]
        user_orm = create_user_orm(**user_kwargs)

        # Add roles and user to database
        for role in user_orm.roles:
            test_session.add(role)
        test_session.add(user_orm)
        await test_session.commit()

        # Query user back
        result = await user_repository.get_sa_instance(user_orm.id)

        # Verify expected permissions exist in roles
        if "expected_permissions" in scenario:
            all_permissions = []
            for role in result.roles:
                all_permissions.extend(role.permissions.split(", "))

            for expected_perm in scenario["expected_permissions"]:
                assert (
                    expected_perm in all_permissions
                ), f"Missing permission {expected_perm} in scenario {scenario['scenario_id']}"

    async def test_role_context_filtering_with_real_data(
        self, user_repository: UserRepo, test_session
    ):
        """Test filtering users by role context"""
        # Create users with roles in different contexts
        iam_user = create_user_orm(
            id="iam_context_user",
            roles=[create_role_orm(name="user", context="IAM", permissions="read")],
        )
        recipes_user = create_user_orm(
            id="recipes_context_user",
            roles=[
                create_role_orm(
                    name="user", context="recipes_catalog", permissions="read"
                )
            ],
        )

        # Add to database
        for user_orm in [iam_user, recipes_user]:
            for role in user_orm.roles:
                test_session.add(role)
            test_session.add(user_orm)
        await test_session.commit()

        # Filter by IAM context only
        iam_results = await user_repository.query(
            filters={"context": "IAM"}, _return_sa_instance=True
        )

        # Should only return IAM user
        assert len(iam_results) == 1
        assert iam_results[0].id == "iam_context_user"
        assert iam_results[0].roles[0].context == "IAM"

    async def test_role_name_filtering_with_real_roles(
        self, user_repository: UserRepo, test_session
    ):
        """Test filtering users by specific role names"""
        # Create users with different role names
        admin_user = create_admin_user_orm(id="admin_role_user")
        manager_user = create_user_manager_orm(id="manager_role_user")
        basic_user = create_basic_user_orm(id="basic_role_user")

        # Add all users to database
        all_users = [admin_user, manager_user, basic_user]
        for user_orm in all_users:
            for role in user_orm.roles:
                test_session.add(role)
            test_session.add(user_orm)
        await test_session.commit()

        # Filter by administrator role only
        admin_results = await user_repository.query(
            filters={"name": "administrator"}, _return_sa_instance=True
        )

        assert len(admin_results) == 1
        assert admin_results[0].id == "admin_role_user"
        assert any(role.name == "administrator" for role in admin_results[0].roles)

        # Filter by user_manager role only
        manager_results = await user_repository.query(
            filters={"name": "user_manager"}, _return_sa_instance=True
        )

        assert len(manager_results) == 1
        assert manager_results[0].id == "manager_role_user"
        assert any(role.name == "user_manager" for role in manager_results[0].roles)

    async def test_multiple_role_combinations_with_database(
        self, user_repository: UserRepo, test_session
    ):
        """Test users with multiple role combinations"""
        # Create user with multiple roles spanning different contexts
        multi_context_user = create_user_orm(
            id="multi_context_user",
            roles=[
                create_role_orm(name="user", context="IAM", permissions="read"),
                create_role_orm(
                    name="administrator",
                    context="recipes_catalog",
                    permissions="read, write, delete",
                ),
                create_role_orm(
                    name="auditor",
                    context="products_catalog",
                    permissions="read, audit",
                ),
            ],
        )

        # Add to database
        for role in multi_context_user.roles:
            test_session.add(role)
        test_session.add(multi_context_user)
        await test_session.commit()

        # Should match when filtering by any of the contexts
        iam_results = await user_repository.query(
            filters={"context": "IAM"}, _return_sa_instance=True
        )
        assert len(iam_results) == 1
        assert iam_results[0].id == "multi_context_user"

        recipes_results = await user_repository.query(
            filters={"context": "recipes_catalog"}, _return_sa_instance=True
        )
        assert len(recipes_results) == 1
        assert recipes_results[0].id == "multi_context_user"

    async def test_role_validation_with_orm_models(
        self, user_repository: UserRepo, test_session
    ):
        """Test role validation with ORM models"""
        # Test valid role creation
        valid_role = create_role_orm(
            name="test_role", context="test_context", permissions="read, write"
        )

        user_orm = create_user_orm(id="role_validation_user", roles=[valid_role])

        test_session.add(valid_role)
        test_session.add(user_orm)
        await test_session.commit()

        # Verify role was created correctly
        result = await user_repository.get_sa_instance("role_validation_user")
        assert len(result.roles) == 1
        assert result.roles[0].name == "test_role"
        assert result.roles[0].context == "test_context"
        assert result.roles[0].permissions == "read, write"


class TestUserRepositoryFiltering:
    """Test filtering functionality with real database"""

    @pytest.mark.parametrize("scenario", get_user_filter_scenarios_orm())
    async def test_user_filter_scenarios_with_real_data(
        self, user_repository: UserRepo, test_session, scenario
    ):
        """Test user filtering scenarios using factory data"""
        # Create user based on scenario
        user_kwargs = scenario["user_kwargs"]
        user_orm = create_user_orm(**user_kwargs)

        # Add roles first if any
        for role in user_orm.roles:
            test_session.add(role)
        test_session.add(user_orm)
        await test_session.commit()

        # Apply filter
        filter_params = scenario["filter"]
        results = await user_repository.query(
            filters=filter_params, _return_sa_instance=True
        )

        if scenario["should_match"]:
            assert (
                len(results) >= 1
            ), f"Scenario {scenario['scenario_id']} should match but didn't"
            assert user_orm.id in [user.id for user in results]
        else:
            user_ids = [user.id for user in results]
            assert (
                user_orm.id not in user_ids
            ), f"Scenario {scenario['scenario_id']} should not match but did"

    async def test_discarded_user_filtering(
        self, user_repository: UserRepo, test_session
    ):
        """Test filtering discarded vs active users"""
        # Create active and discarded users
        active_user = create_user_orm(id="active_user", discarded=False)
        discarded_user = create_user_orm(id="discarded_user", discarded=True)

        # Add basic roles
        basic_role = create_role_orm(name="user", context="IAM", permissions="read")
        test_session.add(basic_role)

        active_user.roles = [basic_role]
        discarded_user.roles = [basic_role]

        test_session.add(active_user)
        test_session.add(discarded_user)
        await test_session.commit()

        # Filter for active users only
        active_results = await user_repository.query(
            filters={"discarded": False}, _return_sa_instance=True
        )

        active_user_ids = [user.id for user in active_results]
        assert "active_user" in active_user_ids
        assert "discarded_user" not in active_user_ids

        # Filter for discarded users only
        discarded_results = await user_repository.query(
            filters={"discarded": True}, _return_sa_instance=True
        )

        discarded_user_ids = [user.id for user in discarded_results]
        assert "discarded_user" in discarded_user_ids
        assert "active_user" not in discarded_user_ids

    async def test_version_filtering_with_real_data(
        self, user_repository: UserRepo, test_session
    ):
        """Test filtering users by version"""
        # Create users with different versions
        v1_user = create_user_orm(id="version_1_user", version=1)
        v2_user = create_user_orm(id="version_2_user", version=2)
        v5_user = create_user_orm(id="version_5_user", version=5)

        basic_role = create_role_orm(name="user", context="IAM", permissions="read")
        test_session.add(basic_role)

        for user_orm in [v1_user, v2_user, v5_user]:
            user_orm.roles = [basic_role]
            test_session.add(user_orm)
        await test_session.commit()

        # Filter by specific version
        v2_results = await user_repository.query(
            filters={"version": 2}, _return_sa_instance=True
        )

        assert len(v2_results) == 1
        assert v2_results[0].id == "version_2_user"
        assert v2_results[0].version == 2

    async def test_combined_filtering_scenarios(
        self, user_repository: UserRepo, test_session
    ):
        """Test complex filtering with multiple criteria"""
        # Create roles once and reuse them to avoid unique constraint violations
        admin_role = create_role_orm(
            name="administrator",
            context="IAM",
            permissions="read, write, delete, admin",
        )
        basic_role = create_role_orm(name="user", context="IAM", permissions="read")
        test_session.add(admin_role)
        test_session.add(basic_role)

        # Create users with various combinations
        admin_active = create_user_orm(id="admin_active", discarded=False, version=1)
        admin_discarded = create_user_orm(
            id="admin_discarded", discarded=True, version=2
        )
        user_active = create_user_orm(id="user_active", discarded=False, version=1)

        # Assign roles to users
        admin_active.roles = [admin_role]
        admin_discarded.roles = [admin_role]
        user_active.roles = [basic_role]

        # Add users
        test_session.add(admin_active)
        test_session.add(admin_discarded)
        test_session.add(user_active)
        await test_session.commit()

        # Filter for active administrators only
        active_admin_results = await user_repository.query(
            filters={"discarded": False, "context": "IAM", "name": "administrator"},
            _return_sa_instance=True,
        )

        assert len(active_admin_results) == 1
        assert active_admin_results[0].id == "admin_active"
        assert not active_admin_results[0].discarded
        assert any(
            role.name == "administrator" for role in active_admin_results[0].roles
        )


class TestUserRepositoryErrorHandling:
    """Test error handling and edge cases"""

    async def test_get_nonexistent_user(self, user_repository: UserRepo):
        """Test getting a user that doesn't exist"""
        with pytest.raises(EntityNotFoundError):
            await user_repository.get_sa_instance("nonexistent_user")

    async def test_get_sa_instance_nonexistent(self, user_repository: UserRepo):
        """Test get_sa_instance with nonexistent user"""
        with pytest.raises(EntityNotFoundError):
            await user_repository.get_sa_instance("nonexistent_sa_user")

    async def test_invalid_filter_parameters(self, user_repository: UserRepo):
        """Test query with invalid filter parameters"""
        with pytest.raises(FilterValidationError):
            results = await user_repository.query(
                filters={"invalid_field": "invalid_value"}, _return_sa_instance=True
            )

    async def test_null_handling_in_filters(self, user_repository: UserRepo):
        """Test that None values in filters are handled gracefully"""
        results = await user_repository.query(
            filters={"discarded": None}, _return_sa_instance=True
        )
        assert isinstance(results, list)

    async def test_empty_filter_dict(self, user_repository: UserRepo):
        """Test query with empty filter dictionary"""
        results = await user_repository.query(filters={}, _return_sa_instance=True)
        assert isinstance(results, list)

    async def test_none_filter(self, user_repository: UserRepo):
        """Test query with empty filter (no filter parameter)"""
        results = await user_repository.query(_return_sa_instance=True)
        assert isinstance(results, list)

    async def test_database_constraint_violations_with_users(
        self, user_repository: UserRepo, test_session
    ):
        """Test various database constraint violations"""
        # Test duplicate primary key (should fail)
        user1 = create_user_orm(id="duplicate_id_test")
        user2 = create_user_orm(id="duplicate_id_test")  # Same ID

        basic_role = create_role_orm(name="user", context="IAM", permissions="read")
        test_session.add(basic_role)

        user1.roles = [basic_role]
        user2.roles = [basic_role]

        test_session.add(user1)
        test_session.add(user2)

        # This should raise IntegrityError due to duplicate primary key
        with pytest.raises(IntegrityError):
            await test_session.commit()

    async def test_role_constraint_validation_with_database(
        self, user_repository: UserRepo, test_session
    ):
        """Test role constraint validation"""
        # Test role with valid composite primary key
        role1 = create_role_orm(
            name="test_role", context="test_context", permissions="read"
        )
        role2 = create_role_orm(
            name="test_role", context="test_context", permissions="write"
        )  # Same composite key

        test_session.add(role1)
        test_session.add(role2)

        # This should raise IntegrityError due to duplicate composite primary key (name, context)
        with pytest.raises(IntegrityError):
            await test_session.commit()


class TestUserRepositoryPerformance:
    """Test performance and bulk operations"""

    @pytest.mark.parametrize("scenario", get_performance_test_scenarios())
    async def test_query_performance_scenarios(
        self, user_repository: UserRepo, scenario: dict[str, Any]
    ):
        """Test query performance with various scenarios"""
        dataset_size = scenario["dataset_size"]
        expected_time = scenario.get("expected_query_time", 1.0)

        # Create roles once and reuse them to avoid unique constraint violations
        async_session = user_repository._session

        admin_role = create_role_orm(
            name="administrator",
            context="IAM",
            permissions="read, write, delete, admin",
        )
        manager_role = create_role_orm(
            name="user_manager", context="IAM", permissions="read, write, manage_users"
        )
        auditor_role = create_role_orm(
            name="auditor", context="IAM", permissions="read, audit"
        )
        user_role = create_role_orm(name="user", context="IAM", permissions="read")

        async_session.add(admin_role)
        async_session.add(manager_role)
        async_session.add(auditor_role)
        async_session.add(user_role)

        # Create users with reused roles
        users = []
        for i in range(dataset_size):
            if i % 4 == 0:
                user_orm = create_user_orm(id=f"perf_user_{i+1:03d}")
                user_orm.roles = [admin_role]
            elif i % 4 == 1:
                user_orm = create_user_orm(id=f"perf_user_{i+1:03d}")
                user_orm.roles = [manager_role]
            elif i % 4 == 2:
                user_orm = create_user_orm(id=f"perf_user_{i+1:03d}")
                user_orm.roles = [user_role, manager_role, auditor_role]
            else:
                user_orm = create_user_orm(id=f"perf_user_{i+1:03d}")
                user_orm.roles = [user_role]
            users.append(user_orm)

        # Add users to database
        for user_orm in users:
            async_session.add(user_orm)
        await async_session.commit()

        # Measure query performance
        start_time = time.perf_counter()

        if "filter" in scenario:
            results = await user_repository.query(
                filters=scenario["filter"], _return_sa_instance=True
            )
        else:
            results = await user_repository.query(_return_sa_instance=True)

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        # Verify performance expectation
        assert (
            elapsed_time <= expected_time
        ), f"Query took {elapsed_time:.3f}s, expected ≤{expected_time}s"
        assert isinstance(results, list)
        assert all(isinstance(user, UserSaModel) for user in results)

    async def test_bulk_persist_performance(
        self, user_repository: UserRepo, test_session
    ):
        """Test bulk user persistence performance"""
        user_count = 50
        expected_time_per_user = 0.01  # 10ms per user

        # Create roles once and reuse them to avoid unique constraint violations
        admin_role = create_role_orm(
            name="administrator",
            context="IAM",
            permissions="read, write, delete, admin",
        )
        manager_role = create_role_orm(
            name="user_manager", context="IAM", permissions="read, write, manage_users"
        )
        basic_role = create_role_orm(name="user", context="IAM", permissions="read")
        test_session.add(admin_role)
        test_session.add(manager_role)
        test_session.add(basic_role)

        # Create users using ORM factories
        users_orm = []
        for i in range(user_count):
            if i % 3 == 0:
                user_orm = create_user_orm(id=f"bulk_user_{i+1:03d}")
                user_orm.roles = [admin_role]
            elif i % 3 == 1:
                user_orm = create_user_orm(id=f"bulk_user_{i+1:03d}")
                user_orm.roles = [manager_role]
            else:
                user_orm = create_user_orm(id=f"bulk_user_{i+1:03d}")
                user_orm.roles = [basic_role]

            users_orm.append(user_orm)

        # Measure bulk insertion time
        start_time = time.perf_counter()

        # Add all users
        for user_orm in users_orm:
            test_session.add(user_orm)

        await test_session.commit()

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        # Verify performance
        time_per_user = elapsed_time / user_count
        assert (
            time_per_user <= expected_time_per_user
        ), f"Bulk creation took {time_per_user:.4f}s per user, expected ≤{expected_time_per_user}s"

        # Verify all users were created
        results = await user_repository.query(_return_sa_instance=True)
        assert len(results) == user_count

    async def test_complex_query_performance(self, user_repository: UserRepo):
        """Test performance of complex queries with role filtering"""
        # Create roles once and reuse them to avoid unique constraint violations
        async_session = user_repository._session

        admin_role = create_role_orm(
            name="administrator",
            context="IAM",
            permissions="read, write, delete, admin",
        )
        manager_role = create_role_orm(
            name="user_manager", context="IAM", permissions="read, write, manage_users"
        )
        auditor_role = create_role_orm(
            name="auditor", context="IAM", permissions="read, audit"
        )
        user_role = create_role_orm(name="user", context="IAM", permissions="read")

        async_session.add(admin_role)
        async_session.add(manager_role)
        async_session.add(auditor_role)
        async_session.add(user_role)

        # Create 100 users with mixed roles
        users = []
        for i in range(100):
            if i % 4 == 0:
                user_orm = create_user_orm(id=f"complex_user_{i+1:03d}")
                user_orm.roles = [admin_role]
            elif i % 4 == 1:
                user_orm = create_user_orm(id=f"complex_user_{i+1:03d}")
                user_orm.roles = [manager_role]
            elif i % 4 == 2:
                user_orm = create_user_orm(id=f"complex_user_{i+1:03d}")
                user_orm.roles = [user_role, manager_role, auditor_role]
            else:
                user_orm = create_user_orm(id=f"complex_user_{i+1:03d}")
                user_orm.roles = [user_role]
            users.append(user_orm)

        # Add all users
        for user_orm in users:
            async_session.add(user_orm)
        await async_session.commit()

        # Complex query with role filtering
        start_time = time.perf_counter()

        results = await user_repository.query(
            filters={"context": "IAM", "discarded": False}, _return_sa_instance=True
        )

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        # Should complete within 1 second for 100 users
        assert (
            elapsed_time <= 1.0
        ), f"Complex query took {elapsed_time:.3f}s, expected ≤1.0s"
        assert len(results) > 0
        assert all(isinstance(user, UserSaModel) for user in results)

    async def test_memory_usage_bulk_operations(self, user_repository: UserRepo):
        """Test memory usage with bulk operations"""
        # Create roles once and reuse them to avoid unique constraint violations
        async_session = user_repository._session

        admin_role = create_role_orm(
            name="administrator",
            context="IAM",
            permissions="read, write, delete, admin",
        )
        manager_role = create_role_orm(
            name="user_manager", context="IAM", permissions="read, write, manage_users"
        )
        auditor_role = create_role_orm(
            name="auditor", context="IAM", permissions="read, audit"
        )
        user_role = create_role_orm(name="user", context="IAM", permissions="read")

        async_session.add(admin_role)
        async_session.add(manager_role)
        async_session.add(auditor_role)
        async_session.add(user_role)

        # Create 50 users with mixed roles
        users = []
        for i in range(50):
            if i % 4 == 0:
                user_orm = create_user_orm(id=f"memory_user_{i+1:03d}")
                user_orm.roles = [admin_role]
            elif i % 4 == 1:
                user_orm = create_user_orm(id=f"memory_user_{i+1:03d}")
                user_orm.roles = [manager_role]
            elif i % 4 == 2:
                user_orm = create_user_orm(id=f"memory_user_{i+1:03d}")
                user_orm.roles = [user_role, manager_role, auditor_role]
            else:
                user_orm = create_user_orm(id=f"memory_user_{i+1:03d}")
                user_orm.roles = [user_role]
            users.append(user_orm)

        # Add all users
        for user_orm in users:
            async_session.add(user_orm)
        await async_session.commit()

        # Query all users multiple times to test memory usage
        for _ in range(5):
            results = await user_repository.query(_return_sa_instance=True)
            assert len(results) == 50
            assert all(isinstance(user, UserSaModel) for user in results)

            # Clear results to free memory
            del results

    async def test_bulk_user_query_performance(
        self, user_repository: UserRepo, test_session
    ):
        """Test performance of querying large numbers of users"""
        user_count = 200

        # Create role once and reuse to avoid unique constraint violations
        basic_role = create_role_orm(name="user", context="IAM", permissions="read")
        test_session.add(basic_role)

        # Create and add users in batches to avoid memory issues
        batch_size = 50
        for batch_start in range(0, user_count, batch_size):
            batch_users = []
            for i in range(batch_start, min(batch_start + batch_size, user_count)):
                user_orm = create_user_orm(id=f"perf_user_{i+1:03d}")
                user_orm.roles = [basic_role]
                batch_users.append(user_orm)

            # Add users
            for user_orm in batch_users:
                test_session.add(user_orm)

        await test_session.commit()

        # Measure query performance
        start_time = time.perf_counter()

        results = await user_repository.query(_return_sa_instance=True)

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        # Should handle 200 users quickly
        assert (
            elapsed_time <= 2.0
        ), f"Bulk query took {elapsed_time:.3f}s for {user_count} users"
        assert len(results) == user_count
        assert all(isinstance(user, UserSaModel) for user in results)


class TestSpecializedUserFactories:
    """Test specialized user factory functions with database persistence"""

    async def test_admin_user_creation_with_database(
        self, user_repository: UserRepo, test_session
    ):
        """Test admin user factory creates proper administrator user"""
        admin_user = create_admin_user_orm(id="test_admin")

        # Add to database
        for role in admin_user.roles:
            test_session.add(role)
        test_session.add(admin_user)
        await test_session.commit()

        # Verify admin user characteristics
        result = await user_repository.get_sa_instance("test_admin")

        assert result.id == "test_admin"
        assert not result.discarded
        assert len(result.roles) == 1
        assert result.roles[0].name == "administrator"
        assert result.roles[0].context == "IAM"
        assert "admin" in result.roles[0].permissions

    async def test_user_manager_creation_with_database(
        self, user_repository: UserRepo, test_session
    ):
        """Test user manager factory creates proper user management user"""
        manager_user = create_user_manager_orm(id="test_manager")

        # Add to database
        for role in manager_user.roles:
            test_session.add(role)
        test_session.add(manager_user)
        await test_session.commit()

        # Verify manager user characteristics
        result = await user_repository.get_sa_instance("test_manager")

        assert result.id == "test_manager"
        assert not result.discarded
        assert len(result.roles) == 1
        assert result.roles[0].name == "user_manager"
        assert result.roles[0].context == "IAM"
        assert "manage_users" in result.roles[0].permissions

    async def test_multi_role_user_creation_with_database(
        self, user_repository: UserRepo, test_session
    ):
        """Test multi-role user factory creates user with multiple roles"""
        multi_user = create_multi_role_user_orm(id="test_multi")

        # Add to database
        for role in multi_user.roles:
            test_session.add(role)
        test_session.add(multi_user)
        await test_session.commit()

        # Verify multi-role user characteristics
        result = await user_repository.get_sa_instance("test_multi")

        assert result.id == "test_multi"
        assert not result.discarded
        assert len(result.roles) == 3

        role_names = [role.name for role in result.roles]
        assert "user" in role_names
        assert "user_manager" in role_names
        assert "auditor" in role_names

    async def test_discarded_user_creation_with_database(
        self, user_repository: UserRepo, test_session
    ):
        """Test discarded user factory creates properly discarded user"""
        discarded_user = create_discarded_user_orm(id="test_discarded")

        # Add basic role (discarded users can still have roles)
        basic_role = create_role_orm(name="user", context="IAM", permissions="read")
        test_session.add(basic_role)
        discarded_user.roles = [basic_role]

        test_session.add(discarded_user)
        await test_session.commit()

        # Verify discarded user characteristics
        result = await user_repository.get_sa_instance(
            "test_discarded", _return_discarded=True
        )

        assert result.id == "test_discarded"
        assert result.discarded is True  # Key characteristic
        assert result.version == 1

    async def test_user_orm_factory_persistence_patterns(
        self, user_repository: UserRepo, test_session
    ):
        """Test that ORM factories work correctly with database persistence"""
        # Create roles once and reuse them to avoid unique constraint violations
        admin_role = create_role_orm(
            name="administrator",
            context="IAM",
            permissions="read, write, delete, admin",
        )
        basic_role = create_role_orm(name="user", context="IAM", permissions="read")
        manager_role = create_role_orm(
            name="user_manager", context="IAM", permissions="read, write, manage_users"
        )
        auditor_role = create_role_orm(
            name="auditor", context="IAM", permissions="read, audit"
        )

        # Add roles first
        test_session.add(admin_role)
        test_session.add(basic_role)
        test_session.add(manager_role)
        test_session.add(auditor_role)

        # Create users manually to test the same patterns as the specialized factories
        admin_user = create_user_orm(id="orm_admin")
        admin_user.roles = [admin_role]

        basic_user = create_user_orm(id="orm_basic")
        basic_user.roles = [basic_role]

        manager_user = create_user_orm(id="orm_manager")
        manager_user.roles = [manager_role]

        multi_user = create_user_orm(id="orm_multi")
        multi_user.roles = [basic_role, manager_role, auditor_role]

        # Add users
        test_session.add(admin_user)
        test_session.add(basic_user)
        test_session.add(manager_user)
        test_session.add(multi_user)

        await test_session.commit()

        # Verify all users were created correctly
        user_ids_and_expected_roles = [
            ("orm_admin", ["administrator"]),
            ("orm_basic", ["user"]),
            ("orm_manager", ["user_manager"]),
            ("orm_multi", ["user", "user_manager", "auditor"]),
        ]

        for user_id, expected_role_names in user_ids_and_expected_roles:
            result = await user_repository.get_sa_instance(user_id)

            assert result.id == user_id
            assert isinstance(result, UserSaModel)
            assert len(result.roles) >= 1
            assert not result.discarded  # All non-discarded factories
            assert result.version == 1

            # Verify expected roles are present
            actual_role_names = [role.name for role in result.roles]
            for expected_role in expected_role_names:
                assert expected_role in actual_role_names
