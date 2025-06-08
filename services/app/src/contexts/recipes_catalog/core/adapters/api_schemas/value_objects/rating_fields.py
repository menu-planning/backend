from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.fields import trim_whitespace

def _rating_range(v: int):
    if v not in range(0, 6):
        raise ValueError(f"Rating must be an int from 0 to 5: {v}")
    return v


RatingValue = Annotated[int, AfterValidator(_rating_range)]

AverageRatingValue = Annotated[float, AfterValidator(_rating_range)] 

RatingComment = Annotated[
    str | None,
    BeforeValidator(lambda v: trim_whitespace(v, value_if_none="##")),
    Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Name of the meal",
    ),
    AfterValidator(lambda v: None if v == "##" else v),
] 