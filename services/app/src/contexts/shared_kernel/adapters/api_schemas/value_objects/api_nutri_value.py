from typing import Any
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.db.base import SaBase
from pydantic import NonNegativeFloat


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
        return self.model_dump(exclude={'unit'})
    

