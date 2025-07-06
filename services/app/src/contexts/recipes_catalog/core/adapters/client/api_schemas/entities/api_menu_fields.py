from __future__ import annotations

from typing import Annotated

from pydantic import BeforeValidator, Field


from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text

# Required string fields with validation
MenuName = Annotated[
    str,
    BeforeValidator(validate_optional_text),
    Field(
        ...,
        min_length=1,
        description="Name of the menu",
    ),
]

# Optional string fields
MenuDescription = Annotated[
    str | None,
    Field(None, description="Description of the menu"),
]

MenuNotes = Annotated[
    str | None,
    Field(None, description="Additional notes about the menu"),
]

# Collection fields
MenuMeals = Annotated[
    'frozenset[ApiMenuMeal]',  # type: ignore # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="Set of meals on the menu"),
]

MenuTags = Annotated[
    'frozenset[ApiTag]',  # type: ignore # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="Set of tags associated with the menu"),
]

