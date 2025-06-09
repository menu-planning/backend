import pytest
from src.contexts.iam.core.adapters.api_schemas.commands.api_create_user import ApiCreateUser
from src.contexts.iam.core.domain.commands import CreateUser
from pydantic import ValidationError


class TestApiCreateUser:
    """Test suite for ApiCreateUser schema."""

    def test_create_user_schema_validation(self):
        """Test that ApiCreateUser properly validates input data."""
        # Test valid data
        valid_data = {"user_id": "123"}
        model = ApiCreateUser(**valid_data)
        assert model.user_id == "123"

        # Test invalid data - missing required field
        with pytest.raises(ValueError):
            ApiCreateUser()  # type: ignore

        # Test invalid data - wrong type
        with pytest.raises(ValueError):
            ApiCreateUser(user_id=123)  # type: ignore

        # Test invalid data - extra field
        with pytest.raises(ValueError):
            ApiCreateUser(user_id="123", extra_field="value")  # type: ignore

    def test_create_user_to_domain(self):
        """Test conversion from API schema to domain model."""
        # Test successful conversion
        api_model = ApiCreateUser(user_id="123")
        domain_model = api_model.to_domain()
        assert isinstance(domain_model, CreateUser)
        assert domain_model.user_id == "123"

        # Test validation error with empty string
        with pytest.raises(ValidationError) as exc_info:
            ApiCreateUser(user_id="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_create_user_from_domain(self):
        """Test conversion from domain model to API schema."""
        # Test successful conversion
        domain_model = CreateUser(user_id="123")
        api_model = ApiCreateUser.from_domain(domain_model)
        assert isinstance(api_model, ApiCreateUser)
        assert api_model.user_id == "123"

    @pytest.mark.parametrize(
        "data,should_raise",
        [
            ({"user_id": "123"}, False),  # valid
            ({}, True),                   # missing user_id
            ({"user_id": 123}, True),     # wrong type
            ({"user_id": "123", "extra": 1}, True),  # extra field
        ]
    )
    def test_create_user_parametrized_validation(self, data, should_raise):
        """Test ApiCreateUser validation with various input data."""
        if should_raise:
            with pytest.raises(ValueError):
                ApiCreateUser(**data)
        else:
            model = ApiCreateUser(**data)
            assert model.user_id == data["user_id"]

    def test_create_user_immutability(self):
        """Test that ApiCreateUser instances are immutable."""
        model = ApiCreateUser(user_id="123")
        with pytest.raises(ValueError):
            model.user_id = "456" 