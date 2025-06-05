from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseValueObject
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.endpoints.pydantic_validators import MyNullableNonNegativeFloat
from src.db.base import SaBase


class ApiNutriValue(BaseValueObject[NutriValue, SaBase]):
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

    unit: MeasureUnit | None = None
    value: MyNullableNonNegativeFloat | None = None

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
            unit=MeasureUnit(self.unit) if self.unit is not None else None,
            value=self.value,
        )

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        return self.model_dump(exclude={'unit'})

