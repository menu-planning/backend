from typing import Annotated, TypedDict

from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text


def validate_ingredient_full_text_length(v: str | None) -> str | None:
    """Validate that ingredient full text doesn't exceed 1000 characters."""
    if v is not None and len(v) > 1000:
        raise ValueError("Validation error: Full text must be 1000 characters or less")
    return v


IngredientName = Annotated[
    str,
    BeforeValidator(validate_optional_text),
    Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the ingredient",
    ),
]


IngredientFullText = Annotated[
    str | None,
    BeforeValidator(validate_optional_text),
    AfterValidator(validate_ingredient_full_text_length),
    Field(
        default=None,
        description="Full text of the ingredient",
    ),
]
IngredientQuantity = Annotated[float, Field(..., gt=0, le=10000)]
IngredientPosition = Annotated[int, Field(..., ge=0, le=100)]

class IngredientFields(TypedDict):
    name: IngredientName
    full_text: IngredientFullText
    quantity: IngredientQuantity
    position: IngredientPosition 