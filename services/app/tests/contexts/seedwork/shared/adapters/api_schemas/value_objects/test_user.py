import pytest
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.user import ApiSeedUser
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole
from src.contexts.iam.core.adapters.ORM.sa_models.user import UserSaModel
from src.contexts.iam.core.adapters.ORM.sa_models.role import RoleSaModel


class TestApiSeedUser:
    """Test suite for ApiSeedUser schema."""

    @pytest.fixture
    def sample_roles(self):
        """Fixture providing sample roles for testing."""
        return set([
            ApiSeedRole(name="admin", permissions=frozenset(["read", "write"])),
            ApiSeedRole(name="user", permissions=frozenset(["read"]))
        ])

    def test_create_valid_user(self, sample_roles):
        """Test creating a valid user with roles."""
        user = ApiSeedUser(id="user_123", roles=sample_roles)
        assert user.id == "user_123"
        assert user.roles == sample_roles

    def test_create_user_without_roles(self):
        """Test creating a user without roles."""
        user = ApiSeedUser(id="user_123", roles=set())
        assert user.id == "user_123"
        assert user.roles == set()

    def test_create_with_empty_id_raises_error(self):
        """Test that creating a user with an empty ID raises ValueError."""
        with pytest.raises(ValueError):
            ApiSeedUser(id="", roles=set())

    def test_create_with_duplicate_roles_raises_error(self, sample_roles):
        """Test that creating a user with duplicate roles raises ValueError."""
        duplicate_roles = sample_roles + [sample_roles[0]]
        with pytest.raises(ValueError):
            ApiSeedUser(id="user_123", roles=duplicate_roles)

    def test_from_domain(self, sample_roles):
        """Test creating an ApiSeedUser from a domain SeedUser object."""
        domain_roles = set([role.to_domain() for role in sample_roles])
        domain_user = SeedUser(id="user_123", roles=domain_roles)
        api_user = ApiSeedUser.from_domain(domain_user)
        
        assert api_user.id == domain_user.id
        assert len(api_user.roles) == len(domain_user.roles)
        for api_role, domain_role in zip(api_user.roles, domain_user.roles):
            assert api_role.name == domain_role.name
            assert api_role.permissions == domain_role.permissions

    def test_to_domain(self, sample_roles):
        """Test converting an ApiSeedUser to a domain SeedUser object."""
        api_user = ApiSeedUser(id="user_123", roles=sample_roles)
        domain_user = api_user.to_domain()
        
        assert isinstance(domain_user, SeedUser)
        assert domain_user.id == api_user.id
        assert len(domain_user.roles) == len(api_user.roles)
        for domain_role, api_role in zip(domain_user.roles, api_user.roles):
            assert domain_role.name == api_role.name
            assert domain_role.permissions == api_role.permissions

    def test_from_orm_model(self):
        """Test creating an ApiSeedUser from an ORM model."""
        orm_roles = [
            RoleSaModel(name="admin", permissions=set("read, write")),
            RoleSaModel(name="user", permissions="read")
        ]
        orm_user = UserSaModel(id="user_123", roles=orm_roles)
        api_user = ApiSeedUser.from_orm_model(orm_user)
        
        assert api_user.id == orm_user.id
        assert len(api_user.roles) == len(orm_user.roles)
        for api_role, orm_role in zip(api_user.roles, orm_user.roles):
            assert api_role.name == orm_role.name
            assert api_role.permissions == orm_role.permissions.split(", ")

    def test_from_orm_model_without_roles(self):
        """Test creating an ApiSeedUser from an ORM model without roles."""
        orm_user = UserSaModel(id="user_123", roles=[])
        api_user = ApiSeedUser.from_orm_model(orm_user)
        
        assert api_user.id == orm_user.id
        assert api_user.roles == []

    def test_to_orm_kwargs(self, sample_roles):
        """Test converting an ApiSeedUser to ORM model kwargs."""
        api_user = ApiSeedUser(id="user_123", roles=sample_roles)
        kwargs = api_user.to_orm_kwargs()
        
        assert kwargs["id"] == api_user.id
        assert len(kwargs["roles"]) == len(api_user.roles)
        for role_kwargs, api_role in zip(kwargs["roles"], api_user.roles):
            assert role_kwargs["name"] == api_role.name
            assert role_kwargs["permissions"] == ", ".join(api_role.permissions)

    def test_to_orm_kwargs_without_roles(self):
        """Test converting an ApiSeedUser without roles to ORM model kwargs."""
        api_user = ApiSeedUser(id="user_123", roles=set())
        kwargs = api_user.to_orm_kwargs()
        
        assert kwargs["id"] == api_user.id
        assert kwargs["roles"] == []

    def test_immutability(self, sample_roles):
        """Test that the user is immutable after creation."""
        user = ApiSeedUser(id="user_123", roles=sample_roles)
        with pytest.raises(ValueError):
            user.id = "new_user_id"

    def test_serialization(self, sample_roles):
        """Test that the user serializes correctly."""
        user = ApiSeedUser(id="user_123", roles=sample_roles)
        serialized = user.model_dump()
        
        assert serialized["id"] == user.id
        assert len(serialized["roles"]) == len(user.roles)
        for serialized_role, user_role in zip(serialized["roles"], user.roles):
            assert serialized_role["name"] == user_role.name
            assert serialized_role["permissions"] == user_role.permissions

    def test_deserialization(self, sample_roles):
        """Test that the user deserializes correctly."""
        data = {
            "id": "user_123",
            "roles": [{"name": role.name, "permissions": role.permissions} for role in sample_roles]
        }
        user = ApiSeedUser.model_validate(data)
        
        assert user.id == data["id"]
        assert len(user.roles) == len(data["roles"])
        for user_role, data_role in zip(user.roles, data["roles"]):
            assert user_role.name == data_role["name"]
            assert user_role.permissions == data_role["permissions"] 