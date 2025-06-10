import pytest
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_mode import RoleSaModel


class TestApiSeedRole:
    """Test suite for ApiSeedRole schema."""

    @pytest.mark.parametrize("name,permissions", [
        ("admin", frozenset(["read", "write", "delete"])),
        ("user", frozenset(["read"])),
        ("guest", frozenset()),
    ])
    def test_create_valid_role(self, name: str, permissions: frozenset[str]):
        """Test creating valid roles with different combinations of values."""
        role = ApiSeedRole(name=name, permissions=permissions)
        assert role.name == name
        assert role.permissions == permissions

    def test_create_with_invalid_name_raises_error(self):
        """Test that creating a role with an invalid name raises ValueError."""
        with pytest.raises(ValueError):
            ApiSeedRole(name="Admin", permissions=frozenset(["read"]))  # Uppercase not allowed

        with pytest.raises(ValueError):
            ApiSeedRole(name="admin@role", permissions=frozenset(["read"]))  # @ symbol not allowed

    def test_create_with_duplicate_permissions_raises_error(self):
        """Test that creating a role with duplicate permissions in a list is handled properly."""
        # When passed as a list with duplicates, it should be converted to frozenset without duplicates
        role = ApiSeedRole(name="admin", permissions=frozenset(["read", "read"]))
        assert role.permissions == frozenset(["read"])

    def test_from_domain(self):
        """Test creating an ApiSeedRole from a domain SeedRole object."""
        domain_role = SeedRole(name="admin", permissions=frozenset(["read", "write"]))
        api_role = ApiSeedRole.from_domain(domain_role)
        
        assert api_role.name == domain_role.name
        assert api_role.permissions == frozenset(domain_role.permissions)

    def test_to_domain(self):
        """Test converting an ApiSeedRole to a domain SeedRole object."""
        api_role = ApiSeedRole(name="admin", permissions=frozenset(["read", "write"]))
        domain_role = api_role.to_domain()
        
        assert isinstance(domain_role, SeedRole)
        assert domain_role.name == api_role.name
        assert domain_role.permissions == set(api_role.permissions)

    def test_from_orm_model(self):
        """Test creating an ApiSeedRole from an ORM model."""
        orm_model = RoleSaModel(name="admin", permissions="read, write")
        api_role = ApiSeedRole.from_orm_model(orm_model)
        
        assert api_role.name == orm_model.name
        assert api_role.permissions == frozenset(["read", "write"])

    def test_from_orm_model_with_empty_permissions(self):
        """Test creating an ApiSeedRole from an ORM model with empty permissions."""
        orm_model = RoleSaModel(name="guest", permissions="")
        api_role = ApiSeedRole.from_orm_model(orm_model)
        
        assert api_role.name == orm_model.name
        assert api_role.permissions == frozenset()

    def test_to_orm_kwargs(self):
        """Test converting an ApiSeedRole to ORM model kwargs."""
        api_role = ApiSeedRole(name="admin", permissions=frozenset(["read", "write"]))
        kwargs = api_role.to_orm_kwargs()
        
        assert kwargs["name"] == api_role.name
        assert kwargs["permissions"] == "read, write"

    def test_to_orm_kwargs_with_empty_permissions(self):
        """Test converting an ApiSeedRole with empty permissions to ORM model kwargs."""
        api_role = ApiSeedRole(name="guest", permissions=frozenset())
        kwargs = api_role.to_orm_kwargs()
        
        assert kwargs["name"] == api_role.name
        assert kwargs["permissions"] == ""

    def test_immutability(self):
        """Test that the role is immutable after creation."""
        role = ApiSeedRole(name="admin", permissions=frozenset(["read"]))
        with pytest.raises(ValueError):
            role.name = "new_admin"

    def test_serialization(self):
        """Test that the role serializes correctly."""
        role = ApiSeedRole(name="admin", permissions=frozenset(["read", "write"]))
        serialized = role.model_dump()
        
        assert serialized["name"] == role.name
        assert serialized["permissions"] == role.permissions

    def test_deserialization(self):
        """Test that the role deserializes correctly."""
        data = {
            "name": "admin",
            "permissions": ["read", "write"]
        }
        role = ApiSeedRole.model_validate(data)
        
        assert role.name == data["name"]
        assert role.permissions == frozenset(data["permissions"]) 