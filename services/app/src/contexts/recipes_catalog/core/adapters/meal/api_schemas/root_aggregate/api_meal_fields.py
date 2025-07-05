from typing import Annotated, List, FrozenSet
from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts

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
    BeforeValidator(validate_optional_text),
    Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the meal",
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
    "List[ApiRecipe]",  # Forward reference to avoid circular import
    Field(default_factory=list, description="List of recipes in the meal"),
]

MealTags = Annotated[
    'FrozenSet[ApiTag]',  # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="Frozenset of tags associated with the meal"),
] 
