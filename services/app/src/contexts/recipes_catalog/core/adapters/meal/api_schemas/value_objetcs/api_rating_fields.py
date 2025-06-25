from typing import Annotated, Any, TypedDict

from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text

def _rating_range(v: int):
    if v not in range(0, 6):
        raise ValueError(f"Rating must be an int from 0 to 5: {v}")
    return v


RatingValue = Annotated[int, AfterValidator(_rating_range)]

AverageRatingValue = Annotated[float, AfterValidator(_rating_range)] 

RatingTaste = Annotated[
    int,
    AfterValidator(_rating_range),
    Field(
        description="Rating for the taste of the recipe (0-5)",
    ),
]

RatingConvenience = Annotated[
    int,
    AfterValidator(_rating_range),
    Field(
        description="Rating for the convenience of preparing the recipe (0-5)",
    ),
]

RatingComment = Annotated[
    str | None,
    BeforeValidator(validate_optional_text),
    Field(
        default=None,
        max_length=1000,
        description="Comment about the rating",
    ),
]

class RatingFields(TypedDict):
    taste: RatingTaste
    convenience: RatingConvenience
    comment: RatingComment 