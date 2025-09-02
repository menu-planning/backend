"""API value object for nutritional values with arithmetic helpers."""

from typing import Any, Union

from pydantic import NonNegativeFloat
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.db.base import SaBase


class ApiNutriValue(BaseApiValueObject[NutriValue, SaBase]):
    """API schema for nutritional value operations.

    Attributes:
        unit: Measurement unit for the nutritional value.
        value: Non-negative numerical value.

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        Provides arithmetic operations that preserve the measurement unit.
        Validates inputs and includes helpers to convert to/from domain models.
    """

    unit: MeasureUnit
    value: NonNegativeFloat

    def _create_new_instance(self, value: float) -> "ApiNutriValue":
        """Create a new instance preserving the current unit.

        Args:
            value: Numerical value for the new instance.

        Returns:
            A new `ApiNutriValue` with the same unit.
        """
        return ApiNutriValue(unit=MeasureUnit(self.unit), value=value)

    def _check_zero_division(self, divisor: float, operation_name: str = "operation"):
        """Validate divisor to prevent division by zero.

        Args:
            divisor: Divisor value to check.
            operation_name: Operation name used in error messages.

        Raises:
            ValidationConversionError: If ``divisor`` equals zero.
        """
        if divisor == 0:
            raise ValidationConversionError(
                message=f"Cannot {operation_name} by zero",
                schema_class=self.__class__,
                conversion_direction="arithmetic_operation",
                source_data={"divisor": divisor, "operation": operation_name},
                validation_errors=["Division by zero is not allowed"]
            )

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

    def __neg__(self) -> "ApiNutriValue":
        """Negate the value while preserving the unit."""
        return self._create_new_instance(-self.value)

    def __pos__(self) -> "ApiNutriValue":
        """Positive value (no change) while preserving the unit."""
        return self._create_new_instance(+self.value)

    def __abs__(self) -> "ApiNutriValue":
        """Absolute value while preserving the unit."""
        return self._create_new_instance(abs(self.value))

    def __float__(self) -> float:
        """Convert to float (returns only the numerical value)."""
        return float(self.value)

    def __int__(self) -> int:
        """Convert to int (returns only the numerical value)."""
        return int(self.value)

    @classmethod
    def from_domain(cls, domain_obj: NutriValue) -> "ApiNutriValue":
        """Create an instance from a domain model.

        Args:
            domain_obj: Source domain model.

        Returns:
            ApiNutriValue instance.
        """
        return cls(
            unit=domain_obj.unit,
            value=domain_obj.value,
        )

    def to_domain(self) -> NutriValue:
        """Convert this value object into a domain model.

        Returns:
            NutriValue domain model.
        """
        return NutriValue(
            unit=MeasureUnit(self.unit),
            value=self.value,
        )

    @classmethod
    def from_orm_model(cls, orm_model: Any):
        """Not implemented; ORM model stores only the numerical value.

        Defers to the base class behavior.
        """
        super().from_orm_model(orm_model)

    def to_orm_kwargs(self) -> dict:
        """Return kwargs suitable for constructing/updating an ORM model.

        Returns:
            Mapping excluding the unit (only the numerical value is stored).
        """
        return self.model_dump(exclude={"unit"})
