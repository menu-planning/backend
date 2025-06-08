from typing import Annotated
from pydantic import AfterValidator, Field

from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.recipe import ApiRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.fields import trim_whitespace
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import ApiNutriFacts

def _validate_percentage_range(v: float | None) -> float | None:
        """Validates that a percentage value is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError(f"Percentage must be between 0 and 100: {v}")
        return v

def _validate_non_negative_float(v: float | None) -> float | None:
        """Validates that a value is non-negative."""
        if v is not None and (v < 0):
            raise ValueError(f"Value must be non-negative: {v}")
        return v

# Required string fields with validation
MealName = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        description="Name of the meal",
    ),
    AfterValidator(trim_whitespace),
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
    Field(None, description="Weight in grams"),
    AfterValidator(_validate_non_negative_float),
]

MealCalorieDensity = Annotated[
    float | None,
    Field(None, description="Calorie density"),
    AfterValidator(_validate_non_negative_float),
]

MealCarboPercentage = Annotated[
    float | None,
    Field(None, description="Percentage of carbohydrates"),
    AfterValidator(_validate_percentage_range),
]

MealProteinPercentage = Annotated[
    float | None,
    Field(None, description="Percentage of proteins"),
    AfterValidator(_validate_percentage_range),
]

MealTotalFatPercentage = Annotated[
    float | None,
    Field(None, description="Percentage of total fat"),
    AfterValidator(_validate_percentage_range),
]

# Optional boolean fields
MealLike = Annotated[
    bool | None,
    Field(None, description="Whether the meal is liked"),
]

# Optional object fields
MealNutriFacts = Annotated[
    ApiNutriFacts | None,  # Forward reference to avoid circular import
    Field(None, description="Nutritional facts"),
]

# Collection fields
MealRecipes = Annotated[
    list[ApiRecipe],  # Forward reference to avoid circular import
    Field(default_factory=list, description="List of recipes in the meal"),
]

MealTags = Annotated[
    set[ApiTag],  # Forward reference to avoid circular import
    Field(default_factory=set, description="Set of tags associated with the meal"),
] 