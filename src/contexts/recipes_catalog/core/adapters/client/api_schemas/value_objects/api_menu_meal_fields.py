from datetime import time
from typing import Annotated

from pydantic import Field
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    SanitizedText,
)
from src.contexts.shared_kernel.domain.enums import Weekday

MealNameRequired = Annotated[
    SanitizedText,
    Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the meal",
    ),
]

WeekNumberRequired = Annotated[int, Field(..., ge=1, le=10)]
WeekdayRequired = Annotated[
    Weekday,
    Field(...,description="Weekday name"),
]
MealTypeRequired = Annotated[
    SanitizedText,
    Field(...,description="Meal type", min_length=1, max_length=50),
]
MealTimeOptional = Annotated[time | None, Field(default=None, description="Time of the meal")]
