from datetime import time
from typing import Annotated

from pydantic import BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import remove_whitespace_and_empty_str

MealNameRequired = Annotated[
    str,
    BeforeValidator(remove_whitespace_and_empty_str),
    Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the meal",
    ),
]

WeekNumberRequired = Annotated[int, Field(..., ge=1, le=10)]
WeekdayRequired = Annotated[
    str,
    BeforeValidator(remove_whitespace_and_empty_str),
    Field(...,description="Weekday name", min_length=1, max_length=50),
]
MealTypeRequired = Annotated[
    str, 
    BeforeValidator(remove_whitespace_and_empty_str),
    Field(...,description="Meal type", min_length=1, max_length=50),
]
MealTimeOptional = Annotated[time | None, Field(default=None)]