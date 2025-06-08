import pytest
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.api_user import ApiUser
from src.contexts.recipes_catalog.core.domain.value_objects.user import User
from src.contexts.iam.core.adapters.ORM.sa_models.user import UserSaModel
from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.api_role import ApiRole
from src.contexts.recipes_catalog.core.domain.value_objects.role import Role


@pytest.fixture
def valid_user_data():
    """Fixture providing valid user data for testing."""
    return {
        "id": str(uuid4()),
        "roles": set([
            ApiRole(name="user", permissions=frozenset(["read"])),
            ApiRole(name="recipe_manager", permissions=frozenset(["read", "write"])),
        ]),
    }


@pytest.fixture
def valid_user_domain(valid_user_data):
    """Fixture creating a valid User domain object."""
    return User(
        id=valid_user_data["id"],
        roles=set([Role(name=role.name, permissions=role.permissions) for role in valid_user_data["roles"]]),
    )


@pytest.fixture
def valid_user_orm(valid_user_data):
    """Fixture creating a valid UserSaModel ORM object."""
    return UserSaModel(
        id=valid_user_data["id"],
        roles=[{"name": role.name, "permissions": ", ".join(role.permissions)} for role in valid_user_data["roles"]],
    )


class TestApiUser:
    """Test suite for ApiUser schema."""

    def test_create_with_valid_data(self, valid_user_data):
        """Test creating an ApiUser with valid data."""
        user = ApiUser(**valid_user_data)
        assert user.id == valid_user_data["id"]
        assert len(user.roles) == len(valid_user_data["roles"])
        assert user.roles == valid_user_data["roles"]

    @pytest.mark.parametrize(
        "field,invalid_value,error_type",
        [
            ("id", "", "ValidationError"),
            ("id", "invalid-uuidsdfgsdfgsdfgsdfgdsfgsdfgdfgsdfgsdfgsdfgsdfgsdfgsdfgsdfg", "ValidationError"),
            ("roles", [{"name": "", "permissions": []}], "ValidationError"),
            ("roles", [{"name": "invalid_role", "permissions": []}], "ValidationError"),
            ("roles", [{"name": "user", "permissions": ["invalid_permission"]}], "ValidationError"),
            ("roles", [{"name": "user", "permissions": []}], "ValidationError"),  # Empty permissions
            ("roles", [{"name": "user", "permissions": ["read"] * 100}], "ValidationError"),  # Too many permissions
        ],
    )
    def test_create_with_invalid_data(self, valid_user_data, field, invalid_value, error_type):
        """Test creating an ApiUser with invalid data."""
        data = valid_user_data.copy()
        data[field] = invalid_value
        with pytest.raises(Exception) as exc_info:
            ApiUser(**data)
        assert exc_info.type.__name__ == error_type

    def test_create_without_optional_roles(self, valid_user_data):
        """Test creating an ApiUser without the optional roles field."""
        data = valid_user_data.copy()
        del data["roles"]
        user = ApiUser(**data)
        assert user.roles == set()

    def test_create_with_empty_roles_set(self, valid_user_data):
        """Test creating an ApiUser with an empty roles set."""
        data = valid_user_data.copy()
        data["roles"] = set()
        user = ApiUser(**data)
        assert user.roles == set()

    def test_create_with_duplicate_roles(self, valid_user_data):
        """Test creating an ApiUser with duplicate roles."""
        data = valid_user_data.copy()
        data["roles"] = set([
            ApiRole(name="user", permissions=frozenset(["read"])),
            ApiRole(name="user", permissions=frozenset(["read"])),  # Duplicate role
        ])
        user = ApiUser(**data)
        assert len(user.roles) == 1  # Should not allow duplicates

    def test_create_with_special_characters_in_role_name(self, valid_user_data):
        """Test creating an ApiUser with special characters in role name."""
        data = valid_user_data.copy()
        data["roles"] = set([
            ApiRole(name="user-manager", permissions=frozenset(["read"])),  # Using hyphen instead of question mark
            ApiRole(name="recipe_manager", permissions=frozenset(["read"])),
        ])
        user = ApiUser(**data)
        assert len(user.roles) == 2
        role_names = {role.name for role in user.roles}
        assert "user-manager" in role_names
        assert "recipe_manager" in role_names

    def test_from_domain_with_valid_object(self, valid_user_domain):
        """Test creating an ApiUser from a valid domain object."""
        user = ApiUser.from_domain(valid_user_domain)
        assert user.id == valid_user_domain.id
        assert len(user.roles) == len(valid_user_domain.roles)
        # Convert domain roles to API roles for comparison
        expected_roles = [ApiRole(name=role.name, permissions=role.permissions) for role in valid_user_domain.roles]
        # Sort both lists by role name for consistent comparison
        assert sorted(user.roles, key=lambda x: x.name) == sorted(expected_roles, key=lambda x: x.name)

    def test_to_domain_with_valid_object(self, valid_user_data):
        """Test converting an ApiUser to a domain object."""
        user = ApiUser(**valid_user_data)
        domain_obj = user.to_domain()
        assert isinstance(domain_obj, User)
        assert domain_obj.id == valid_user_data["id"]
        assert len(domain_obj.roles) == len(valid_user_data["roles"])
        # Convert API roles to domain roles for comparison
        expected_roles = [Role(name=role.name, permissions=role.permissions) for role in valid_user_data["roles"]]
        # Sort both lists by role name for consistent comparison
        assert sorted(domain_obj.roles, key=lambda x: x.name) == sorted(expected_roles, key=lambda x: x.name)

    def test_from_orm_model_with_valid_object(self, valid_user_orm):
        """Test creating an ApiUser from a valid ORM model."""
        user = ApiUser.from_orm_model(valid_user_orm)
        assert user.id == valid_user_orm.id
        assert len(user.roles) == len(valid_user_orm.roles)
        # Convert ORM roles to expected format for comparison
        expected_roles = [ApiRole(name=role["name"], permissions=frozenset(role["permissions"].split(", "))) for role in valid_user_orm.roles]
        # Convert both to sets for comparison
        assert set(user.roles) == set(expected_roles)

    def test_to_orm_kwargs_with_valid_object(self, valid_user_data):
        """Test converting an ApiUser to ORM model kwargs."""
        user = ApiUser(**valid_user_data)
        kwargs = user.to_orm_kwargs()
        assert kwargs["id"] == valid_user_data["id"]
        assert len(kwargs["roles"]) == len(valid_user_data["roles"])
        # Convert expected roles to ORM format for comparison
        expected_roles = [
            {"name": role.name, "permissions": ", ".join(role.permissions)}
            for role in valid_user_data["roles"]
        ]
        assert sorted(kwargs["roles"], key=lambda x: x["name"]) == sorted(expected_roles, key=lambda x: x["name"])

    def test_immutability(self, valid_user_data):
        """Test that ApiUser instances are immutable."""
        user = ApiUser(**valid_user_data)
        with pytest.raises(Exception):
            user.id = str(uuid4())
        with pytest.raises(Exception):
            user.roles = set()
        with pytest.raises(Exception):
            next(iter(user.roles)).name = "new_role" 