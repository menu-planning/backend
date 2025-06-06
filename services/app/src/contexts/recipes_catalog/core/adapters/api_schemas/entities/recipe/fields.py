from typing import Annotated, TYPE_CHECKING
from pydantic import Field

from src.contexts.shared_kernel.domain.enums import Privacy

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.ingredient import ApiIngredient
    from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.rating import ApiRating
    from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import ApiNutriFacts
    from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag

# Required string fields with validation
RecipeName = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        description="Name of the recipe",
        pattern=r"^\S.*\S$",  # Ensures non-empty string with no leading/trailing whitespace
    ),
]

RecipeInstructions = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        description="Detailed instructions",
        pattern=r"^\S.*\S$",  # Ensures non-empty string with no leading/trailing whitespace
    ),
]

# Optional string fields
RecipeDescription = Annotated[
    str | None,
    Field(None, description="Detailed description"),
]

RecipeUtensils = Annotated[
    str | None,
    Field(None, description="Comma-separated list of utensils"),
]

RecipeNotes = Annotated[
    str | None,
    Field(None, description="Additional notes"),
]

RecipeImageUrl = Annotated[
    str | None,
    Field(None, description="URL of the recipe image"),
]

# Optional numeric fields
RecipeTotalTime = Annotated[
    int | None,
    Field(None, ge=0, description="Total preparation time in minutes"),
]

RecipeWeightInGrams = Annotated[
    int | None,
    Field(None, ge=0, description="Weight in grams"),
]

# Optional enum fields
RecipePrivacy = Annotated[
    Privacy,
    Field(default=Privacy.PRIVATE, description="Privacy setting"),
]

# Optional object fields
RecipeNutriFacts = Annotated[
    "ApiNutriFacts | None",  # Forward reference to avoid circular import
    Field(None, description="Nutritional facts"),
]

# Collection fields
RecipeIngredients = Annotated[
    "list[ApiIngredient]",  # Forward reference to avoid circular import
    Field(default_factory=list, description="List of ingredients"),
]

RecipeTags = Annotated[
    "set[ApiTag]",  # Forward reference to avoid circular import
    Field(default_factory=set, description="Set of tags"),
]

RecipeRatings = Annotated[
    "list[ApiRating]",  # Forward reference to avoid circular import
    Field(default_factory=list, description="List of user ratings"),
]

# Optional collection fields
OptionalRecipeTags = Annotated[
    "set[ApiTag] | None",  # Forward reference to avoid circular import
    Field(default_factory=set, description="Set of tags"),
]

# Optional numeric fields with range validation
RecipeAverageTasteRating = Annotated[
    float | None,
    Field(None, ge=0, le=5, description="Average taste rating"),
]

RecipeAverageConvenienceRating = Annotated[
    float | None,
    Field(None, ge=0, le=5, description="Average convenience rating"),
] 