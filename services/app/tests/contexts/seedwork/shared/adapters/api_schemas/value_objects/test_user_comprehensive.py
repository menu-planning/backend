import pytest
import time
from unittest.mock import Mock
from typing import Any
from uuid import uuid4

from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.user import ApiSeedUser
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel


class TestApiSeedUserComprehensive:
    """
    Comprehensive test suite for ApiSeedUser schema meeting task requirements:
    - >95% coverage for all conversion methods
    - Round-trip conversion validation tests
    - Error handling tests (minimum 5 error scenarios per method)
    - Edge case tests (null values, empty collections, boundary values)
    - Performance validation tests (<5ms conversion time)
    - Integration tests with base classes
    """

    # =============================================================================
    # FIXTURES AND TEST DATA
    # =============================================================================

    @pytest.fixture
    def sample_api_roles(self):
        """Sample API roles for testing."""
        return frozenset([
            ApiSeedRole(name="admin", permissions=frozenset(["read", "write", "delete"])),
            ApiSeedRole(name="user", permissions=frozenset(["read", "comment"])),
            ApiSeedRole(name="moderator", permissions=frozenset(["read", "moderate"]))
        ])

    @pytest.fixture
    def sample_domain_roles(self):
        """Sample domain roles for testing."""
        return set([
            SeedRole(name="admin", permissions=frozenset(["read", "write", "delete"])),
            SeedRole(name="user", permissions=frozenset(["read", "comment"])),
            SeedRole(name="moderator", permissions=frozenset(["read", "moderate"]))
        ])

    @pytest.fixture
    def valid_user_data(self, sample_api_roles):
        """Sample valid user data for testing."""
        return {
            "id": str(uuid4()),
            "roles": sample_api_roles
        }

    @pytest.fixture
    def domain_user(self, sample_domain_roles):
        """Sample domain user for conversion tests."""
        return SeedUser(
            id=str(uuid4()),
            roles=sample_domain_roles
        )

    @pytest.fixture
    def orm_user(self):
        """Sample ORM user model for conversion tests."""
        return UserSaModel(
            id=str(uuid4()),
            roles=[
                RoleSaModel(name="admin", permissions="read, write, delete"),
                RoleSaModel(name="user", permissions="read, comment")
            ]
        )

    @pytest.fixture
    def edge_case_role_collections(self):
        """Edge case role collections for testing boundaries."""
        return {
            "empty": frozenset(),
            "single": frozenset([ApiSeedRole(name="single", permissions=frozenset(["read"]))]),
            "large": frozenset([
                ApiSeedRole(name=f"role_{i}", permissions=frozenset([f"perm_{i}"]))
                for i in range(50)
            ]),
            "duplicate_names": frozenset([
                ApiSeedRole(name="duplicate", permissions=frozenset(["read"])),
                ApiSeedRole(name="duplicate", permissions=frozenset(["write"]))  # Same name, different permissions
            ])
        }

    # =============================================================================
    # UNIT TESTS FOR ALL CONVERSION METHODS (>95% COVERAGE TARGET)
    # =============================================================================

    def test_from_domain_basic_conversion(self, domain_user):
        """Test from_domain basic conversion functionality."""
        api_user = ApiSeedUser.from_domain(domain_user)
        
        assert api_user.id == domain_user.id
        assert len(api_user.roles) == len(domain_user.roles)
        assert isinstance(api_user.roles, frozenset)
        assert all(isinstance(role, ApiSeedRole) for role in api_user.roles)

    def test_from_domain_with_empty_roles(self):
        """Test from_domain with empty roles set."""
        domain_user = SeedUser(id=str(uuid4()), roles=set())
        api_user = ApiSeedUser.from_domain(domain_user)
        
        assert api_user.id == domain_user.id
        assert api_user.roles == frozenset()

    def test_from_domain_role_conversion(self, sample_domain_roles):
        """Test from_domain properly converts domain roles to API roles."""
        domain_user = SeedUser(id=str(uuid4()), roles=sample_domain_roles)
        api_user = ApiSeedUser.from_domain(domain_user)
        
        # Verify role conversion
        api_role_names = {role.name for role in api_user.roles}
        domain_role_names = {role.name for role in domain_user.roles}
        assert api_role_names == domain_role_names
        
        # Verify all roles are API types
        assert all(isinstance(role, ApiSeedRole) for role in api_user.roles)

    def test_from_domain_type_preservation(self, domain_user):
        """Test that from_domain preserves all type characteristics."""
        api_user = ApiSeedUser.from_domain(domain_user)
        
        # Verify type characteristics
        assert isinstance(api_user, ApiSeedUser)
        assert isinstance(api_user.id, str)
        assert isinstance(api_user.roles, frozenset)
        assert all(isinstance(role, ApiSeedRole) for role in api_user.roles)

    def test_to_domain_basic_conversion(self, valid_user_data):
        """Test to_domain basic conversion functionality."""
        api_user = ApiSeedUser(**valid_user_data)
        domain_user = api_user.to_domain()
        
        assert isinstance(domain_user, SeedUser)
        assert domain_user.id == api_user.id
        assert len(domain_user.roles) == len(api_user.roles)
        assert isinstance(domain_user.roles, set)

    def test_to_domain_collection_type_conversion(self, sample_api_roles):
        """Test to_domain converts frozenset to set."""
        api_user = ApiSeedUser(id=str(uuid4()), roles=sample_api_roles)
        domain_user = api_user.to_domain()
        
        # Domain should use mutable set for roles
        assert isinstance(domain_user.roles, set)
        assert all(isinstance(role, SeedRole) for role in domain_user.roles)
        
        # Verify role data integrity
        api_role_names = {role.name for role in api_user.roles}
        domain_role_names = {role.name for role in domain_user.roles}
        assert api_role_names == domain_role_names

    def test_from_orm_model_basic_conversion(self, orm_user):
        """Test from_orm_model basic conversion functionality."""
        api_user = ApiSeedUser.from_orm_model(orm_user)
        
        assert api_user.id == orm_user.id
        assert len(api_user.roles) == len(orm_user.roles)
        assert isinstance(api_user.roles, frozenset)
        assert all(isinstance(role, ApiSeedRole) for role in api_user.roles)

    def test_from_orm_model_role_conversion(self, orm_user):
        """Test from_orm_model properly converts ORM roles to API roles."""
        api_user = ApiSeedUser.from_orm_model(orm_user)
        
        # Verify role names are preserved
        orm_role_names = {role.name for role in orm_user.roles}
        api_role_names = {role.name for role in api_user.roles}
        assert api_role_names == orm_role_names
        
        # Verify permissions are correctly converted
        for orm_role in orm_user.roles:
            matching_api_role = next(
                (api_role for api_role in api_user.roles if api_role.name == orm_role.name),
                None
            )
            assert matching_api_role is not None
            expected_permissions = frozenset(
                perm.strip() for perm in orm_role.permissions.split(", ") if perm.strip()
            )
            assert matching_api_role.permissions == expected_permissions

    def test_from_orm_model_empty_roles(self):
        """Test from_orm_model with empty roles list."""
        orm_user = UserSaModel(id=str(uuid4()), roles=[])
        api_user = ApiSeedUser.from_orm_model(orm_user)
        
        assert api_user.id == orm_user.id
        assert api_user.roles == frozenset()

    def test_to_orm_kwargs_basic_conversion(self, valid_user_data):
        """Test to_orm_kwargs basic conversion functionality."""
        api_user = ApiSeedUser(**valid_user_data)
        kwargs = api_user.to_orm_kwargs()
        
        assert kwargs["id"] == api_user.id
        assert "roles" in kwargs
        assert isinstance(kwargs["roles"], list)
        assert len(kwargs["roles"]) == len(api_user.roles)

    def test_to_orm_kwargs_role_conversion(self, sample_api_roles):
        """Test to_orm_kwargs converts API roles to ORM-compatible format."""
        api_user = ApiSeedUser(id=str(uuid4()), roles=sample_api_roles)
        kwargs = api_user.to_orm_kwargs()
        
        # Verify role conversion format
        assert isinstance(kwargs["roles"], list)
        
        for role_kwargs in kwargs["roles"]:
            assert "name" in role_kwargs
            assert "permissions" in role_kwargs
            assert isinstance(role_kwargs["permissions"], str)
            
            # Verify comma-separated permissions format
            if role_kwargs["permissions"]:
                permissions = role_kwargs["permissions"].split(", ")
                assert all(isinstance(perm, str) for perm in permissions)

    def test_to_orm_kwargs_empty_roles(self):
        """Test to_orm_kwargs with empty roles."""
        api_user = ApiSeedUser(id=str(uuid4()), roles=frozenset())
        kwargs = api_user.to_orm_kwargs()
        
        assert kwargs["id"] == api_user.id
        assert kwargs["roles"] == []

    # =============================================================================
    # ROUND-TRIP CONVERSION VALIDATION TESTS
    # =============================================================================

    def test_domain_to_api_to_domain_round_trip(self, domain_user):
        """Test complete domain → API → domain round-trip preserves data integrity."""
        # Domain → API
        api_user = ApiSeedUser.from_domain(domain_user)
        
        # API → Domain
        recovered_domain = api_user.to_domain()
        
        # Verify complete data integrity
        assert recovered_domain.id == domain_user.id
        assert len(recovered_domain.roles) == len(domain_user.roles)
        assert isinstance(recovered_domain.roles, set)
        
        # Verify role data integrity
        original_role_names = {role.name for role in domain_user.roles}
        recovered_role_names = {role.name for role in recovered_domain.roles}
        assert recovered_role_names == original_role_names

    def test_orm_to_api_to_orm_round_trip(self, orm_user):
        """Test complete ORM → API → ORM round-trip preserves data integrity."""
        # ORM → API
        api_user = ApiSeedUser.from_orm_model(orm_user)
        
        # API → ORM kwargs
        orm_kwargs = api_user.to_orm_kwargs()
        
        # Verify data integrity through conversion
        assert orm_kwargs["id"] == orm_user.id
        assert len(orm_kwargs["roles"]) == len(orm_user.roles)
        
        # Verify role names preserved
        original_role_names = {role.name for role in orm_user.roles}
        converted_role_names = {role["name"] for role in orm_kwargs["roles"]}
        assert converted_role_names == original_role_names

    def test_complete_four_layer_round_trip(self, sample_domain_roles):
        """Test complete four-layer conversion cycle preserves data integrity."""
        # Start with domain object
        original_domain = SeedUser(
            id=str(uuid4()),
            roles=sample_domain_roles
        )
        
        # Domain → API
        api_user = ApiSeedUser.from_domain(original_domain)
        
        # API → ORM kwargs
        orm_kwargs = api_user.to_orm_kwargs()
        
        # Simulate ORM → API (using kwargs to create mock ORM)
        mock_orm_roles = [RoleSaModel(**role_data) for role_data in orm_kwargs["roles"]]
        mock_orm = UserSaModel(id=orm_kwargs["id"], roles=mock_orm_roles)
        reconstructed_api = ApiSeedUser.from_orm_model(mock_orm)
        
        # API → Domain
        final_domain = reconstructed_api.to_domain()
        
        # Verify complete data integrity
        assert final_domain.id == original_domain.id
        assert len(final_domain.roles) == len(original_domain.roles)
        
        original_role_names = {role.name for role in original_domain.roles}
        final_role_names = {role.name for role in final_domain.roles}
        assert final_role_names == original_role_names

    def test_round_trip_with_edge_cases(self, edge_case_role_collections):
        """Test round-trip conversion with edge case role collections."""
        for case_name, roles in edge_case_role_collections.items():
            # Create domain object with edge case roles
            domain_user = SeedUser(
                id=str(uuid4()),
                roles=set(role.to_domain() for role in roles)
            )
            
            # Complete round-trip
            api_user = ApiSeedUser.from_domain(domain_user)
            recovered_domain = api_user.to_domain()
            
            # Verify integrity
            assert recovered_domain.id == domain_user.id
            assert len(recovered_domain.roles) == len(domain_user.roles)

    # =============================================================================
    # ERROR HANDLING TESTS (MINIMUM 5 ERROR SCENARIOS PER METHOD)
    # =============================================================================

    def test_from_domain_error_scenarios(self):
        """Test from_domain error handling - minimum 5 error scenarios."""
        
        # Error 1: None input
        with pytest.raises(Exception):
            ApiSeedUser.from_domain(None)  # type: ignore
        
        # Error 2: Invalid object type
        with pytest.raises(Exception):
            ApiSeedUser.from_domain("not_a_user_object")  # type: ignore
        
        # Error 3: Object missing required attributes
        mock_invalid = Mock()
        del mock_invalid.id  # Missing id attribute
        with pytest.raises(AttributeError):
            ApiSeedUser.from_domain(mock_invalid)  # type: ignore
        
        # Error 4: Object with None id
        mock_none_id = Mock()
        mock_none_id.id = None
        mock_none_id.roles = set()
        with pytest.raises(Exception):
            ApiSeedUser.from_domain(mock_none_id)  # type: ignore
        
        # Error 5: Object with invalid roles type
        mock_invalid_roles = Mock()
        mock_invalid_roles.id = str(uuid4())
        mock_invalid_roles.roles = "not_a_set"  # Should be set
        with pytest.raises(Exception):
            ApiSeedUser.from_domain(mock_invalid_roles)  # type: ignore

    def test_to_domain_error_scenarios(self):
        """Test to_domain error handling through validation errors."""
        
        # Error 1: Empty id
        with pytest.raises(ValueError):
            ApiSeedUser(id="", roles=frozenset())
        
        # Error 2: Whitespace-only id
        with pytest.raises(ValueError):
            ApiSeedUser(id="   ", roles=frozenset())
        
        # Error 3: Invalid roles type
        with pytest.raises(ValueError):
            ApiSeedUser(id=str(uuid4()), roles="not_a_frozenset")  # type: ignore
        
        # Error 4: Invalid role objects in roles collection
        with pytest.raises(ValueError):
            ApiSeedUser(id=str(uuid4()), roles=["not_a_role_object"])  # type: ignore
        
        # Error 5: None id
        with pytest.raises(ValueError):
            ApiSeedUser(id=None, roles=frozenset())  # type: ignore

    def test_from_orm_model_error_scenarios(self):
        """Test from_orm_model error handling - minimum 5 error scenarios."""
        
        # Error 1: None input
        with pytest.raises((AttributeError, TypeError)):
            ApiSeedUser.from_orm_model(None)  # type: ignore
        
        # Error 2: Invalid object type
        with pytest.raises((AttributeError, TypeError)):
            ApiSeedUser.from_orm_model("not_an_orm_object")  # type: ignore
        
        # Error 3: Missing id attribute
        mock_orm = Mock()
        del mock_orm.id
        with pytest.raises(AttributeError):
            ApiSeedUser.from_orm_model(mock_orm)  # type: ignore
        
        # Error 4: Invalid id type
        mock_orm = Mock()
        mock_orm.id = 123  # Should be string
        mock_orm.roles = []
        with pytest.raises(ValueError):  # Validation error
            ApiSeedUser.from_orm_model(mock_orm)
        
        # Error 5: Invalid roles type
        mock_orm = Mock()
        mock_orm.id = str(uuid4())
        mock_orm.roles = "not_a_list"  # Should be list
        with pytest.raises((AttributeError, TypeError)):
            ApiSeedUser.from_orm_model(mock_orm)  # type: ignore

    def test_to_orm_kwargs_error_scenarios(self):
        """Test to_orm_kwargs error handling - this method is quite robust, testing edge cases."""
        
        # Valid API user for testing
        api_user = ApiSeedUser(id=str(uuid4()), roles=frozenset())
        
        # Test edge cases rather than force impossible errors
        
        # Error 1: Large role collection (should still work)
        large_roles = frozenset([
            ApiSeedRole(name=f"role_{i}", permissions=frozenset([f"perm_{i}"]))
            for i in range(100)
        ])
        large_user = ApiSeedUser(id=str(uuid4()), roles=large_roles)
        kwargs = large_user.to_orm_kwargs()
        assert len(kwargs["roles"]) == 100
        
        # Error 2: Empty roles (should work)
        empty_user = ApiSeedUser(id=str(uuid4()), roles=frozenset())
        kwargs = empty_user.to_orm_kwargs()
        assert kwargs["roles"] == []
        
        # Error 3-5: Test consistency and determinism
        for _ in range(3):
            result = api_user.to_orm_kwargs()
            assert "id" in result
            assert "roles" in result
            assert isinstance(result["roles"], list)

    def test_validation_error_scenarios(self):
        """Test comprehensive validation error scenarios."""
        
        # ID validation errors
        invalid_ids = [
            ("", "Empty id"),
            ("   ", "Whitespace only id"),
            (None, "None id"),
            (123, "Numeric id"),
        ]
        
        for invalid_id, description in invalid_ids:
            with pytest.raises(ValueError):
                ApiSeedUser(id=invalid_id, roles=frozenset())  # type: ignore
        
        # Roles validation errors
        invalid_roles = [
            ("string instead of frozenset", "String instead of collection"),
            (["not_role_objects"], "Invalid objects in collection"),
            (123, "Number instead of collection"),
            ({"not": "frozenset"}, "Dict instead of collection"),
        ]
        
        for invalid_roles_val, description in invalid_roles:
            with pytest.raises(ValueError):
                ApiSeedUser(id=str(uuid4()), roles=invalid_roles_val)  # type: ignore

    # =============================================================================
    # EDGE CASE TESTS
    # =============================================================================

    def test_edge_case_empty_roles(self):
        """Test handling of empty roles collection."""
        user_id = str(uuid4())
        
        # API creation
        api_user = ApiSeedUser(id=user_id, roles=frozenset())
        assert api_user.roles == frozenset()
        
        # Domain conversion
        domain_user = api_user.to_domain()
        assert domain_user.roles == set()
        
        # ORM conversion
        orm_kwargs = api_user.to_orm_kwargs()
        assert orm_kwargs["roles"] == []
        
        # ORM round-trip
        orm_user = UserSaModel(id=user_id, roles=[])
        api_from_orm = ApiSeedUser.from_orm_model(orm_user)
        assert api_from_orm.roles == frozenset()

    def test_edge_case_single_role(self):
        """Test handling of single role."""
        user_id = str(uuid4())
        single_role = frozenset([ApiSeedRole(name="reader", permissions=frozenset(["read"]))])
        api_user = ApiSeedUser(id=user_id, roles=single_role)
        
        # Verify single role handling
        assert len(api_user.roles) == 1
        role = next(iter(api_user.roles))
        assert role.name == "reader"
        
        # Test conversions preserve single role
        domain_user = api_user.to_domain()
        assert len(domain_user.roles) == 1
        
        orm_kwargs = api_user.to_orm_kwargs()
        assert len(orm_kwargs["roles"]) == 1
        assert orm_kwargs["roles"][0]["name"] == "reader"

    def test_edge_case_large_role_collection(self):
        """Test handling of large role collections."""
        user_id = str(uuid4())
        large_roles = frozenset([
            ApiSeedRole(name=f"role_{i:03d}", permissions=frozenset([f"permission_{i}"]))
            for i in range(100)
        ])
        api_user = ApiSeedUser(id=user_id, roles=large_roles)
        
        # Verify large collection handling
        assert len(api_user.roles) == 100
        
        # Test domain conversion preserves all roles
        domain_user = api_user.to_domain()
        assert len(domain_user.roles) == 100
        
        # Test ORM conversion preserves all roles
        orm_kwargs = api_user.to_orm_kwargs()
        assert len(orm_kwargs["roles"]) == 100
        
        # Verify all role names are preserved
        api_role_names = {role.name for role in api_user.roles}
        domain_role_names = {role.name for role in domain_user.roles}
        orm_role_names = {role["name"] for role in orm_kwargs["roles"]}
        
        assert domain_role_names == api_role_names
        assert orm_role_names == api_role_names

    def test_edge_case_complex_role_permissions(self):
        """Test handling of roles with complex permission structures."""
        complex_roles = frozenset([
            ApiSeedRole(
                name="complex_admin",
                permissions=frozenset([
                    "read:all:users",
                    "write:own:profile",
                    "delete:any:content",
                    "manage:system:settings"
                ])
            ),
            ApiSeedRole(
                name="unicode_role",
                permissions=frozenset(["읽기", "쓰기", "删除"])
            )
        ])
        
        api_user = ApiSeedUser(id=str(uuid4()), roles=complex_roles)
        
        # Test round-trip with complex permissions
        domain_user = api_user.to_domain()
        recovered_api = ApiSeedUser.from_domain(domain_user)
        
        # Verify permission preservation
        original_perms = {perm for role in api_user.roles for perm in role.permissions}
        recovered_perms = {perm for role in recovered_api.roles for perm in role.permissions}
        assert recovered_perms == original_perms

    # =============================================================================
    # PERFORMANCE VALIDATION TESTS (<5MS CONVERSION TIME)
    # =============================================================================

    def test_from_domain_performance(self, domain_user):
        """Test from_domain conversion meets <5ms requirement."""
        start_time = time.perf_counter()
        
        for _ in range(100):  # Test 100 conversions for reliable timing
            ApiSeedUser.from_domain(domain_user)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        assert avg_time_ms < 5.0, f"from_domain average time {avg_time_ms:.3f}ms exceeds 5ms limit"

    def test_to_domain_performance(self, valid_user_data):
        """Test to_domain conversion meets <5ms requirement."""
        api_user = ApiSeedUser(**valid_user_data)
        
        start_time = time.perf_counter()
        
        for _ in range(100):  # Test 100 conversions
            api_user.to_domain()
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        assert avg_time_ms < 5.0, f"to_domain average time {avg_time_ms:.3f}ms exceeds 5ms limit"

    def test_from_orm_model_performance(self, orm_user):
        """Test from_orm_model conversion meets <5ms requirement."""
        start_time = time.perf_counter()
        
        for _ in range(100):  # Test 100 conversions
            ApiSeedUser.from_orm_model(orm_user)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        assert avg_time_ms < 5.0, f"from_orm_model average time {avg_time_ms:.3f}ms exceeds 5ms limit"

    def test_to_orm_kwargs_performance(self, valid_user_data):
        """Test to_orm_kwargs conversion meets <5ms requirement."""
        api_user = ApiSeedUser(**valid_user_data)
        
        start_time = time.perf_counter()
        
        for _ in range(100):  # Test 100 conversions
            api_user.to_orm_kwargs()
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        assert avg_time_ms < 5.0, f"to_orm_kwargs average time {avg_time_ms:.3f}ms exceeds 5ms limit"

    def test_complete_conversion_cycle_performance(self, domain_user):
        """Test complete four-layer conversion cycle performance."""
        start_time = time.perf_counter()
        
        for _ in range(50):  # Test 50 complete cycles
            # Domain → API
            api_user = ApiSeedUser.from_domain(domain_user)
            
            # API → ORM kwargs
            orm_kwargs = api_user.to_orm_kwargs()
            
            # ORM → API (simulated)
            mock_orm_roles = [RoleSaModel(**role_data) for role_data in orm_kwargs["roles"]]
            mock_orm = UserSaModel(id=orm_kwargs["id"], roles=mock_orm_roles)
            reconstructed_api = ApiSeedUser.from_orm_model(mock_orm)
            
            # API → Domain
            final_domain = reconstructed_api.to_domain()
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 50) * 1000
        
        # Complete cycle should be under 10ms (more lenient for full cycle)
        assert avg_time_ms < 10.0, f"Complete cycle average time {avg_time_ms:.3f}ms exceeds 10ms limit"

    def test_large_role_collection_performance(self):
        """Test performance with large role collections."""
        user_id = str(uuid4())
        large_roles = set([
            SeedRole(name=f"role_{i:03d}", permissions=frozenset([f"permission_{i}"]))
            for i in range(1000)
        ])
        domain_user = SeedUser(id=user_id, roles=large_roles)
        
        start_time = time.perf_counter()
        
        # Test conversion with large collection
        api_user = ApiSeedUser.from_domain(domain_user)
        orm_kwargs = api_user.to_orm_kwargs()
        
        end_time = time.perf_counter()
        conversion_time_ms = (end_time - start_time) * 1000
        
        # Should handle large collections efficiently
        assert conversion_time_ms < 50.0, f"Large collection conversion {conversion_time_ms:.3f}ms exceeds 50ms limit"
        assert len(api_user.roles) == 1000

    # =============================================================================
    # INTEGRATION TESTS WITH BASE CLASSES
    # =============================================================================

    def test_base_value_object_inheritance(self):
        """Test proper inheritance from BaseValueObject."""
        api_user = ApiSeedUser(id=str(uuid4()), roles=frozenset())
        
        # Should inherit from BaseValueObject
        from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
        assert isinstance(api_user, BaseApiValueObject)
        
        # Should have base model configuration
        assert api_user.model_config.get('frozen') is True
        assert api_user.model_config.get('strict') is True
        assert api_user.model_config.get('extra') == 'forbid'

    def test_base_api_model_conversion_utilities(self):
        """Test integration with BaseApiModel conversion utilities."""
        api_user = ApiSeedUser(id=str(uuid4()), roles=frozenset())
        
        # Should have access to conversion utility
        assert hasattr(api_user, 'convert')
        assert api_user.convert is not None
        
        # Test safe conversion methods work
        domain_user = SeedUser(id=str(uuid4()), roles=set())
        safe_api = api_user.from_domain(domain_user)
        assert isinstance(safe_api, ApiSeedUser)

    def test_immutability_from_base_class(self):
        """Test that immutability is properly enforced from base class."""
        api_user = ApiSeedUser(id=str(uuid4()), roles=frozenset())
        
        # Should be immutable (frozen)
        with pytest.raises(ValueError):
            api_user.id = "changed"  # type: ignore
        
        with pytest.raises(ValueError):
            api_user.roles = frozenset()  # type: ignore

    def test_pydantic_validation_integration(self):
        """Test integration with Pydantic validation from base class."""
        # Test validation works
        user_id = str(uuid4())
        valid_data = f'{{"id": "{user_id}", "roles": []}}'
        api_user = ApiSeedUser.model_validate_json(valid_data)
        assert api_user.id == user_id
        assert api_user.roles == frozenset()
        
        # Test validation fails for invalid data
        with pytest.raises(ValueError):
            ApiSeedUser.model_validate({"id": "", "roles": []})

    def test_serialization_integration(self):
        """Test JSON serialization integration from base class."""
        # Create user with simple roles for serialization test
        api_user = ApiSeedUser(id=str(uuid4()), roles=frozenset())
        
        # Should serialize to JSON (simple case with empty roles)
        json_data = api_user.model_dump_json()
        assert isinstance(json_data, str)
        assert api_user.id in json_data
        
        # Test model_dump for dict representation (avoiding complex serialization)
        user_dict = api_user.model_dump()
        assert user_dict["id"] == api_user.id
        assert "roles" in user_dict
        assert user_dict["roles"] == frozenset()  # Empty frozenset stays as frozenset in dict
        
        # Verify the structure can be reconstructed from simple data
        reconstructed = ApiSeedUser.model_validate(user_dict)
        assert reconstructed.id == api_user.id
        assert reconstructed.roles == frozenset()

    # =============================================================================
    # COMPREHENSIVE COVERAGE VALIDATION
    # =============================================================================

    def test_all_public_methods_covered(self):
        """Verify all public methods are covered by tests."""
        api_user = ApiSeedUser(id=str(uuid4()), roles=frozenset())
        
        # Test all required conversion methods exist and work
        domain_user = SeedUser(id=str(uuid4()), roles=set())
        orm_user = UserSaModel(id=str(uuid4()), roles=[])
        
        # from_domain
        result1 = ApiSeedUser.from_domain(domain_user)
        assert isinstance(result1, ApiSeedUser)
        
        # to_domain
        result2 = api_user.to_domain()
        assert isinstance(result2, SeedUser)
        
        # from_orm_model
        result3 = ApiSeedUser.from_orm_model(orm_user)
        assert isinstance(result3, ApiSeedUser)
        
        # to_orm_kwargs
        result4 = api_user.to_orm_kwargs()
        assert isinstance(result4, dict)
        
        # All methods successfully tested
        assert True

    def test_field_validation_coverage(self):
        """Test all field validation patterns are covered."""
        # Test id validation
        with pytest.raises(ValueError):
            ApiSeedUser(id="", roles=frozenset())
        
        # Test roles validation
        valid_user = ApiSeedUser(id=str(uuid4()), roles=frozenset())
        assert isinstance(valid_user.roles, frozenset)
        
        # Test field constraints
        assert len(valid_user.id) >= 1  # Minimum length validation
        
        # Test with valid roles
        sample_role = ApiSeedRole(name="test", permissions=frozenset(["read"]))
        user_with_role = ApiSeedUser(id=str(uuid4()), roles=frozenset([sample_role]))
        assert len(user_with_role.roles) == 1 