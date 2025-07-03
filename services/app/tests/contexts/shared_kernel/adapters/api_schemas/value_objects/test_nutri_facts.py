import pytest
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import ApiNutriValue


class TestApiNutriValue:
    """Test suite for ApiNutriValue schema.
    
    This class tests the API schema for nutritional values, which allows None values
    for both value and unit fields, unlike the domain model which converts None to
    default values for mathematical operations.
    """

    @pytest.mark.parametrize("value,unit", [
        (1.5, MeasureUnit.GRAM),
        (2.0, MeasureUnit.KILOGRAM),
        (0.5, MeasureUnit.LITER),
        (100.0, MeasureUnit.ENERGY),
    ])
    def test_create_with_valid_values(self, value, unit):
        """Test creating a nutritional value with different valid combinations.
        
        The API schema should accept any non-negative float value and any valid unit.
        """
        nutri_value = ApiNutriValue(value=value, unit=unit)
        assert nutri_value.value == value
        assert nutri_value.unit == unit

    @pytest.mark.parametrize("invalid_value", [-1.0, -0.5, -100.0])
    def test_create_with_negative_values_raises_error(self, invalid_value):
        """Test that creating a nutritional value with negative values raises ValueError.
        
        The API schema should validate that values are non-negative to maintain
        consistency with the domain model's requirements.
        """
        with pytest.raises(ValueError):
            ApiNutriValue(value=invalid_value, unit=MeasureUnit.GRAM)

    def test_from_domain_converts_correctly(self):
        """Test converting from domain object to API schema.
        
        The API schema should correctly convert domain objects, preserving
        their values and units.
        """
        domain_value = NutriValue(value=2.5, unit=MeasureUnit.KILOGRAM)
        api_value = ApiNutriValue.from_domain(domain_value)
        
        assert api_value.value == 2.5
        assert api_value.unit == MeasureUnit.KILOGRAM

    def test_from_domain_none_raises_error(self):
        """Test that converting from None domain object raises AttributeError.
        
        The API schema's from_domain method requires a valid domain object
        due to strict type checking in the base class.
        """
        with pytest.raises(AttributeError):
            ApiNutriValue.from_domain(None) # type: ignore

    def test_to_domain_converts_correctly(self):
        """Test converting from API schema to domain object.
        
        The API schema should correctly convert to domain objects, with None
        values being converted to zeros and None units to defaults.
        """
        api_value = ApiNutriValue(value=3.0, unit=MeasureUnit.LITER)
        domain_value = api_value.to_domain()
        
        assert domain_value.value == 3.0
        assert domain_value.unit == MeasureUnit.LITER

    def test_to_domain_passes_none_values_unchanged(self):
        """Test that None values are passed as is to domain objects.
        
        The domain NutriValue accepts None values, so ApiNutriValue should pass them unchanged.
        """
        api_value = ApiNutriValue(value=None, unit=None) # type: ignore
        domain_value = api_value.to_domain()
        assert domain_value.value is None
        assert domain_value.unit is None

    @pytest.mark.parametrize("value,unit,expected", [
        (1.5, MeasureUnit.GRAM, {"value": 1.5, "unit": "g"}),
        (None, None, {"value": None, "unit": None}),
        (2.0, MeasureUnit.KILOGRAM, {"value": 2.0, "unit": "kg"}),
    ])
    def test_serialization(self, value, unit, expected):
        """Test that the nutritional value serializes correctly.
        
        The API schema should serialize to a dictionary with the correct
        value and unit, preserving None values.
        """
        value = ApiNutriValue(value=value, unit=unit)
        serialized = value.model_dump()
        
        assert serialized["value"] == expected["value"]
        assert serialized["unit"] == expected["unit"]

    def test_immutability(self):
        """Test that the nutritional value is immutable.
        
        The API schema should be immutable to prevent accidental modifications
        after creation.
        """
        value = ApiNutriValue(value=1.5, unit=MeasureUnit.GRAM)
        with pytest.raises(ValueError):
            value.value = 2.0


class TestApiNutriFacts:
    """Test suite for ApiNutriFacts schema.
    
    This class tests the API schema for nutritional facts, which allows None values
    for any nutrient field, unlike the domain model which converts None to default
    values for mathematical operations.
    """

    def test_create_with_valid_nutri_values(self):
        """Test creating nutritional facts with valid ApiNutriValue instances.
        
        The API schema should accept ApiNutriValue instances for any nutrient,
        preserving their values and units.
        """
        nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=10.0, unit=MeasureUnit.GRAM),
            carbohydrate=ApiNutriValue(value=20.0, unit=MeasureUnit.GRAM),
            total_fat=ApiNutriValue(value=5.0, unit=MeasureUnit.GRAM)
        ) # type: ignore
        assert isinstance(nutri_facts.calories, ApiNutriValue)
        assert nutri_facts.calories.value == 100.0
        assert nutri_facts.calories.unit == MeasureUnit.ENERGY
        assert isinstance(nutri_facts.protein, ApiNutriValue)
        assert nutri_facts.protein.value == 10.0
        assert isinstance(nutri_facts.carbohydrate, ApiNutriValue)
        assert nutri_facts.carbohydrate.value == 20.0
        assert isinstance(nutri_facts.total_fat, ApiNutriValue)
        assert nutri_facts.total_fat.value == 5.0

    def test_create_with_float_values(self):
        """Test creating nutritional facts with float values.
        
        The API schema should accept float values for any nutrient,
        which will be converted to ApiNutriValue instances with default units.
        """
        nutri_facts = ApiNutriFacts(
            calories=100.0,
            protein=10.0,
            carbohydrate=20.0,
            total_fat=5.0
        ) # type: ignore
        assert nutri_facts.calories == 100.0
        assert nutri_facts.protein == 10.0
        assert nutri_facts.carbohydrate == 20.0
        assert nutri_facts.total_fat == 5.0

    def test_create_with_mixed_value_types(self):
        """Test creating nutritional facts with mixed value types.
        
        The API schema should accept a mix of ApiNutriValue instances and float
        values for different nutrients.
        """
        nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=10.0,
            carbohydrate=ApiNutriValue(value=20.0, unit=MeasureUnit.GRAM),
            total_fat=5.0
        ) # type: ignore
        assert isinstance(nutri_facts.calories, ApiNutriValue)
        assert nutri_facts.calories.value == 100.0
        assert nutri_facts.calories.unit == MeasureUnit.ENERGY
        assert isinstance(nutri_facts.protein, float)
        assert nutri_facts.protein == 10.0
        assert isinstance(nutri_facts.carbohydrate, ApiNutriValue)
        assert nutri_facts.carbohydrate.value == 20.0
        assert nutri_facts.carbohydrate.unit == MeasureUnit.GRAM
        assert isinstance(nutri_facts.total_fat, float)
        assert nutri_facts.total_fat == 5.0

    def test_create_with_all_none_values(self):
        """Test creating nutritional facts with all values set to None.
        
        The API schema should allow None values for all nutrients, providing
        flexibility in API responses.
        """
        nutri_facts = ApiNutriFacts(
            calories=None,
            protein=None,
            carbohydrate=None,
            total_fat=None
        ) # type: ignore
        assert nutri_facts.calories is None
        assert nutri_facts.protein is None
        assert nutri_facts.carbohydrate is None
        assert nutri_facts.total_fat is None

    def test_create_with_mixed_none_and_valid_values(self):
        """Test creating nutritional facts with a mix of None and valid values.
        
        The API schema should allow any combination of None and valid values
        for different nutrients.
        """
        nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=None,
            carbohydrate=20.0,
            total_fat=ApiNutriValue(value=5.0, unit=MeasureUnit.GRAM)
        ) # type: ignore
        assert isinstance(nutri_facts.calories, ApiNutriValue)
        assert nutri_facts.calories.value == 100.0
        assert nutri_facts.calories.unit == MeasureUnit.ENERGY
        assert nutri_facts.protein is None
        assert nutri_facts.carbohydrate == 20.0
        assert isinstance(nutri_facts.total_fat, ApiNutriValue)
        assert nutri_facts.total_fat.value == 5.0

    def test_create_with_invalid_nutri_value_raises_error(self):
        """Test that creating nutritional facts with invalid NutriValue raises error.
        
        The API schema should validate that all values are non-negative,
        even when using ApiNutriValue instances.
        """
        with pytest.raises(ValueError):
            ApiNutriFacts(
                calories=ApiNutriValue(value=-1.0, unit=MeasureUnit.ENERGY),
                protein=10.0
            ) # type: ignore

    def test_from_domain_converts_correctly(self):
        """Test converting from domain object to API schema.
        
        The API schema should correctly convert domain objects, preserving
        their values and units.
        """
        domain_facts = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=10.0, unit=MeasureUnit.GRAM),
            carbohydrate=NutriValue(value=20.0, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=5.0, unit=MeasureUnit.GRAM)
        )
        api_facts = ApiNutriFacts.from_domain(domain_facts)
        
        assert isinstance(api_facts.calories, ApiNutriValue)
        assert api_facts.calories.value == 100.0
        assert api_facts.calories.unit == MeasureUnit.ENERGY
        assert isinstance(api_facts.protein, ApiNutriValue)
        assert api_facts.protein.value == 10.0
        assert api_facts.protein.unit == MeasureUnit.GRAM
        assert isinstance(api_facts.carbohydrate, ApiNutriValue)
        assert api_facts.carbohydrate.value == 20.0
        assert api_facts.carbohydrate.unit == MeasureUnit.GRAM
        assert isinstance(api_facts.total_fat, ApiNutriValue)
        assert api_facts.total_fat.value == 5.0
        assert api_facts.total_fat.unit == MeasureUnit.GRAM

    def test_from_domain_none_raises_error(self):
        """Test that converting from None domain object raises AttributeError.
        
        The API schema's from_domain method requires a valid domain object
        due to strict type checking in the base class.
        """
        with pytest.raises(AttributeError):
            ApiNutriFacts.from_domain(None) # type: ignore

    def test_from_domain_with_zero_values_converts_correctly(self):
        """Test converting from domain object with zero values.
        
        The API schema should correctly convert domain objects with zero values,
        preserving their units.
        """
        domain_facts = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=0.0, unit=MeasureUnit.GRAM),
            carbohydrate=NutriValue(value=20.0, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=0.0, unit=MeasureUnit.GRAM)
        )
        api_facts = ApiNutriFacts.from_domain(domain_facts)
        
        assert isinstance(api_facts.calories, ApiNutriValue)
        assert api_facts.calories.value == 100.0
        assert api_facts.calories.unit == MeasureUnit.ENERGY
        assert isinstance(api_facts.protein, ApiNutriValue)
        assert api_facts.protein.value == 0.0
        assert api_facts.protein.unit == MeasureUnit.GRAM
        assert isinstance(api_facts.carbohydrate, ApiNutriValue)
        assert api_facts.carbohydrate.value == 20.0
        assert api_facts.total_fat.value == 0.0 # type: ignore
        assert api_facts.total_fat.unit == MeasureUnit.GRAM # type: ignore

    def test_to_domain_converts_correctly(self):
        """Test converting from API schema to domain object.
        
        The API schema should correctly convert to domain objects, with None
        values being converted to zeros and None units to defaults.
        """
        api_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=10.0, unit=MeasureUnit.GRAM),
            carbohydrate=ApiNutriValue(value=20.0, unit=MeasureUnit.GRAM),
            total_fat=ApiNutriValue(value=5.0, unit=MeasureUnit.GRAM)
        ) # type: ignore
        domain_facts = api_facts.to_domain()
        
        assert domain_facts.calories.value == 100.0
        assert domain_facts.calories.unit == MeasureUnit.ENERGY
        assert domain_facts.protein.value == 10.0
        assert domain_facts.protein.unit == MeasureUnit.GRAM
        assert domain_facts.carbohydrate.value == 20.0
        assert domain_facts.carbohydrate.unit == MeasureUnit.GRAM
        assert domain_facts.total_fat.value == 5.0
        assert domain_facts.total_fat.unit == MeasureUnit.GRAM

    def test_to_domain_converts_none_values_to_zeros(self):
        """Test that None values are converted to zeros in domain objects.
        
        The domain model requires non-None values for mathematical operations,
        so the API schema should convert None values to zeros when converting
        to domain objects.
        """
        api_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=None,
            carbohydrate=20.0,
            total_fat=None
        ) # type: ignore
        domain_facts = api_facts.to_domain()
        
        assert domain_facts.calories.value == 100.0
        assert domain_facts.calories.unit == MeasureUnit.ENERGY
        assert domain_facts.protein.value == 0.0
        assert domain_facts.protein.unit == MeasureUnit.GRAM
        assert domain_facts.carbohydrate.value == 20.0
        assert domain_facts.carbohydrate.unit == MeasureUnit.GRAM
        assert domain_facts.total_fat.value == 0.0
        assert domain_facts.total_fat.unit == MeasureUnit.GRAM

    def test_to_orm_kwargs_converts_correctly(self):
        """Test converting to ORM model kwargs.
        
        The API schema should convert to ORM model kwargs, extracting values
        from ApiNutriValue instances and preserving float values.
        """
        api_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=10.0, unit=MeasureUnit.GRAM),
            carbohydrate=ApiNutriValue(value=20.0, unit=MeasureUnit.GRAM),
            total_fat=ApiNutriValue(value=5.0, unit=MeasureUnit.GRAM)
        ) # type: ignore
        kwargs = api_facts.to_orm_kwargs()
        
        assert kwargs["calories"] == 100.0
        assert kwargs["protein"] == 10.0
        assert kwargs["carbohydrate"] == 20.0
        assert kwargs["total_fat"] == 5.0

    def test_to_orm_kwargs_omits_none_values(self):
        """Test that None values are omitted from ORM model kwargs.
        
        The API schema should omit None values when converting to ORM model
        kwargs, as the ORM layer handles missing values appropriately.
        """
        api_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=None,
            carbohydrate=20.0,
            total_fat=None
        ) # type: ignore
        kwargs = api_facts.to_orm_kwargs()
        
        assert kwargs["calories"] == 100.0
        assert "protein" not in kwargs
        assert kwargs["carbohydrate"] == 20.0
        assert "total_fat" not in kwargs

    def test_serialization_preserves_values_and_units(self):
        """Test that serialization preserves values and units.
        
        The API schema should serialize to a dictionary that preserves
        all values and units, including those from ApiNutriValue instances.
        """
        nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=10.0, unit=MeasureUnit.GRAM),
            carbohydrate=ApiNutriValue(value=20.0, unit=MeasureUnit.GRAM),
            total_fat=ApiNutriValue(value=5.0, unit=MeasureUnit.GRAM)
        ) # type: ignore
        serialized = nutri_facts.model_dump()
        
        assert serialized["calories"]["value"] == 100.0
        assert serialized["calories"]["unit"] == MeasureUnit.ENERGY.value
        assert serialized["protein"]["value"] == 10.0
        assert serialized["protein"]["unit"] == MeasureUnit.GRAM.value

    def test_serialization_preserves_none_values(self):
        """Test that serialization preserves None values.
        
        The API schema should serialize to a dictionary that preserves
        None values, as they are valid in the API layer.
        """
        nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=None,
            carbohydrate=20.0,
            total_fat=None
        ) # type: ignore
        serialized = nutri_facts.model_dump()
        
        assert serialized["calories"]["value"] == 100.0
        assert serialized["calories"]["unit"] == MeasureUnit.ENERGY.value
        assert serialized["protein"] is None
        assert serialized["carbohydrate"] == 20.0
        assert serialized["total_fat"] is None

    def test_immutability(self):
        """Test that the nutritional facts are immutable.
        
        The API schema should be immutable to prevent accidental modifications
        after creation.
        """
        nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=10.0, unit=MeasureUnit.GRAM)
        ) # type: ignore
        with pytest.raises(ValueError):
            nutri_facts.calories = ApiNutriValue(value=200.0, unit=MeasureUnit.ENERGY) 