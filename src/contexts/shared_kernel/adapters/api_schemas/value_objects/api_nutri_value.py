from typing import Any, Union

from pydantic import NonNegativeFloat

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.db.base import SaBase


class ApiNutriValue(BaseApiValueObject[NutriValue, SaBase]):
    """
    A Pydantic model representing and validating the nutritional value
    of a food item.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes
        unit (Unit): The unit of measurement for the nutritional value.
            This is an instance of the `Unit` Enum class defined in the
            codebase.
        value (MyNullableNonNegativeFloat): The nutritional value, which must be a
            non-negative float or None. Defaults to None.
    """

    unit: MeasureUnit
    value: NonNegativeFloat

    def _create_new_instance(self, value: float) -> "ApiNutriValue":
        """Helper method to create a new instance with the same unit."""
        return ApiNutriValue(unit=MeasureUnit(self.unit), value=value)

    def _check_zero_division(self, divisor: float, operation_name: str = "operation"):
        """Helper method to check for division by zero."""
        if divisor == 0:
            error_message = f"Cannot {operation_name} by zero"
            raise ZeroDivisionError(error_message)

    # Arithmetic operations - preserve unit from ApiNutriValue operand
    def __add__(self, other: Union["ApiNutriValue", float]) -> "ApiNutriValue":
        """Add values, preserving the unit from the ApiNutriValue operand."""
        if isinstance(other, ApiNutriValue):
            return self._create_new_instance(self.value + other.value)
        return self._create_new_instance(self.value + other)

    def __radd__(self, other: float) -> "ApiNutriValue":
        """Reverse add - when float/int + ApiNutriValue."""
        return self._create_new_instance(other + self.value)

    def __sub__(self, other: Union["ApiNutriValue", float]) -> "ApiNutriValue":
        """Subtract values, preserving the unit from the ApiNutriValue operand."""
        if isinstance(other, ApiNutriValue):
            return self._create_new_instance(self.value - other.value)
        return self._create_new_instance(self.value - other)

    def __rsub__(self, other: float) -> "ApiNutriValue":
        """Reverse subtract - when float/int - ApiNutriValue."""
        return self._create_new_instance(other - self.value)

    def __mul__(self, other: Union["ApiNutriValue", float]) -> "ApiNutriValue":
        """Multiply values, preserving the unit from the ApiNutriValue operand."""
        if isinstance(other, ApiNutriValue):
            return self._create_new_instance(self.value * other.value)
        return self._create_new_instance(self.value * other)

    def __rmul__(self, other: float) -> "ApiNutriValue":
        """Reverse multiply - when float/int * ApiNutriValue."""
        return self._create_new_instance(other * self.value)

    def __truediv__(self, other: Union["ApiNutriValue", float]) -> "ApiNutriValue":
        """Divide values, preserving the unit from the ApiNutriValue operand."""
        if isinstance(other, ApiNutriValue):
            self._check_zero_division(other.value, "divide")
            return self._create_new_instance(self.value / other.value)
        self._check_zero_division(other, "divide")
        return self._create_new_instance(self.value / other)

    def __rtruediv__(self, other: float) -> "ApiNutriValue":
        """Reverse divide - when float/int / ApiNutriValue."""
        self._check_zero_division(self.value, "divide")
        return self._create_new_instance(other / self.value)

    def __floordiv__(self, other: Union["ApiNutriValue", float]) -> "ApiNutriValue":
        """Floor divide values, preserving the unit from the ApiNutriValue operand."""
        if isinstance(other, ApiNutriValue):
            self._check_zero_division(other.value, "floor divide")
            return self._create_new_instance(self.value // other.value)
        self._check_zero_division(other, "floor divide")
        return self._create_new_instance(self.value // other)

    def __rfloordiv__(self, other: float) -> "ApiNutriValue":
        """Reverse floor divide - when float/int // ApiNutriValue."""
        self._check_zero_division(self.value, "floor divide")
        return self._create_new_instance(other // self.value)

    def __mod__(self, other: Union["ApiNutriValue", float]) -> "ApiNutriValue":
        """Modulo operation, preserving the unit from the ApiNutriValue operand."""
        if isinstance(other, ApiNutriValue):
            self._check_zero_division(other.value, "modulo")
            return self._create_new_instance(self.value % other.value)
        self._check_zero_division(other, "modulo")
        return self._create_new_instance(self.value % other)

    def __rmod__(self, other: float) -> "ApiNutriValue":
        """Reverse modulo - when float/int % ApiNutriValue."""
        self._check_zero_division(self.value, "modulo")
        return self._create_new_instance(other % self.value)

    def __pow__(self, other: Union["ApiNutriValue", float]) -> "ApiNutriValue":
        """Power operation, preserving the unit from the ApiNutriValue operand."""
        if isinstance(other, ApiNutriValue):
            return self._create_new_instance(self.value**other.value)
        return self._create_new_instance(self.value**other)

    def __rpow__(self, other: float) -> "ApiNutriValue":
        """Reverse power - when float/int ** ApiNutriValue."""
        return self._create_new_instance(other**self.value)

    # Unary operations
    def __neg__(self) -> "ApiNutriValue":
        """Negate the value while preserving the unit."""
        return self._create_new_instance(-self.value)

    def __pos__(self) -> "ApiNutriValue":
        """Positive value (no change) while preserving the unit."""
        return self._create_new_instance(+self.value)

    def __abs__(self) -> "ApiNutriValue":
        """Absolute value while preserving the unit."""
        return self._create_new_instance(abs(self.value))

    # Conversion methods for better integration
    def __float__(self) -> float:
        """Convert to float (returns only the numerical value)."""
        return float(self.value)

    def __int__(self) -> int:
        """Convert to int (returns only the numerical value)."""
        return int(self.value)

    @classmethod
    def from_domain(cls, domain_obj: NutriValue) -> "ApiNutriValue":
        """Creates an instance of `ApiNutriValue` from a domain model object."""
        return cls(
            unit=domain_obj.unit,
            value=domain_obj.value,
        )

    def to_domain(self) -> NutriValue:
        """Converts the instance to a domain model object."""
        return NutriValue(
            unit=MeasureUnit(self.unit),
            value=self.value,
        )

    @classmethod
    def from_orm_model(cls, orm_model: Any):
        """
        Can't be implemented because ORM model stores only the value.
        """
        super().from_orm_model(orm_model)

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        return self.model_dump(exclude={"unit"})
