from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.fields import trim_whitespace


IngredientName = Annotated[
    str,
    BeforeValidator(trim_whitespace),
    Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the ingredient",
    ),
    AfterValidator(trim_whitespace),
]
IngredientFullText = Annotated[
    str | None,
    BeforeValidator(lambda v: trim_whitespace(v, value_if_none="##")),
    Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Full text of the ingredient",
    ),
    AfterValidator(lambda v: None if v == "##" else trim_whitespace(v, value_if_none=None)),
]
IngredientQuantity = Annotated[float, Field(..., gt=0, le=10000)]
IngredientPosition = Annotated[int, Field(..., ge=0, le=100)] 