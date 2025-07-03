import pytest
from datetime import time
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_meal_sa_model import MenuMealSaModel
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.value_objects.api_menu_meal import ApiMenuMeal
from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import MenuMeal
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts


@pytest.fixture
def valid_menu_meal_data():
    """Fixture providing valid menu meal data for testing."""
    return {
        "meal_id": str(uuid4()),
        "meal_name": "Breakfast",
        "nutri_facts": ApiNutriFacts(
            calories=500,
            protein=20,
            carbohydrate=60,
            total_fat=15,
        ), # type: ignore
        "week": 1,
        "weekday": "Monday",
        "hour": time(8, 0),
        "meal_type": "breakfast",
    }


@pytest.fixture
def valid_menu_meal_domain(valid_menu_meal_data):
    """Fixture creating a valid MenuMeal domain object."""
    return MenuMeal(
        meal_id=valid_menu_meal_data["meal_id"],
        meal_name=valid_menu_meal_data["meal_name"],
        nutri_facts=valid_menu_meal_data["nutri_facts"].to_domain(),
        week=valid_menu_meal_data["week"],
        weekday=valid_menu_meal_data["weekday"],
        hour=valid_menu_meal_data["hour"],
        meal_type=valid_menu_meal_data["meal_type"],
    )


@pytest.fixture
def valid_menu_meal_orm(valid_menu_meal_data):
    """Fixture creating a valid MenuMealSaModel ORM object."""
    return MenuMealSaModel(
        meal_id=valid_menu_meal_data["meal_id"],
        meal_name=valid_menu_meal_data["meal_name"],
        nutri_facts=NutriFactsSaModel(**valid_menu_meal_data["nutri_facts"].to_orm_kwargs()),
        week=valid_menu_meal_data["week"],
        weekday=valid_menu_meal_data["weekday"],
        hour=valid_menu_meal_data["hour"],
        meal_type=valid_menu_meal_data["meal_type"],
    )


class TestApiMenuMeal:
    """Test suite for ApiMenuMeal schema."""

    def test_create_with_valid_data(self, valid_menu_meal_data):
        """Test creating an ApiMenuMeal with valid data."""
        menu_meal = ApiMenuMeal(**valid_menu_meal_data)
        assert menu_meal.meal_id == valid_menu_meal_data["meal_id"]
        assert menu_meal.meal_name == valid_menu_meal_data["meal_name"]
        assert menu_meal.nutri_facts == valid_menu_meal_data["nutri_facts"]
        assert menu_meal.week == valid_menu_meal_data["week"]
        assert menu_meal.weekday == valid_menu_meal_data["weekday"]
        assert menu_meal.hour == valid_menu_meal_data["hour"]
        assert menu_meal.meal_type == valid_menu_meal_data["meal_type"]

    @pytest.mark.parametrize(
        "field,invalid_value,error_type",
        [
            ("meal_id", "", "ValidationError"),
            ("meal_id", "invalid-uuidfadsfadsfadsfadsfasdfasdfasdfdsadfadsfadsfas", "ValidationError"),
            ("meal_name", "", "ValidationError"),
            # ("meal_name", " " * 100, "ValidationError"),  # Test whitespace only
            ("meal_name", "a" * 256, "ValidationError"),  # Test max length
            # ("meal_name", "Special!@#$%^&*()", "ValidationError"),  # Test special characters
            ("week", 0, "ValidationError"),
            ("week", -1, "ValidationError"),
            ("week", 53, "ValidationError"),  # Test max weeks in a year
            ("weekday", "", "ValidationError"),
            # ("weekday", "invalid_day", "ValidationError"),
            # ("weekday", "monday", "ValidationError"),  # Test case sensitivity
            ("meal_type", "", "ValidationError"),
            # ("meal_type", "invalid_type", "ValidationError"),
        ],
    )
    def test_create_with_invalid_data(self, valid_menu_meal_data, field, invalid_value, error_type):
        """Test creating an ApiMenuMeal with invalid data."""
        data = valid_menu_meal_data.copy()
        data[field] = invalid_value
        with pytest.raises(Exception) as exc_info:
            ApiMenuMeal(**data)
        assert exc_info.type.__name__ == error_type

    @pytest.mark.parametrize(
        "weekday",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    )
    def test_create_with_valid_weekdays(self, valid_menu_meal_data, weekday):
        """Test creating an ApiMenuMeal with each valid weekday."""
        data = valid_menu_meal_data.copy()
        data["weekday"] = weekday
        menu_meal = ApiMenuMeal(**data)
        assert menu_meal.weekday == weekday

    @pytest.mark.parametrize(
        "meal_type",
        ["breakfast", "lunch", "dinner", "snack"],
    )
    def test_create_with_valid_meal_types(self, valid_menu_meal_data, meal_type):
        """Test creating an ApiMenuMeal with valid meal types."""
        data = valid_menu_meal_data.copy()
        data["meal_type"] = meal_type
        menu_meal = ApiMenuMeal(**data)
        assert menu_meal.meal_type == meal_type

    @pytest.mark.parametrize(
        "hour",
        [
            time(0, 0),  # Midnight
            time(6, 0),  # Early morning
            time(12, 0),  # Noon
            time(18, 0),  # Evening
            time(23, 59),  # Late night
        ],
    )
    def test_create_with_valid_hours(self, valid_menu_meal_data, hour):
        """Test creating an ApiMenuMeal with various valid hours."""
        data = valid_menu_meal_data.copy()
        data["hour"] = hour
        menu_meal = ApiMenuMeal(**data)
        assert menu_meal.hour == hour

    def test_create_without_optional_nutri_facts(self, valid_menu_meal_data):
        """Test creating an ApiMenuMeal without the optional nutri_facts field."""
        data = valid_menu_meal_data.copy()
        del data["nutri_facts"]
        menu_meal = ApiMenuMeal(**data)
        assert menu_meal.nutri_facts is None

    def test_create_without_optional_hour(self, valid_menu_meal_data):
        """Test creating an ApiMenuMeal without the optional hour field."""
        data = valid_menu_meal_data.copy()
        del data["hour"]
        menu_meal = ApiMenuMeal(**data)
        assert menu_meal.hour is None

    def test_whitespace_handling(self, valid_menu_meal_data):
        """Test that whitespace is properly handled in meal_name."""
        data = valid_menu_meal_data.copy()
        data["meal_name"] = "  Breakfast  "
        menu_meal = ApiMenuMeal(**data)
        assert menu_meal.meal_name == "Breakfast"  # Should be stripped

    def test_from_domain_with_valid_object(self, valid_menu_meal_domain):
        """Test creating an ApiMenuMeal from a valid domain object."""
        menu_meal = ApiMenuMeal.from_domain(valid_menu_meal_domain)
        assert menu_meal.meal_id == valid_menu_meal_domain.meal_id
        assert menu_meal.meal_name == valid_menu_meal_domain.meal_name
        assert menu_meal.nutri_facts == ApiNutriFacts.from_domain(valid_menu_meal_domain.nutri_facts)
        assert menu_meal.week == valid_menu_meal_domain.week
        assert menu_meal.weekday == valid_menu_meal_domain.weekday
        assert menu_meal.hour == valid_menu_meal_domain.hour
        assert menu_meal.meal_type == valid_menu_meal_domain.meal_type

    def test_to_domain_with_valid_object(self, valid_menu_meal_data):
        """Test converting an ApiMenuMeal to a domain object."""
        menu_meal = ApiMenuMeal(**valid_menu_meal_data)
        domain_obj = menu_meal.to_domain()
        assert isinstance(domain_obj, MenuMeal)
        assert domain_obj.meal_id == valid_menu_meal_data["meal_id"]
        assert domain_obj.meal_name == valid_menu_meal_data["meal_name"]
        assert domain_obj.nutri_facts == valid_menu_meal_data["nutri_facts"].to_domain()
        assert domain_obj.week == valid_menu_meal_data["week"]
        assert domain_obj.weekday == valid_menu_meal_data["weekday"]
        assert domain_obj.hour == valid_menu_meal_data["hour"]
        assert domain_obj.meal_type == valid_menu_meal_data["meal_type"]

    def test_from_orm_model_with_valid_object(self, valid_menu_meal_orm):
        """Test creating an ApiMenuMeal from a valid ORM model."""
        menu_meal = ApiMenuMeal.from_orm_model(valid_menu_meal_orm)
        assert menu_meal.meal_id == valid_menu_meal_orm.meal_id
        assert menu_meal.meal_name == valid_menu_meal_orm.meal_name
        assert menu_meal.week == int(valid_menu_meal_orm.week)  # Week should be converted to int
        assert menu_meal.weekday == valid_menu_meal_orm.weekday
        assert menu_meal.hour == valid_menu_meal_orm.hour
        assert menu_meal.meal_type == valid_menu_meal_orm.meal_type

    def test_to_orm_kwargs_with_valid_object(self, valid_menu_meal_data):
        """Test converting an ApiMenuMeal to ORM model kwargs."""
        menu_meal = ApiMenuMeal(**valid_menu_meal_data)
        kwargs = menu_meal.to_orm_kwargs()
        assert kwargs["meal_id"] == valid_menu_meal_data["meal_id"]
        assert kwargs["meal_name"] == valid_menu_meal_data["meal_name"]
        assert kwargs["nutri_facts"] == valid_menu_meal_data["nutri_facts"].to_orm_kwargs()
        assert kwargs["week"] == str(valid_menu_meal_data["week"])  # Week should be converted to string
        assert kwargs["weekday"] == valid_menu_meal_data["weekday"]
        assert kwargs["hour"] == valid_menu_meal_data["hour"]
        assert kwargs["meal_type"] == valid_menu_meal_data["meal_type"]

    def test_immutability(self, valid_menu_meal_data):
        """Test that ApiMenuMeal instances are immutable."""
        menu_meal = ApiMenuMeal(**valid_menu_meal_data)
        with pytest.raises(Exception):
            menu_meal.meal_id = str(uuid4())
        with pytest.raises(Exception):
            menu_meal.meal_name = "New Name"
        with pytest.raises(Exception):
            menu_meal.week = 2
        with pytest.raises(Exception):
            menu_meal.weekday = "Tuesday"
        with pytest.raises(Exception):
            menu_meal.hour = time(9, 0)
        with pytest.raises(Exception):
            menu_meal.meal_type = "lunch"
        with pytest.raises(Exception):
            menu_meal.nutri_facts = ApiNutriFacts(calories=600, protein=25, carbohydrate=70, total_fat=20)  # type: ignore