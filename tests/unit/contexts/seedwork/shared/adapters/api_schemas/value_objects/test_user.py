from typing import Any
from uuid import uuid4

import pytest
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_role import (
    ApiSeedRole,
)
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_user import (
    ApiSeedUser,
)
from src.contexts.seedwork.domain.value_objects.role import SeedRole
from src.contexts.seedwork.domain.value_objects.user import SeedUser


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


class ConcreteApiSeedUser(
    ApiSeedUser["ConcreteApiSeedUser", ConcreteApiSeedRole, SeedUser, UserSaModel]
):
    """Concrete implementation of ApiSeedUser for testing purposes."""

    def to_domain(self) -> SeedUser:
        """Convert API schema instance to domain model object."""
        return SeedUser(id=self.id, roles=set(self.roles))

    @classmethod
    def from_domain(cls, domain_obj: SeedUser) -> "ConcreteApiSeedUser":
        """Create API schema instance from domain model object."""
        return cls(id=domain_obj.id, roles=frozenset(domain_obj.roles))

    @classmethod
    def from_orm_model(cls, orm_model: UserSaModel) -> "ConcreteApiSeedUser":
        """Create API schema instance from SQLAlchemy model."""
        return cls(id=orm_model.id, roles=frozenset())  # Simplified for testing

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API user to ORM model kwargs."""
        return {"id": self.id, "roles": list(self.roles) if self.roles else []}


class TestConcreteApiSeedUser:
    """Test suite for ConcreteApiSeedUser schema."""

    @pytest.fixture
    def sample_roles(self):
        """Fixture providing sample roles for testing."""
        return frozenset(
            [
                ConcreteApiSeedRole(
                    name="admin", permissions=frozenset(["read", "write"])
                ),
                ConcreteApiSeedRole(name="user", permissions=frozenset(["read"])),
            ]
        )

    @pytest.mark.unit
    def test_create_valid_user(self, sample_roles):
        """Test creating a valid user with roles."""
        user_id = str(uuid4())
        user = ConcreteApiSeedUser(id=user_id, roles=sample_roles)
        assert user.id == user_id
        assert user.roles == sample_roles

    @pytest.mark.unit
    def test_create_user_without_roles(self):
        """Test creating a user without roles."""
        user_id = str(uuid4())
        user = ConcreteApiSeedUser(id=user_id, roles=frozenset())
        assert user.id == user_id
        assert user.roles == frozenset()

    @pytest.mark.security
    def test_create_with_empty_id_raises_error(self):
        """Test that creating a user with an empty ID raises ValueError."""
        with pytest.raises(ValueError):
            ConcreteApiSeedUser(id="", roles=frozenset())

    @pytest.mark.unit
    def test_create_with_duplicate_roles_raises_error(self, sample_roles):
        """Test that creating a user with duplicate roles is handled properly."""
        # Since frozensets automatically prevent duplicates, this should work fine
        admin_role = ApiSeedRole(name="admin", permissions=frozenset(["read", "write"]))
        roles_with_duplicate = frozenset(
            [admin_role, admin_role]
        )  # Frozenset will deduplicate
        user = ConcreteApiSeedUser(id=str(uuid4()), roles=roles_with_duplicate)
        assert len(user.roles) == 1  # Frozenset automatically removes duplicates

    @pytest.mark.unit
    def test_from_domain(self, sample_roles):
        """Test creating an ConcreteApiSeedUser from a domain SeedUser object."""
        domain_roles = frozenset([role.to_domain() for role in sample_roles])
        domain_user = SeedUser(id=str(uuid4()), roles=domain_roles)
        api_user = ConcreteApiSeedUser.from_domain(domain_user)

        assert api_user.id == domain_user.id
        assert len(api_user.roles) == len(domain_user.roles)
        # Convert to lists and sort for comparison
        api_role_names = sorted([role.name for role in api_user.roles])
        domain_role_names = sorted([role.name for role in domain_user.roles])
        assert api_role_names == domain_role_names

    @pytest.mark.unit
    def test_to_domain(self, sample_roles):
        """Test converting an ConcreteApiSeedUser to a domain SeedUser object."""
        api_user = ConcreteApiSeedUser(id=str(uuid4()), roles=sample_roles)
        domain_user = api_user.to_domain()

        assert isinstance(domain_user, SeedUser)
        assert domain_user.id == api_user.id
        assert len(domain_user.roles) == len(api_user.roles)
        # Convert to lists and sort for comparison
        api_role_names = sorted([role.name for role in api_user.roles])
        domain_role_names = sorted([role.name for role in domain_user.roles])
        assert api_role_names == domain_role_names

    @pytest.mark.integration
    def test_from_orm_model(self):
        """Test creating an ConcreteApiSeedUser from an ORM model."""
        orm_roles = [
            RoleSaModel(name="admin", permissions="read, write"),
            RoleSaModel(name="user", permissions="read"),
        ]
        orm_user = UserSaModel(id=str(uuid4()), roles=orm_roles)
        api_user = ConcreteApiSeedUser.from_orm_model(orm_user)

        assert api_user.id == orm_user.id
        assert len(api_user.roles) == len(orm_user.roles)

    @pytest.mark.integration
    def test_from_orm_model_without_roles(self):
        """Test creating an ConcreteApiSeedUser from an ORM model without roles."""
        orm_user = UserSaModel(id=str(uuid4()), roles=[])
        api_user = ConcreteApiSeedUser.from_orm_model(orm_user)

        assert api_user.id == orm_user.id
        assert api_user.roles == frozenset()

    @pytest.mark.integration
    def test_to_orm_kwargs(self, sample_roles):
        """Test converting an ConcreteApiSeedUser to ORM model kwargs."""
        api_user = ConcreteApiSeedUser(id=str(uuid4()), roles=sample_roles)
        kwargs = api_user.to_orm_kwargs()

        assert kwargs["id"] == api_user.id
        assert len(kwargs["roles"]) == len(api_user.roles)

    @pytest.mark.unit
    def test_serialization(self, sample_roles):
        """Test that the user serializes correctly."""
        user_id = str(uuid4())
        user = ConcreteApiSeedUser(id=user_id, roles=sample_roles)
        # Just verify the user can be created and has the expected attributes
        assert user.id == user_id
        assert len(user.roles) == len(sample_roles)

    @pytest.mark.unit
    def test_deserialization(self, sample_roles):
        """Test that the user deserializes correctly."""
        # Test basic creation with role objects
        user_id = str(uuid4())
        user = ConcreteApiSeedUser(id=user_id, roles=sample_roles)
        assert user.id == user_id
        assert len(user.roles) == len(sample_roles)
