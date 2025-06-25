from datetime import time
from typing import Annotated, TypedDict

from pydantic import BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text

MealName = Annotated[
    str,
    BeforeValidator(validate_optional_text),
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
    BeforeValidator(validate_optional_text),
    Field(...,description="Weekday name", min_length=1, max_length=50),
]
MealType = Annotated[
    str, 
    BeforeValidator(validate_optional_text),
    Field(...,description="Meal type", min_length=1, max_length=50),
]
MealTime = Annotated[time | None, Field(default=None)]

class MenuFields(TypedDict):
    name: MealName
    week_number: WeekNumber
    weekday: Weekday
    meal_type: MealType
    meal_time: MealTime 