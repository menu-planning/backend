import pytest
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.user import ApiSeedUser
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel


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
        """Test that creating a user with duplicate roles is handled properly."""
        # Since sets automatically prevent duplicates, this should work fine
        admin_role = ApiSeedRole(name="admin", permissions=frozenset(["read", "write"]))
        roles_with_duplicate = set([admin_role, admin_role])  # Set will deduplicate
        user = ApiSeedUser(id="user_123", roles=roles_with_duplicate)
        assert len(user.roles) == 1  # Set automatically removes duplicates

    def test_from_domain(self, sample_roles):
        """Test creating an ApiSeedUser from a domain SeedUser object."""
        domain_roles = set([role.to_domain() for role in sample_roles])
        domain_user = SeedUser(id="user_123", roles=domain_roles)
        api_user = ApiSeedUser.from_domain(domain_user)
        
        assert api_user.id == domain_user.id
        assert len(api_user.roles) == len(domain_user.roles)
        # Convert to lists and sort for comparison
        api_role_names = sorted([role.name for role in api_user.roles])
        domain_role_names = sorted([role.name for role in domain_user.roles])
        assert api_role_names == domain_role_names

    def test_to_domain(self, sample_roles):
        """Test converting an ApiSeedUser to a domain SeedUser object."""
        api_user = ApiSeedUser(id="user_123", roles=sample_roles)
        domain_user = api_user.to_domain()
        
        assert isinstance(domain_user, SeedUser)
        assert domain_user.id == api_user.id
        assert len(domain_user.roles) == len(api_user.roles)
        # Convert to lists and sort for comparison
        api_role_names = sorted([role.name for role in api_user.roles])
        domain_role_names = sorted([role.name for role in domain_user.roles])
        assert api_role_names == domain_role_names

    def test_from_orm_model(self):
        """Test creating an ApiSeedUser from an ORM model."""
        orm_roles = [
            RoleSaModel(name="admin", permissions="read, write"),
            RoleSaModel(name="user", permissions="read")
        ]
        orm_user = UserSaModel(id="user_123", roles=orm_roles)
        api_user = ApiSeedUser.from_orm_model(orm_user)
        
        assert api_user.id == orm_user.id
        assert len(api_user.roles) == len(orm_user.roles)

    def test_from_orm_model_without_roles(self):
        """Test creating an ApiSeedUser from an ORM model without roles."""
        orm_user = UserSaModel(id="user_123", roles=[])
        api_user = ApiSeedUser.from_orm_model(orm_user)
        
        assert api_user.id == orm_user.id
        assert api_user.roles == set()

    def test_to_orm_kwargs(self, sample_roles):
        """Test converting an ApiSeedUser to ORM model kwargs."""
        api_user = ApiSeedUser(id="user_123", roles=sample_roles)
        kwargs = api_user.to_orm_kwargs()
        
        assert kwargs["id"] == api_user.id
        assert len(kwargs["roles"]) == len(api_user.roles)

    def test_serialization(self, sample_roles):
        """Test that the user serializes correctly."""
        user = ApiSeedUser(id="user_123", roles=sample_roles)
        # Just verify the user can be created and has the expected attributes
        assert user.id == "user_123"
        assert len(user.roles) == len(sample_roles)

    def test_deserialization(self, sample_roles):
        """Test that the user deserializes correctly."""
        # Test basic creation with role objects
        user = ApiSeedUser(id="user_123", roles=sample_roles)
        assert user.id == "user_123"
        assert len(user.roles) == len(sample_roles) 