from typing import Annotated, TYPE_CHECKING
from pydantic import Field

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.recipe import ApiRecipe
    from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
    from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import ApiNutriFacts

# Required string fields with validation
MealName = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        description="Name of the meal",
        pattern=r"^\S.*\S$",  # Ensures non-empty string with no leading/trailing whitespace
    ),
]

# Optional string fields
MealDescription = Annotated[
    str | None,
    Field(None, description="Detailed description"),
]

MealNotes = Annotated[
    str | None,
    Field(None, description="Additional notes"),
]

MealImageUrl = Annotated[
    str | None,
    Field(None, description="URL of the meal image"),
]

# Optional numeric fields
MealWeightInGrams = Annotated[
    int | None,
    Field(None, ge=0, description="Weight in grams"),
]

MealCalorieDensity = Annotated[
    float | None,
    Field(None, ge=0, description="Calorie density"),
]

MealCarboPercentage = Annotated[
    float | None,
    Field(None, ge=0, le=100, description="Percentage of carbohydrates"),
]

MealProteinPercentage = Annotated[
    float | None,
    Field(None, ge=0, le=100, description="Percentage of proteins"),
]

MealTotalFatPercentage = Annotated[
    float | None,
    Field(None, ge=0, le=100, description="Percentage of total fat"),
]

# Optional boolean fields
MealLike = Annotated[
    bool | None,
    Field(None, description="Whether the meal is liked"),
]

# Optional object fields
MealNutriFacts = Annotated[
    "ApiNutriFacts | None",  # Forward reference to avoid circular import
    Field(None, description="Nutritional facts"),
]

# Collection fields
MealRecipes = Annotated[
    "list[ApiRecipe]",  # Forward reference to avoid circular import
    Field(default_factory=list, description="List of recipes in the meal"),
]

MealTags = Annotated[
    "set[ApiTag]",  # Forward reference to avoid circular import
    Field(default_factory=set, description="Set of tags associated with the meal"),
] 