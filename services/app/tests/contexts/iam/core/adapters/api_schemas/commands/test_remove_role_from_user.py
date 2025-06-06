import pytest
from src.contexts.iam.core.adapters.api_schemas.commands.remove_role_from_user import ApiRemoveRoleFromUser
from src.contexts.iam.core.adapters.api_schemas.value_objects.role import ApiRole
from src.contexts.iam.core.domain.commands import RemoveRoleFromUser
from src.contexts.iam.core.domain.value_objects.role import Role
from pydantic import ValidationError


class TestApiRemoveRoleFromUser:
    """Test suite for ApiRemoveRoleFromUser schema."""

    @pytest.fixture
    def valid_role(self):
        """Fixture providing a valid ApiRole instance."""
        return ApiRole(name="admin", context="IAM", permissions=["read", "write"])

    def test_remove_role_schema_validation(self, valid_role):
        """Test that ApiRemoveRoleFromUser properly validates input data."""
        # Test valid data
        valid_data = {"user_id": "123", "role": valid_role}
        model = ApiRemoveRoleFromUser(**valid_data)
        assert model.user_id == "123"
        assert model.role == valid_role

        # Test invalid data - missing required fields
        with pytest.raises(ValueError):
            ApiRemoveRoleFromUser()  # type: ignore
        with pytest.raises(ValueError):
            ApiRemoveRoleFromUser(user_id="123")  # type: ignore
        with pytest.raises(ValueError):
            ApiRemoveRoleFromUser(role=valid_role)  # type: ignore

        # Test invalid data - wrong types
        with pytest.raises(ValueError):
            ApiRemoveRoleFromUser(user_id=123, role=valid_role)  # type: ignore
        with pytest.raises(ValueError):
            ApiRemoveRoleFromUser(user_id="123", role="not_a_role")  # type: ignore

        # Test invalid data - extra field
        with pytest.raises(ValueError):
            ApiRemoveRoleFromUser(user_id="123", role=valid_role, extra_field="value")  # type: ignore

    def test_remove_role_to_domain(self, valid_role):
        """Test conversion from API schema to domain model."""
        # Test successful conversion
        api_model = ApiRemoveRoleFromUser(user_id="123", role=valid_role)
        domain_model = api_model.to_domain()
        assert isinstance(domain_model, RemoveRoleFromUser)
        assert domain_model.user_id == "123"
        assert isinstance(domain_model.role, Role)
        assert domain_model.role.name == "admin"
        assert domain_model.role.context == "IAM"
        assert domain_model.role.permissions == ["read", "write"]

        # Test validation error with empty string
        with pytest.raises(ValidationError) as exc_info:
            ApiRemoveRoleFromUser(user_id="", role=valid_role)
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_remove_role_from_domain(self, valid_role):
        """Test conversion from domain model to API schema."""
        # Test successful conversion
        domain_role = Role(name="admin", context="IAM", permissions=["read", "write"])
        domain_model = RemoveRoleFromUser(user_id="123", role=domain_role)
        api_model = ApiRemoveRoleFromUser.from_domain(domain_model)
        assert isinstance(api_model, ApiRemoveRoleFromUser)
        assert api_model.user_id == "123"
        assert api_model.role.name == "admin"
        assert api_model.role.context == "IAM"
        assert api_model.role.permissions == ["read", "write"]

    @pytest.mark.parametrize(
        "data,should_raise",
        [
            ({"user_id": "123", "role": ApiRole(name="admin", context="IAM", permissions=["read"])}, False),  # valid
            ({}, True),  # missing all fields
            ({"user_id": "123"}, True),  # missing role
            ({"role": ApiRole(name="admin", context="IAM", permissions=["read"])}, True),  # missing user_id
            ({"user_id": 123, "role": ApiRole(name="admin", context="IAM", permissions=["read"])}, True),  # wrong user_id type
            ({"user_id": "123", "role": "not_a_role"}, True),  # wrong role type
            ({"user_id": "123", "role": ApiRole(name="admin", context="IAM", permissions=["read"]), "extra": 1}, True),  # extra field
        ]
    )
    def test_remove_role_parametrized_validation(self, data, should_raise):
        """Test ApiRemoveRoleFromUser validation with various input data."""
        if should_raise:
            with pytest.raises(ValueError):
                ApiRemoveRoleFromUser(**data)
        else:
            model = ApiRemoveRoleFromUser(**data)
            assert model.user_id == data["user_id"]
            assert model.role == data["role"]

    def test_remove_role_immutability(self, valid_role):
        """Test that ApiRemoveRoleFromUser instances are immutable."""
        model = ApiRemoveRoleFromUser(user_id="123", role=valid_role)
        with pytest.raises(ValueError):
            model.user_id = "456"
        with pytest.raises(ValueError):
            model.role = ApiRole(name="user", context="IAM", permissions=["read"]) 