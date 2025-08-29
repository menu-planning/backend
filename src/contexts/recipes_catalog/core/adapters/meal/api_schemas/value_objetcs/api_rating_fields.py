from typing import Annotated

from pydantic import AfterValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    SanitizedTextOptional,
)
from src.contexts.seedwork.shared.adapters.api_schemas.validators import (
    validate_optional_text_length,
    validate_rating_range,
)

RatingValue = Annotated[int, AfterValidator(validate_rating_range)]

AverageRatingValue = Annotated[float, AfterValidator(validate_rating_range)]

RatingTasteRequired = Annotated[
    int,
    AfterValidator(validate_rating_range),
    Field(
        description="Rating for the taste of the recipe (0-5)",
    ),
]

RatingConvenienceRequired = Annotated[
    int,
    AfterValidator(validate_rating_range),
    Field(
        description="Rating for the convenience of preparing the recipe (0-5)",
    ),
]

RatingCommentOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Comment of the rating"),
    AfterValidator(
        lambda v: validate_optional_text_length(
            v, 1000, "Comment must be 1000 characters or less"
        )
    ),
]
