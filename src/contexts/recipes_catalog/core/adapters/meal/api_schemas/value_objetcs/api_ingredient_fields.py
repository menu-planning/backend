from typing import Annotated

from pydantic import AfterValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    SanitizedText,
    SanitizedTextOptional,
)
from src.contexts.seedwork.shared.adapters.api_schemas.validators import (
    validate_optional_text_length,
)

IngredientNameRequired = Annotated[
    SanitizedText,
    Field(
        ...,
        max_length=255,
        description="Name of the ingredient",
    ),
]


IngredientFullTextOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Full text of the ingredient"),
    AfterValidator(
        lambda v: validate_optional_text_length(
            v, 1000, "Full text must be 1000 characters or less"
        )
    ),
]
IngredientQuantityRequired = Annotated[float, Field(..., gt=0, le=10000)]
IngredientPositionRequired = Annotated[int, Field(..., ge=0, le=100)]
