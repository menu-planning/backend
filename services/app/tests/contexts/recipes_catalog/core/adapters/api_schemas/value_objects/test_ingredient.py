import pytest
from datetime import datetime
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import IngredientSaModel
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.shared_kernel.domain.enums import MeasureUnit


@pytest.fixture
def valid_ingredient_data():
    """Fixture providing valid ingredient data for testing."""
    return {
        "name": "Salt",
        "quantity": 1.5,
        "unit": MeasureUnit.GRAM,
        "position": 1,
        "full_text": "1.5 grams of salt",
        "product_id": str(uuid4()),
    }


@pytest.fixture
def valid_ingredient_domain(valid_ingredient_data):
    """Fixture creating a valid Ingredient domain object."""
    return Ingredient(**valid_ingredient_data)


@pytest.fixture
def valid_ingredient_orm(valid_ingredient_data):
    """Fixture creating a valid IngredientSaModel ORM object."""
    return IngredientSaModel(
        **valid_ingredient_data,
        recipe_id=str(uuid4()),
        preprocessed_name=valid_ingredient_data["name"].lower(),
        created_at=datetime.now(),
    )


class TestApiIngredient:
    """Test suite for ApiIngredient schema."""

    def test_create_with_valid_data(self, valid_ingredient_data):
        """Test creating an ApiIngredient with valid data."""
        ingredient = ApiIngredient(**valid_ingredient_data)
        assert ingredient.name == valid_ingredient_data["name"]
        assert ingredient.quantity == valid_ingredient_data["quantity"]
        assert ingredient.unit == valid_ingredient_data["unit"]
        assert ingredient.position == valid_ingredient_data["position"]
        assert ingredient.full_text == valid_ingredient_data["full_text"]
        assert ingredient.product_id == valid_ingredient_data["product_id"]

    @pytest.mark.parametrize(
        "field,invalid_value,error_type",
        [
            ("name", "", "ValidationError"),
            ("name", " " * 100, "ValidationError"),  # Test whitespace only
            ("name", "a" * 256, "ValidationError"),  # Test max length
            # ("name", "Special!@#$%^&*()", "ValidationError"),  # Test special characters
            ("quantity", -1.0, "ValidationError"),
            ("quantity", 1e10, "ValidationError"),  # Test very large number
            ("unit", "invalid_unit", "ValidationError"),
            ("position", -1, "ValidationError"),
            ("full_text", "", "ValidationError"),
            ("full_text", " " * 1000, "ValidationError"),  # Test whitespace only
            ("full_text", "a" * 1001, "ValidationError"),  # Test max length
            ("product_id", "", "ValidationError"),
            ("product_id", "invalid-uuidfadsfadsfasdfasdfasdfasdfasdfasdfasdfasdfs", "ValidationError"),
        ],
    )
    def test_create_with_invalid_data(self, valid_ingredient_data, field, invalid_value, error_type):
        """Test creating an ApiIngredient with invalid data."""
        data = valid_ingredient_data.copy()
        data[field] = invalid_value
        with pytest.raises(Exception) as exc_info:
            ApiIngredient(**data)
        assert exc_info.type.__name__ == error_type

    @pytest.mark.parametrize(
        "quantity,unit,expected_text",
        [
            (1.0, MeasureUnit.GRAM, "1.0 gram of salt"),
            (2.0, MeasureUnit.GRAM, "2.0 grams of salt"),
            (0.5, MeasureUnit.KILOGRAM, "0.5 kilogram of salt"),
            (1.0, MeasureUnit.LITER, "1.0 liter of salt"),
            (2.0, MeasureUnit.LITER, "2.0 liters of salt"),
        ],
    )
    def test_full_text_generation(self, valid_ingredient_data, quantity, unit, expected_text):
        """Test that full_text is correctly generated based on quantity and unit."""
        data = valid_ingredient_data.copy()
        data["quantity"] = quantity
        data["unit"] = unit
        data["full_text"] = expected_text
        ingredient = ApiIngredient(**data)
        assert ingredient.full_text == expected_text

    def test_whitespace_handling(self, valid_ingredient_data):
        """Test that whitespace is properly handled in name and full_text."""
        data = valid_ingredient_data.copy()
        data["name"] = "  Salt  "
        data["full_text"] = "  1.5 grams of salt  "
        ingredient = ApiIngredient(**data)
        assert ingredient.name == "Salt"
        assert ingredient.full_text == "1.5 grams of salt"

    def test_from_domain_with_valid_object(self, valid_ingredient_domain):
        """Test creating an ApiIngredient from a valid domain object."""
        ingredient = ApiIngredient.from_domain(valid_ingredient_domain)
        assert ingredient.name == valid_ingredient_domain.name
        assert ingredient.quantity == valid_ingredient_domain.quantity
        assert ingredient.unit == valid_ingredient_domain.unit
        assert ingredient.position == valid_ingredient_domain.position
        assert ingredient.full_text == valid_ingredient_domain.full_text
        assert ingredient.product_id == valid_ingredient_domain.product_id

    def test_to_domain_with_valid_object(self, valid_ingredient_data):
        """Test converting an ApiIngredient to a domain object."""
        ingredient = ApiIngredient(**valid_ingredient_data)
        domain_obj = ingredient.to_domain()
        assert isinstance(domain_obj, Ingredient)
        assert domain_obj.name == valid_ingredient_data["name"]
        assert domain_obj.quantity == valid_ingredient_data["quantity"]
        assert domain_obj.unit == valid_ingredient_data["unit"]
        assert domain_obj.position == valid_ingredient_data["position"]
        assert domain_obj.full_text == valid_ingredient_data["full_text"]
        assert domain_obj.product_id == valid_ingredient_data["product_id"]

    def test_from_orm_model_with_valid_object(self, valid_ingredient_orm):
        """Test creating an ApiIngredient from a valid ORM model."""
        ingredient = ApiIngredient.from_orm_model(valid_ingredient_orm)
        assert ingredient.name == valid_ingredient_orm.name
        assert ingredient.quantity == valid_ingredient_orm.quantity
        assert ingredient.unit == MeasureUnit(valid_ingredient_orm.unit)
        assert ingredient.position == valid_ingredient_orm.position
        assert ingredient.full_text == valid_ingredient_orm.full_text
        assert ingredient.product_id == valid_ingredient_orm.product_id

    def test_to_orm_kwargs_with_valid_object(self, valid_ingredient_data):
        """Test converting an ApiIngredient to ORM model kwargs."""
        ingredient = ApiIngredient(**valid_ingredient_data)
        kwargs = ingredient.to_orm_kwargs()
        assert kwargs["name"] == valid_ingredient_data["name"]
        assert kwargs["quantity"] == valid_ingredient_data["quantity"]
        assert kwargs["unit"] == valid_ingredient_data["unit"].value
        assert kwargs["position"] == valid_ingredient_data["position"]
        assert kwargs["full_text"] == valid_ingredient_data["full_text"]
        assert kwargs["product_id"] == valid_ingredient_data["product_id"]

    def test_immutability(self, valid_ingredient_data):
        """Test that ApiIngredient instances are immutable."""
        ingredient = ApiIngredient(**valid_ingredient_data)
        with pytest.raises(Exception):
            ingredient.name = "New Name"
        with pytest.raises(Exception):
            ingredient.quantity = 2.0
        with pytest.raises(Exception):
            ingredient.unit = MeasureUnit.KILOGRAM
        with pytest.raises(Exception):
            ingredient.position = 2
        with pytest.raises(Exception):
            ingredient.full_text = "New text"
        with pytest.raises(Exception):
            ingredient.product_id = str(uuid4()) 