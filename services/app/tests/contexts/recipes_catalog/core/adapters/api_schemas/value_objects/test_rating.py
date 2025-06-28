import pytest
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.rating_sa_model import RatingSaModel
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating


@pytest.fixture
def valid_rating_data():
    """Fixture providing valid rating data for testing."""
    return {
        "user_id": str(uuid4()),
        "recipe_id": str(uuid4()),
        "taste": 4,
        "convenience": 3,
        "comment": "Great recipe!",
    }


@pytest.fixture
def valid_rating_domain(valid_rating_data):
    """Fixture creating a valid Rating domain object."""
    return Rating(**valid_rating_data)


@pytest.fixture
def valid_rating_orm(valid_rating_data):
    """Fixture creating a valid RatingSaModel ORM object."""
    return RatingSaModel(**valid_rating_data)


class TestApiRating:
    """Test suite for ApiRating schema."""

    def test_create_with_valid_data(self, valid_rating_data):
        """Test creating an ApiRating with valid data."""
        rating = ApiRating(**valid_rating_data)
        assert rating.user_id == valid_rating_data["user_id"]
        assert rating.recipe_id == valid_rating_data["recipe_id"]
        assert rating.taste == valid_rating_data["taste"]
        assert rating.convenience == valid_rating_data["convenience"]
        assert rating.comment == valid_rating_data["comment"]

    @pytest.mark.parametrize(
        "field,invalid_value,error_type",
        [
            ("user_id", "", "ValidationError"),
            ("user_id", "invalid-uuidfdfadsfasdfdsfasdfasdfasdfasdfadfasdfasdfasdfasdfasdfasdfasdf", "ValidationError"),
            ("recipe_id", "", "ValidationError"),
            ("recipe_id", "invalid-uuidfadfadsfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfa", "ValidationError"),
            ("taste", 6, "ValidationError"),
            ("taste", -1, "ValidationError"),
            ("taste", 1.5, "ValidationError"),  # Test decimal rating
            ("convenience", 6, "ValidationError"),
            ("convenience", -1, "ValidationError"),
            ("convenience", 1.5, "ValidationError"),  # Test decimal rating
            ("comment", "a" * 1001, "ValidationError"),  # Test max length
        ],
    )
    def test_create_with_invalid_data(self, valid_rating_data, field, invalid_value, error_type):
        """Test creating an ApiRating with invalid data."""
        data = valid_rating_data.copy()
        data[field] = invalid_value
        with pytest.raises(Exception) as exc_info:
            ApiRating(**data)
        assert exc_info.type.__name__ == error_type

    def test_create_without_optional_comment(self, valid_rating_data):
        """Test creating an ApiRating without the optional comment field."""
        data = valid_rating_data.copy()
        del data["comment"]
        rating = ApiRating(**data)
        assert rating.comment is None

    def test_whitespace_handling(self, valid_rating_data):
        """Test that whitespace is properly handled in comment."""
        data = valid_rating_data.copy()
        data["comment"] = "  Great recipe!  "
        rating = ApiRating(**data)
        assert rating.comment == "Great recipe!"  # Should be stripped

    def test_special_characters_in_comment(self, valid_rating_data):
        """Test handling of special characters in comment."""
        data = valid_rating_data.copy()
        data["comment"] = "Great recipe! 😋 #yummy #delicious"
        rating = ApiRating(**data)
        assert rating.comment == "Great recipe! 😋 #yummy #delicious"

    def test_empty_string_comment_returns_none(self, valid_rating_data):
        """Test that empty string comment returns None."""
        data = valid_rating_data.copy()
        data["comment"] = ""
        rating = ApiRating(**data)
        assert rating.comment is None

    def test_whitespace_only_comment_returns_none(self, valid_rating_data):
        """Test that whitespace-only comment returns None."""
        data = valid_rating_data.copy()
        data["comment"] = "   "
        rating = ApiRating(**data)
        assert rating.comment is None

    def test_newline_whitespace_comment_returns_none(self, valid_rating_data):
        """Test that comment with newlines and whitespace returns None."""
        data = valid_rating_data.copy()
        data["comment"] = " \n \t \r "
        rating = ApiRating(**data)
        assert rating.comment is None

    def test_from_domain_with_valid_object(self, valid_rating_domain):
        """Test creating an ApiRating from a valid domain object."""
        rating = ApiRating.from_domain(valid_rating_domain)
        assert rating.user_id == valid_rating_domain.user_id
        assert rating.recipe_id == valid_rating_domain.recipe_id
        assert rating.taste == valid_rating_domain.taste
        assert rating.convenience == valid_rating_domain.convenience
        assert rating.comment == valid_rating_domain.comment

    def test_to_domain_with_valid_object(self, valid_rating_data):
        """Test converting an ApiRating to a domain object."""
        rating = ApiRating(**valid_rating_data)
        domain_obj = rating.to_domain()
        assert isinstance(domain_obj, Rating)
        assert domain_obj.user_id == valid_rating_data["user_id"]
        assert domain_obj.recipe_id == valid_rating_data["recipe_id"]
        assert domain_obj.taste == valid_rating_data["taste"]
        assert domain_obj.convenience == valid_rating_data["convenience"]
        assert domain_obj.comment == valid_rating_data["comment"]

    def test_from_orm_model_with_valid_object(self, valid_rating_orm):
        """Test creating an ApiRating from a valid ORM model."""
        rating = ApiRating.from_orm_model(valid_rating_orm)
        assert rating.user_id == valid_rating_orm.user_id
        assert rating.recipe_id == valid_rating_orm.recipe_id
        assert rating.taste == valid_rating_orm.taste
        assert rating.convenience == valid_rating_orm.convenience
        assert rating.comment == valid_rating_orm.comment

    def test_to_orm_kwargs_with_valid_object(self, valid_rating_data):
        """Test converting an ApiRating to ORM model kwargs."""
        rating = ApiRating(**valid_rating_data)
        kwargs = rating.to_orm_kwargs()
        assert kwargs["user_id"] == valid_rating_data["user_id"]
        assert kwargs["recipe_id"] == valid_rating_data["recipe_id"]
        assert kwargs["taste"] == valid_rating_data["taste"]
        assert kwargs["convenience"] == valid_rating_data["convenience"]
        assert kwargs["comment"] == valid_rating_data["comment"]

    def test_immutability(self, valid_rating_data):
        """Test that ApiRating instances are immutable."""
        rating = ApiRating(**valid_rating_data)
        with pytest.raises(Exception):
            rating.user_id = str(uuid4())
        with pytest.raises(Exception):
            rating.recipe_id = str(uuid4())
        with pytest.raises(Exception):
            rating.taste = 5
        with pytest.raises(Exception):
            rating.convenience = 5
        with pytest.raises(Exception):
            rating.comment = "New comment" 