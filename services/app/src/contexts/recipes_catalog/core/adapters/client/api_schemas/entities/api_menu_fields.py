from typing import Annotated

from pydantic import BeforeValidator, Field


from src.contexts.recipes_catalog.core.adapters.client.api_schemas.value_objects.api_menu_meal import ApiMenuMeal
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import remove_whitespace_and_empty_str
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag

# Required string fields with validation
MenuNameRequired = Annotated[
    str,
    BeforeValidator(remove_whitespace_and_empty_str),
    Field(
        ...,
        min_length=1,
        description="Name of the menu",
    ),
]

# Optional string fields
MenuDescriptionOptional = Annotated[
    str | None,
    Field(None, description="Description of the menu"),
]

MenuNotesOptional = Annotated[
    str | None,
    Field(None, description="Additional notes about the menu"),
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

