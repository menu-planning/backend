"""API value object for a complete set of nutritional facts.

Provides validation, normalization, arithmetic operations, and conversions to
and from domain and ORM representations. Each field is an `ApiNutriValue` that
encapsulates a numeric value and its measurement unit.
"""

from typing import Any, Union

from pydantic import Field, model_validator
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import (
    ApiNutriValue,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
    NutriFactsSaModel,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.db.base import SaBase


def default_nutri_value() -> ApiNutriValue:
    return ApiNutriValue(value=0.0, unit=MeasureUnit.ENERGY)


class ApiNutriFacts(BaseApiValueObject[NutriFacts, SaBase]):
    """API schema for nutritional facts operations.

    Attributes:
        calories: Caloric content with unit.
        protein: Protein content with unit.
        carbohydrate: Carbohydrate content with unit.
        total_fat: Total fat content with unit.
        saturated_fat: Saturated fat content with unit.
        trans_fat: Trans fat content with unit.
        dietary_fiber: Dietary fiber content with unit.
        sodium: Sodium content with unit.
        arachidonic_acid: Arachidonic acid content with unit.
        ashes: Ash content with unit.
        dha: DHA content with unit.
        epa: EPA content with unit.
        sugar: Sugar content with unit.
        starch: Starch content with unit.
        biotin: Biotin content with unit.
        boro: Boron content with unit.
        caffeine: Caffeine content with unit.
        calcium: Calcium content with unit.
        chlorine: Chlorine content with unit.
        copper: Copper content with unit.
        cholesterol: Cholesterol content with unit.
        choline: Choline content with unit.
        chrome: Chromium content with unit.
        dextrose: Dextrose content with unit.
        sulfur: Sulfur content with unit.
        phenylalanine: Phenylalanine content with unit.
        iron: Iron content with unit.
        insoluble_fiber: Insoluble fiber content with unit.
        soluble_fiber: Soluble fiber content with unit.
        fluor: Fluoride content with unit.
        phosphorus: Phosphorus content with unit.
        fructo_oligosaccharides: Fructo-oligosaccharides content with unit.
        fructose: Fructose content with unit.
        galacto_oligosaccharides: Galacto-oligosaccharides content with unit.
        galactose: Galactose content with unit.
        glucose: Glucose content with unit.
        glucoronolactone: Glucuronolactone content with unit.
        monounsaturated_fat: Monounsaturated fat content with unit.
        polyunsaturated_fat: Polyunsaturated fat content with unit.
        guarana: Guarana content with unit.
        inositol: Inositol content with unit.
        inulin: Inulin content with unit.
        iodine: Iodine content with unit.
        l_carnitine: L-carnitine content with unit.
        l_methionine: L-methionine content with unit.
        lactose: Lactose content with unit.
        magnesium: Magnesium content with unit.
        maltose: Maltose content with unit.
        manganese: Manganese content with unit.
        molybdenum: Molybdenum content with unit.
        linolenic_acid: Linolenic acid content with unit.
        linoleic_acid: Linoleic acid content with unit.
        omega_7: Omega-7 content with unit.
        omega_9: Omega-9 content with unit.
        oleic_acid: Oleic acid content with unit.
        other_carbo: Other carbohydrates content with unit.
        polydextrose: Polydextrose content with unit.
        polyols: Polyols content with unit.
        potassium: Potassium content with unit.
        sacarose: Sucrose content with unit.
        selenium: Selenium content with unit.
        silicon: Silicon content with unit.
        sorbitol: Sorbitol content with unit.
        sucralose: Sucralose content with unit.
        taurine: Taurine content with unit.
        vitamin_a: Vitamin A content with unit.
        vitamin_b1: Vitamin B1 content with unit.
        vitamin_b2: Vitamin B2 content with unit.
        vitamin_b3: Vitamin B3 content with unit.
        vitamin_b5: Vitamin B5 content with unit.
        vitamin_b6: Vitamin B6 content with unit.
        folic_acid: Folic acid content with unit.

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        Each field is an ApiNutriValue that encapsulates a numeric value and its measurement unit.
        Provides validation, normalization, and arithmetic operations.
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
        """Normalize inputs to `ApiNutriValue` using sensible default units.

        For each field, infer a default unit, accept numbers, dicts, or
        existing `ApiNutriValue` instances, and return a complete mapping of
        field names to `ApiNutriValue`. Missing fields are populated with
        defaults.

        Args:
            values: Mapping of field names to incoming values.

        Returns:
            Mapping of field names to `ApiNutriValue` instances.

        Raises:
            ValidationConversionError: On invalid units, non-numeric values, or out-of-range
                numbers.
        """
        all_field_names = cls.model_fields
        default_units = (
            NutriFacts.default_units if hasattr(NutriFacts, "default_units") else {}
        )
        result = {}

        def _validate_value(value: float, field_name: str) -> None:
            """Validate numeric bounds for a nutrition field value."""
            if not (0.0 <= value <= float("inf")):
                raise ValidationConversionError(
                    message=f"Value for field '{field_name}' must be between 0.0 and infinity, got: {value}",
                    schema_class=cls,
                    conversion_direction="field_validation",
                    source_data=value,
                    validation_errors=[
                        f"Value {value} is outside valid range [0.0, infinity)"
                    ],
                )

        def _validate_unit(unit: Any, field_name: str) -> MeasureUnit:
            """Return a valid `MeasureUnit` from input or raise ValidationConversionError."""
            try:
                if isinstance(unit, MeasureUnit):
                    return unit
                if isinstance(unit, str):
                    return MeasureUnit(unit)
            except (ValueError, TypeError) as e:
                raise ValidationConversionError(
                    message=f"Invalid unit for field '{field_name}': {unit}",
                    schema_class=cls,
                    conversion_direction="field_validation",
                    source_data=unit,
                    validation_errors=[f"Invalid unit format: {unit}"],
                ) from e
            else:
                raise ValidationConversionError(
                    message=f"Unit for field '{field_name}' must be a valid MeasureUnit, got: {unit}",
                    schema_class=cls,
                    conversion_direction="field_validation",
                    source_data=unit,
                    validation_errors=[
                        f"Expected MeasureUnit, got {type(unit).__name__}"
                    ],
                )

        for field_name in all_field_names:
            try:
                value = values.get(field_name)
            except Exception:
                continue

            default_unit = (
                default_units.get(field_name)
                if isinstance(default_units, dict)
                else None
            )
            if default_unit is None:
                default_unit = MeasureUnit.GRAM

            if isinstance(value, int | float):
                float_value = float(value)
                _validate_value(float_value, field_name)
                result[field_name] = ApiNutriValue(value=float_value, unit=default_unit)
            elif isinstance(value, ApiNutriValue):
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
                        raise ValidationConversionError(
                            message=f"Value for field '{field_name}' must be a number, got: {type(dict_value).__name__}",
                            schema_class=cls,
                            conversion_direction="field_validation",
                            source_data=dict_value,
                            validation_errors=[
                                f"Expected number, got {type(dict_value).__name__}"
                            ],
                        )
                elif value.get("value") is not None:
                    dict_value = value.get("value")
                    if isinstance(dict_value, int | float):
                        float_value = float(dict_value)
                        _validate_value(float_value, field_name)
                        result[field_name] = ApiNutriValue(
                            value=float_value, unit=default_unit
                        )
                    else:
                        raise ValidationConversionError(
                            message=f"Value for field '{field_name}' must be a number, got: {type(dict_value).__name__}",
                            schema_class=cls,
                            conversion_direction="field_validation",
                            source_data=dict_value,
                            validation_errors=[
                                f"Expected number, got {type(dict_value).__name__}"
                            ],
                        )
                elif value.get("unit") is not None:
                    dict_unit = value.get("unit")
                    validated_unit = _validate_unit(dict_unit, field_name)
                    result[field_name] = ApiNutriValue(value=0.0, unit=validated_unit)
                else:
                    result[field_name] = ApiNutriValue(value=0.0, unit=default_unit)
            elif value is None:
                result[field_name] = ApiNutriValue(value=0.0, unit=default_unit)
            else:
                raise ValidationConversionError(
                    message=f"Invalid value for field '{field_name}': expected number, dict, ApiNutriValue, or None, got {type(value).__name__}: {value}",
                    schema_class=cls,
                    conversion_direction="field_validation",
                    source_data=value,
                    validation_errors=[
                        f"Expected number, dict, ApiNutriValue, or None, got {type(value).__name__}"
                    ],
                )

        return result

    def _combine_values(
        self, value1: ApiNutriValue, value2: ApiNutriValue, operation: str
    ) -> ApiNutriValue:
        """Combine two values using an arithmetic operation.

        Args:
            value1: Left operand.
            value2: Right operand.
            operation: One of "add", "sub", "mul", or "truediv".

        Returns:
            Resulting `ApiNutriValue`.
        """
        if operation == "add":
            return value1 + value2
        if operation == "sub":
            return value1 - value2
        if operation == "mul":
            return value1 * value2
        if operation == "truediv":
            return value1 / value2
        return ApiNutriValue(value=0.0, unit=value1.unit)

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
            kwargs = {}
            for field_name in self.__class__.model_fields:
                self_value = getattr(self, field_name)
                kwargs[field_name] = self_value * other
            return self.__class__(**kwargs)
        if isinstance(other, ApiNutriFacts):
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
                raise ValidationConversionError(
                    message="Cannot divide by zero",
                    schema_class=self.__class__,
                    conversion_direction="arithmetic_operation",
                    source_data={"divisor": other, "operation": "division"},
                    validation_errors=["Division by zero is not allowed"],
                )
            kwargs = {}
            for field_name in self.__class__.model_fields:
                self_value = getattr(self, field_name)
                kwargs[field_name] = self_value / other
            return self.__class__(**kwargs)
        if isinstance(other, ApiNutriFacts):
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
        """Create an instance from a domain model.

        Args:
            domain_obj: Source domain model.

        Returns:
            ApiNutriFacts instance.
        """
        kwargs = {}
        for name in cls.model_fields:
            value = getattr(domain_obj, name)
            if value is not None and isinstance(value, NutriValue):
                kwargs[name] = ApiNutriValue.from_domain(value)
            else:
                kwargs[name] = value
        return cls(**kwargs)

    def to_domain(self) -> NutriFacts:
        """Convert this value object into a domain model.

        Returns:
            NutriFacts domain model.
        """
        kwargs = {}
        for name in self.__class__.model_fields:
            value = getattr(self, name)
            kwargs[name] = value.to_domain()
        return NutriFacts(**kwargs)

    @classmethod
    def from_orm_model(cls, orm_model: NutriFactsSaModel):
        """Create an instance from an ORM model that stores numeric values.

        Args:
            orm_model: ORM instance with per-field numeric values.

        Returns:
            ApiNutriFacts instance with numbers to be normalized by validator.
        """
        kwargs = {}
        for name in cls.model_fields:
            value = getattr(orm_model, name)
            if value is not None:
                kwargs[name] = value
        return cls(**kwargs)

    def to_orm_kwargs(self) -> dict:
        """Return kwargs suitable for constructing/updating an ORM model.

        Returns:
            Mapping of field names to raw numeric values.
        """
        kwargs = {}
        for name in self.__class__.model_fields:
            value = getattr(self, name)
            kwargs[name] = value.value
        return kwargs
