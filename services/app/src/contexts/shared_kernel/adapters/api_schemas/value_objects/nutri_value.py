from pydantic import BaseModel

from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.endpoints.pydantic_validators import \
    MyNonNegativeFloat


class ApiNutriValue(BaseModel, frozen=True):
    """
    A Pydantic model representing and validating the nutritional value
    of a food item.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes
        unit (Unit): The unit of measurement for the nutritional value.
            This is an instance of the `Unit` Enum class defined in the
            codebase.
        value (MyNonNegativeFloat): The nutritional value, which must be a
            non-negative float. Defaults to 0.0.
    """

    unit: MeasureUnit
    value: MyNonNegativeFloat = 0.0
    unit: MeasureUnit
    value: MyNonNegativeFloat = 0.0
