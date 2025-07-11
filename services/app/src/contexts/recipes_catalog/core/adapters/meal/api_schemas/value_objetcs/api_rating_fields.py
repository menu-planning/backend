from typing import Annotated, Any, TypedDict

from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import remove_whitespace_and_empty_str

def _rating_range(v: int):
    if v not in range(0, 6):
        raise ValueError(f"Validation error: Rating must be an int from 0 to 5: {v}")
    return v


RatingValue = Annotated[int, AfterValidator(_rating_range)]

AverageRatingValue = Annotated[float, AfterValidator(_rating_range)] 

RatingTasteRequired = Annotated[
    int,
    AfterValidator(_rating_range),
    Field(
        description="Rating for the taste of the recipe (0-5)",
    ),
]

RatingConvenienceRequired = Annotated[
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


RatingCommentOptional = Annotated[
    str | None,
    BeforeValidator(remove_whitespace_and_empty_str),
    AfterValidator(validate_rating_comment_length),
    Field(
        default=None,
        description="Comment about the rating",
    ),
]