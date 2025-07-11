from typing import Annotated, TypedDict

from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import remove_whitespace_and_empty_str


def validate_ingredient_full_text_length(v: str | None) -> str | None:
    """Validate that ingredient full text doesn't exceed 1000 characters."""
    if v is not None and len(v) > 1000:
        raise ValueError("Validation error: Full text must be 1000 characters or less")
    return v


IngredientNameRequired = Annotated[
    str,
    BeforeValidator(remove_whitespace_and_empty_str),
    Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the ingredient",
    ),
]


IngredientFullTextOptional = Annotated[
    str | None,
    BeforeValidator(remove_whitespace_and_empty_str),
    AfterValidator(validate_ingredient_full_text_length),
    Field(
        default=None,
        description="Full text of the ingredient",
    ),
]
IngredientQuantityRequired = Annotated[float, Field(..., gt=0, le=10000)]
IngredientPositionRequired = Annotated[int, Field(..., ge=0, le=100)]