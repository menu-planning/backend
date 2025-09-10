import json
from typing import Any

import pytest
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_role import (
    ApiSeedRole,
)
from src.contexts.seedwork.domain.value_objects.role import SeedRole


class ConcreteApiSeedRole(ApiSeedRole["ConcreteApiSeedRole", SeedRole, RoleSaModel]):
    """Concrete implementation of ApiSeedRole for testing purposes."""

    def to_domain(self) -> SeedRole:
        """Convert API schema instance to domain model object."""
        return SeedRole(name=self.name, permissions=set(self.permissions))

    @classmethod
    def from_domain(cls, domain_obj: SeedRole) -> "ConcreteApiSeedRole":
        """Create API schema instance from domain model object."""
        return cls(name=domain_obj.name, permissions=frozenset(domain_obj.permissions))

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ConcreteApiSeedRole":
        """Create API schema instance from SQLAlchemy model."""
        return cls(
            name=orm_model.name,
            permissions=(
                frozenset(
                    perm.strip()
                    for perm in orm_model.permissions.split(", ")
                    if perm.strip()
                )
                if orm_model.permissions
                else frozenset()
            ),
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API role to ORM model kwargs."""
        return {
            "name": self.name,
            "permissions": (
                ", ".join(sorted(self.permissions)) if self.permissions else ""
            ),
        }


class TestConcreteApiSeedRole:
    """Test suite for ConcreteApiSeedRole schema."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "name,permissions",
        [
            ("admin", frozenset(["read", "write", "delete"])),
            ("user", frozenset(["read"])),
            ("guest", frozenset()),
        ],
    )
    def test_create_valid_role(self, name: str, permissions: frozenset[str]):
        """Test creating valid roles with different combinations of values."""
        role = ConcreteApiSeedRole(name=name, permissions=permissions)
        assert role.name == name
        assert role.permissions == permissions

    @pytest.mark.security
    def test_create_with_invalid_name_raises_error(self):
        """Test that creating a role with an invalid name raises ValueError."""
        with pytest.raises(ValueError):
            ConcreteApiSeedRole(
                name="Admin", permissions=frozenset(["read"])
            )  # Uppercase not allowed

        with pytest.raises(ValueError):
            ConcreteApiSeedRole(
                name="admin@role", permissions=frozenset(["read"])
            )  # @ symbol not allowed

    @pytest.mark.unit
    def test_create_with_duplicate_permissions_raises_error(self):
        """Test that creating a role with duplicate permissions in a list is handled properly."""
        # When passed as a list with duplicates, it should be converted to frozenset without duplicates
        role = ConcreteApiSeedRole(
            name="admin", permissions=frozenset(["read", "read"])
        )
        assert role.permissions == frozenset(["read"])

    @pytest.mark.unit
    def test_from_domain(self):
        """Test creating an ConcreteApiSeedRole from a domain SeedRole object."""
        domain_role = SeedRole(name="admin", permissions=frozenset(["read", "write"]))
        api_role = ConcreteApiSeedRole.from_domain(domain_role)

        assert api_role.name == domain_role.name
        assert api_role.permissions == frozenset(domain_role.permissions)

    @pytest.mark.unit
    def test_to_domain(self):
        """Test converting an ConcreteApiSeedRole to a domain SeedRole object."""
        api_role = ConcreteApiSeedRole(
            name="admin", permissions=frozenset(["read", "write"])
        )
        domain_role = api_role.to_domain()

        assert isinstance(domain_role, SeedRole)
        assert domain_role.name == api_role.name
        assert domain_role.permissions == set(api_role.permissions)

    @pytest.mark.integration
    def test_from_orm_model(self):
        """Test creating an ConcreteApiSeedRole from an ORM model."""
        orm_model = RoleSaModel(name="admin", permissions="read, write")
        api_role = ConcreteApiSeedRole.from_orm_model(orm_model)

        assert api_role.name == orm_model.name
        assert api_role.permissions == frozenset(["read", "write"])

    @pytest.mark.integration
    def test_from_orm_model_with_empty_permissions(self):
        """Test creating an ConcreteApiSeedRole from an ORM model with empty permissions."""
        orm_model = RoleSaModel(name="guest", permissions="")
        api_role = ConcreteApiSeedRole.from_orm_model(orm_model)

        assert api_role.name == orm_model.name
        assert api_role.permissions == frozenset()

    @pytest.mark.integration
    def test_to_orm_kwargs(self):
        """Test converting an ConcreteApiSeedRole to ORM model kwargs."""
        api_role = ConcreteApiSeedRole(
            name="admin", permissions=frozenset(["read", "write"])
        )
        kwargs = api_role.to_orm_kwargs()

        assert kwargs["name"] == api_role.name
        assert kwargs["permissions"] == "read, write"

    @pytest.mark.integration
    def test_to_orm_kwargs_with_empty_permissions(self):
        """Test converting an ConcreteApiSeedRole with empty permissions to ORM model kwargs."""
        api_role = ConcreteApiSeedRole(name="guest", permissions=frozenset())
        kwargs = api_role.to_orm_kwargs()

        assert kwargs["name"] == api_role.name
        assert kwargs["permissions"] == ""

    @pytest.mark.unit
    def test_immutability(self):
        """Test that the role is immutable after creation."""
        role = ConcreteApiSeedRole(name="admin", permissions=frozenset(["read"]))
        with pytest.raises(ValueError):
            role.name = "new_admin"

    @pytest.mark.unit
    def test_serialization(self):
        """Test that the role serializes correctly."""
        data = {"name": "admin", "permissions": frozenset(["read", "write"])}
        role = ConcreteApiSeedRole(**data)
        serialized = role.model_dump_json()

        assert serialized == '{"name":"admin","permissions":["read","write"]}'

    @pytest.mark.unit
    def test_deserialization(self):
        """Test that the role deserializes correctly."""
        data = {"name": "admin", "permissions": ["read", "write"]}
        json_data = json.dumps(data)
        role = ConcreteApiSeedRole.model_validate_json(json_data)

        assert role.name == data["name"]
        assert role.permissions == frozenset(data["permissions"])
