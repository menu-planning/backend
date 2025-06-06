from datetime import time
from typing import Annotated, Any

from pydantic import BeforeValidator, Field

# Rating fields
def _rating_range(v: Any):
    if v is None or v not in range(0, 6):
        raise ValueError(f"Ranting must be an int from 0 to 5: {v}")
    return v


RatingValue = Annotated[int, BeforeValidator(_rating_range)]


def _average_rating_range(v: Any):
    if v is None or v < 0 or v > 5:
        raise ValueError(f"Ranting must be an float from 0 to 5: {v}")
    return v


AverageRatingValue = Annotated[float | None, BeforeValidator(_average_rating_range)]

# Menu meal fields
WeekNumber = Annotated[int, Field(..., ge=1)]
Weekday = Annotated[str, Field(..., min_length=1)]
MealType = Annotated[str, Field(..., min_length=1)]
MealTime = Annotated[time | None, Field(default=None)]

# Ingredient fields
IngredientName = Annotated[str, Field(..., min_length=1)]
IngredientQuantity = Annotated[float, Field(..., ge=0)]
IngredientPosition = Annotated[int, Field(..., ge=0)]