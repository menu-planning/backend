from datetime import time
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.fields import trim_whitespace

MealName = Annotated[
    str,
    BeforeValidator(trim_whitespace),
    Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the meal",
    ),
]

WeekNumber = Annotated[int, Field(..., ge=1, le=10)]
Weekday = Annotated[
    str,
    BeforeValidator(trim_whitespace),
    Field(...,description="Weekday name", min_length=1, max_length=50),
]
MealType = Annotated[
    str, 
    BeforeValidator(trim_whitespace),
    Field(...,description="Meal type", min_length=1, max_length=50),
]
MealTime = Annotated[time | None, Field(default=None)] 