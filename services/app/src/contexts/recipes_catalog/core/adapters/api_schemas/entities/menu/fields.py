from typing import Annotated, TYPE_CHECKING
from pydantic import Field

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.menu_meal import ApiMenuMeal
    from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag

# Required string fields with validation
MenuName = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        description="Name of the menu",
        pattern=r"^\S.*\S$",  # Ensures non-empty string with no leading/trailing whitespace
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
    "set[ApiMenuMeal]",  # Forward reference to avoid circular import
    Field(default_factory=set, description="Set of meals on the menu"),
]

MenuTags = Annotated[
    "set[ApiTag]",  # Forward reference to avoid circular import
    Field(default_factory=set, description="Set of tags associated with the menu"),
] 