from typing import Annotated, Any, TypedDict

from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text

def _rating_range(v: int):
    if v not in range(0, 6):
        raise ValueError(f"Validation error: Rating must be an int from 0 to 5: {v}")
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

def validate_rating_comment_length(v: str | None) -> str | None:
    """Validate that rating comment doesn't exceed 1000 characters."""
    if v is not None and len(v) > 1000:
        raise ValueError("Comment must be 1000 characters or less")
    return v


RatingComment = Annotated[
    str | None,
    BeforeValidator(validate_optional_text),
    AfterValidator(validate_rating_comment_length),
    Field(
        default=None,
        description="Comment about the rating",
    ),
]

class RatingFields(TypedDict):
    taste: RatingTaste
    convenience: RatingConvenience
    comment: RatingComment 