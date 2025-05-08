from typing import Optional

from pydantic import BaseModel, field_validator
from decimal import Decimal

from src.contexts.products_catalog.shared.domain.value_objects.yield_rate import YieldRate


class ApiYieldRate(BaseModel):
    """
    A Pydantic model representing and validating the edible yield rate of a product.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        factor (Decimal): Fraction of the product that is usable (0 < factor <= 1).
    """

    factor: Decimal

    @field_validator("factor")
    def check_factor_range(cls, value: Decimal) -> Decimal:
        if not (Decimal("0") < value <= Decimal("1")):
            raise ValueError("YieldRate factor must be > 0 and <= 1")
        return value

    @classmethod
    def from_domain(cls, domain_obj: YieldRate | None) -> Optional["ApiYieldRate"]:
        """Creates an instance of `ApiYieldRate` from a domain model object."""
        if domain_obj is None:
            return None
        try:
            return cls(factor=domain_obj.factor)
        except Exception as e:
            raise ValueError(f"Failed to build ApiYieldRate from domain instance: {e}")

    def to_domain(self) -> YieldRate:
        """Converts the instance to a domain model object."""
        try:
            # model_dump() returns a dict of field values
            return YieldRate(factor=self.factor)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiYieldRate to domain model: {e}")
