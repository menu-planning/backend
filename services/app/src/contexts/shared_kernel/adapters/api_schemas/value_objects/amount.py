from pydantic import BaseModel, field_serializer
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects import Amount
from src.contexts.shared_kernel.endpoints.pydantic_validators import MyNonNegativeFloat


class ApiAmount(BaseModel):
    quantity: MyNonNegativeFloat
    unit: MeasureUnit

    @field_serializer("unit")
    def serialize_unit(self, unit: MeasureUnit, _info):
        """Serializes the unit to a domain model."""
        return unit.value

    @classmethod
    def from_domain(cls, domain_obj: Amount) -> "ApiAmount":
        return cls(quantity=domain_obj.quantity, unit=MeasureUnit(domain_obj.unit))

    def to_domain(self) -> Amount:
        return Amount(quantity=self.quantity, unit=self.unit.value)
