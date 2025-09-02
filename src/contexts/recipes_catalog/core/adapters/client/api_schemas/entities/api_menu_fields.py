from typing import Annotated

from pydantic import AfterValidator, Field
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.value_objects.api_menu_meal import (
    ApiMenuMeal,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedText,
    SanitizedTextOptional,
)
from src.contexts.seedwork.adapters.api_schemas.validators import (
    validate_optional_text_length,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)

# Required string fields with validation
MenuNameRequired = Annotated[
    SanitizedText,
    Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Name of the recipe",
    ),
]

# Optional string fields
MenuDescriptionOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Description of the menu"),
    AfterValidator(lambda v: validate_optional_text_length(v, 10000, "Description must be less than 10000 characters")),
]

MenuNotesOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Notes of the menu"),
    AfterValidator(lambda v: validate_optional_text_length(v, 10000, "Notes must be less than 10000 characters")),
]

# Collection fields
MenuMealsOptional = Annotated[
    frozenset[ApiMenuMeal] | None,
    Field(default_factory=frozenset, description="Set of meals on the menu"),
]

MenuTagsOptional = Annotated[
    frozenset[ApiTag] | None,
    Field(default_factory=frozenset, description="Set of tags associated with the menu"),
]

