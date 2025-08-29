from typing import Any, Union

from pydantic import model_validator

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import (  # noqa: E501
    ApiNutriValue,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
    NutriFactsSaModel,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.db.base import SaBase


class ApiNutriFacts(BaseApiValueObject[NutriFacts, SaBase]):
    """
    A Pydantic model representing and validating the nutritional facts
    of a food item.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Each nutrient is represented by an ApiNutriValue instance that contains
    both the value and the appropriate unit for that nutrient.
    """

    calories: ApiNutriValue
    protein: ApiNutriValue
    carbohydrate: ApiNutriValue
    total_fat: ApiNutriValue
    saturated_fat: ApiNutriValue
    trans_fat: ApiNutriValue
    dietary_fiber: ApiNutriValue
    sodium: ApiNutriValue
    arachidonic_acid: ApiNutriValue
    ashes: ApiNutriValue
    dha: ApiNutriValue
    epa: ApiNutriValue
    sugar: ApiNutriValue
    starch: ApiNutriValue
    biotin: ApiNutriValue
    boro: ApiNutriValue
    caffeine: ApiNutriValue
    calcium: ApiNutriValue
    chlorine: ApiNutriValue
    copper: ApiNutriValue
    cholesterol: ApiNutriValue
    choline: ApiNutriValue
    chrome: ApiNutriValue
    dextrose: ApiNutriValue
    sulfur: ApiNutriValue
    phenylalanine: ApiNutriValue
    iron: ApiNutriValue
    insoluble_fiber: ApiNutriValue
    soluble_fiber: ApiNutriValue
    fluor: ApiNutriValue
    phosphorus: ApiNutriValue
    fructo_oligosaccharides: ApiNutriValue
    fructose: ApiNutriValue
    galacto_oligosaccharides: ApiNutriValue
    galactose: ApiNutriValue
    glucose: ApiNutriValue
    glucoronolactone: ApiNutriValue
    monounsaturated_fat: ApiNutriValue
    polyunsaturated_fat: ApiNutriValue
    guarana: ApiNutriValue
    inositol: ApiNutriValue
    inulin: ApiNutriValue
    iodine: ApiNutriValue
    l_carnitine: ApiNutriValue
    l_methionine: ApiNutriValue
    lactose: ApiNutriValue
    magnesium: ApiNutriValue
    maltose: ApiNutriValue
    manganese: ApiNutriValue
    molybdenum: ApiNutriValue
    linolenic_acid: ApiNutriValue
    linoleic_acid: ApiNutriValue
    omega_7: ApiNutriValue
    omega_9: ApiNutriValue
    oleic_acid: ApiNutriValue
    other_carbo: ApiNutriValue
    polydextrose: ApiNutriValue
    polyols: ApiNutriValue
    potassium: ApiNutriValue
    sacarose: ApiNutriValue
    selenium: ApiNutriValue
    silicon: ApiNutriValue
    sorbitol: ApiNutriValue
    sucralose: ApiNutriValue
    taurine: ApiNutriValue
    vitamin_a: ApiNutriValue
    vitamin_b1: ApiNutriValue
    vitamin_b2: ApiNutriValue
    vitamin_b3: ApiNutriValue
    vitamin_b5: ApiNutriValue
    vitamin_b6: ApiNutriValue
    folic_acid: ApiNutriValue
    vitamin_b12: ApiNutriValue
    vitamin_c: ApiNutriValue
    vitamin_d: ApiNutriValue
    vitamin_e: ApiNutriValue
    vitamin_k: ApiNutriValue
    zinc: ApiNutriValue
    retinol: ApiNutriValue
    thiamine: ApiNutriValue
    riboflavin: ApiNutriValue
    pyridoxine: ApiNutriValue
    niacin: ApiNutriValue

    @model_validator(mode="before")
    @classmethod
    def convert_to_api_nutri_value(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Convert input values to ApiNutriValue using field-specific default units.

        This general validator accesses field names to determine the appropriate
        default unit for each nutrient and converts int/float values to ApiNutriValue
        instances accordingly. It also adds missing fields with default values.

        Args:
            values: A dictionary of field names and their corresponding values

        Returns:
            A dictionary of field names and their corresponding ApiNutriValue instances

        Raises:
            ValueError: If unit is not a valid MeasureUnit or value is negative/infinite
        """
        # Get all field names from the model
        all_field_names = cls.model_fields
        default_units = NutriFacts.DEFAULT_UNITS
        result = {}

        def _validate_value(value: float, field_name: str) -> None:
            """Validate that value is within acceptable range."""
            if not (0.0 <= value <= float("inf")):
                error_message = (
                    f"Validation error.Value for field '{field_name}' "
                    f"must be between 0.0 and infinity, got: {value}"
                )
                raise ValueError(error_message)

        def _validate_unit(unit: Any, field_name: str) -> MeasureUnit:
            """Validate that unit is a valid MeasureUnit."""
            try:
                if isinstance(unit, MeasureUnit):
                    return unit
                if isinstance(unit, str):
                    return MeasureUnit(unit)
            except (ValueError, TypeError) as e:
                error_message = (
                    f"Validation error. Invalid unit for field '{field_name}': {unit}"
                )
                raise ValueError(error_message) from e
            else:
                error_message = (
                    f"Validation error. Unit for field '{field_name}' "
                    f"  must be a valid MeasureUnit, got: {unit}"
                )
                raise ValueError(error_message)

        # Process all fields (provided and missing)
        for field_name in all_field_names:
            try:
                # Handle case where values is not a dictionary
                # (e.g., string "not_an_object")
                # If values doesn't have .get() method, skip this field and continue
                value = values.get(field_name)
            except Exception:
                continue

            # Get the default unit for this field
            default_unit = default_units.get(field_name)
            if default_unit is None:
                # If no default unit mapping exists, use a fallback
                default_unit = MeasureUnit.GRAM

            if isinstance(value, int | float):
                float_value = float(value)
                _validate_value(float_value, field_name)
                result[field_name] = ApiNutriValue(value=float_value, unit=default_unit)
            elif isinstance(value, ApiNutriValue):
                # Validate existing ApiNutriValue
                _validate_value(value.value, field_name)
                result[field_name] = value
            elif isinstance(value, dict):
                if value.get("value") is not None and value.get("unit") is not None:
                    dict_value = value.get("value")
                    dict_unit = value.get("unit")
                    if isinstance(dict_value, int | float):
                        float_value = float(dict_value)
                        _validate_value(float_value, field_name)
                        validated_unit = _validate_unit(dict_unit, field_name)
                        result[field_name] = ApiNutriValue(
                            value=float_value, unit=validated_unit
                        )
                    else:
                        error_message = (
                            f"Validation error. Value for field '{field_name}' "
                            f"must be a number, got: {type(dict_value).__name__}"
                        )
                        raise ValueError(error_message)
                elif value.get("value") is not None:
                    # Use default unit if only value is provided
                    dict_value = value.get("value")
                    if isinstance(dict_value, int | float):
                        float_value = float(dict_value)
                        _validate_value(float_value, field_name)
                        result[field_name] = ApiNutriValue(
                            value=float_value, unit=default_unit
                        )
                    else:
                        error_message = (
                            f"Validation error. Value for field '{field_name}' "
                            f"must be a number, got: {type(dict_value).__name__}"
                        )
                        raise ValueError(error_message)
                elif value.get("unit") is not None:
                    # Only unit provided, validate it but use 0.0 as value
                    dict_unit = value.get("unit")
                    validated_unit = _validate_unit(dict_unit, field_name)
                    result[field_name] = ApiNutriValue(value=0.0, unit=validated_unit)
                else:
                    # Empty dict - use default values
                    result[field_name] = ApiNutriValue(value=0.0, unit=default_unit)
            elif value is None:
                # Handle None values with default
                result[field_name] = ApiNutriValue(value=0.0, unit=default_unit)
            else:
                # Reject invalid types
                error_message = (
                    f"Validation error. Invalid value for field '{field_name}': "
                    f"expected number, dict, ApiNutriValue, or None, got "
                    f"{type(value).__name__}: {value}"
                )
                raise ValueError(error_message)

        return result

    def _combine_values(
        self, value1: ApiNutriValue, value2: ApiNutriValue, operation: str
    ) -> ApiNutriValue:
        """Combine two ApiNutriValue objects using the specified operation."""
        if operation == "add":
            return value1 + value2
        if operation == "sub":
            return value1 - value2
        if operation == "mul":
            return value1 * value2
        if operation == "truediv":
            return value1 / value2
        return ApiNutriValue(value=0.0, unit=value1.unit)

    # Arithmetic operations - preserve units when available
    def __add__(self, other: "ApiNutriFacts") -> "ApiNutriFacts":
        """Add nutritional facts, preserving units when available."""
        if not isinstance(other, ApiNutriFacts):
            return NotImplemented

        kwargs = {}
        for field_name in self.__class__.model_fields:
            self_value = getattr(self, field_name)
            other_value = getattr(other, field_name)
            kwargs[field_name] = self._combine_values(self_value, other_value, "add")

        return self.__class__(**kwargs)

    def __sub__(self, other: "ApiNutriFacts") -> "ApiNutriFacts":
        """Subtract nutritional facts, preserving units when available."""
        if not isinstance(other, ApiNutriFacts):
            return NotImplemented

        kwargs = {}
        for field_name in self.__class__.model_fields:
            self_value = getattr(self, field_name)
            other_value = getattr(other, field_name)
            kwargs[field_name] = self._combine_values(self_value, other_value, "sub")

        return self.__class__(**kwargs)

    def __mul__(self, other: Union["ApiNutriFacts", float]) -> "ApiNutriFacts":
        """Multiply nutritional facts by another ApiNutriFacts or scalar."""
        if isinstance(other, float | int):
            # Scalar multiplication
            kwargs = {}
            for field_name in self.__class__.model_fields:
                self_value = getattr(self, field_name)
                kwargs[field_name] = self_value * other
            return self.__class__(**kwargs)
        if isinstance(other, ApiNutriFacts):
            # Element-wise multiplication
            kwargs = {}
            for field_name in self.__class__.model_fields:
                self_value = getattr(self, field_name)
                other_value = getattr(other, field_name)
                kwargs[field_name] = self._combine_values(
                    self_value, other_value, "mul"
                )
            return self.__class__(**kwargs)
        return NotImplemented

    def __rmul__(self, other: float) -> "ApiNutriFacts":
        """Reverse multiply - when scalar * ApiNutriFacts."""
        return self.__mul__(other)

    def __truediv__(self, other: Union["ApiNutriFacts", float]) -> "ApiNutriFacts":
        """Divide nutritional facts by another ApiNutriFacts or scalar."""
        if isinstance(other, float | int):
            if other == 0:
                error_message = "Validation error. Cannot divide by zero"
                raise ZeroDivisionError(error_message)
            # Scalar division
            kwargs = {}
            for field_name in self.__class__.model_fields:
                self_value = getattr(self, field_name)
                kwargs[field_name] = self_value / other
            return self.__class__(**kwargs)
        if isinstance(other, ApiNutriFacts):
            # Element-wise division
            kwargs = {}
            for field_name in self.__class__.model_fields:
                self_value = getattr(self, field_name)
                other_value = getattr(other, field_name)
                kwargs[field_name] = self._combine_values(
                    self_value, other_value, "truediv"
                )
            return self.__class__(**kwargs)
        return NotImplemented

    @classmethod
    def from_domain(cls, domain_obj: NutriFacts) -> "ApiNutriFacts":
        """Creates an instance of `ApiNutriFacts` from a domain model object."""
        kwargs = {}
        for name in cls.model_fields:
            value = getattr(domain_obj, name)
            if value is not None and isinstance(value, NutriValue):
                kwargs[name] = ApiNutriValue.from_domain(value)
            else:
                # If None or not a NutriValue, let the validator handle it
                kwargs[name] = value
        return cls(**kwargs)

    def to_domain(self) -> NutriFacts:
        """Converts the instance to a domain model object."""
        kwargs = {}
        for name in self.__class__.model_fields:
            value = getattr(self, name)
            # All values are now ApiNutriValue
            kwargs[name] = value.to_domain()
        return NutriFacts(**kwargs)

    @classmethod
    def from_orm_model(cls, orm_model: NutriFactsSaModel):
        """
        Can't be implemented because ORM model stores only the value.
        """
        kwargs = {}
        for name in cls.model_fields:
            value = getattr(orm_model, name)
            if value is not None:
                kwargs[name] = value
        return cls(**kwargs)

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        kwargs = {}
        for name in self.__class__.model_fields:
            value = getattr(self, name)
            # All values are now ApiNutriValue, so extract the numerical value
            kwargs[name] = value.value
        return kwargs
