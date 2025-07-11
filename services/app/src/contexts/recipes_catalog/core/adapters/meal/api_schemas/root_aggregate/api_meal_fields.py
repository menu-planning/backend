from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import remove_whitespace_and_empty_str
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag

def _validate_percentage_range(v: float | None) -> float | None:
        """Validates that a percentage value is between 0 and 100."""
        if v is not None and not (0 <= v <= 100):
            raise ValueError(f"Validation error: Percentage must be between 0 and 100: {v}")
        return v

def _validate_non_negative_float(v: float | None) -> float | None:
    """Validates that a value is non-negative."""
    if v is not None and (not (v >= 0) or v == float('inf')):
        raise ValueError(f"Validation error: Value must be non-negative: {v}")
    return v

def _validate_non_negative_int(v: int | None) -> int | None:
    """Validates that an integer value is non-negative."""
    if v is not None and (v < 0 or v == float('inf')):
        raise ValueError(f"Validation error: Value must be non-negative: {v}")
    return v


# Required string fields with validation
MealNameRequired = Annotated[
    str,
    BeforeValidator(remove_whitespace_and_empty_str),
    Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the meal",
    ),
]

MealNutriFactsOptional = Annotated[
    ApiNutriFacts | None,
    Field(None, description="Nutritional facts"),
]

# Optional string fields
MealDescriptionOptional = Annotated[
    str | None,
    Field(None, description="Detailed description"),
]

MealNotesOptional = Annotated[
    str | None,
    Field(None, description="Additional notes"),
]

MealImageUrlOptional = Annotated[
    str | None,
    Field(None, description="URL of the meal image"),
]

# Optional numeric fields
MealWeightInGramsOptional = Annotated[
    int | None,
    Field(None, description="Weight in grams"),
    AfterValidator(_validate_non_negative_int),
]

MealCalorieDensityOptional = Annotated[
    float | None,
    Field(None, description="Calorie density"),
    AfterValidator(_validate_non_negative_float),
]

MealCarboPercentageOptional = Annotated[
    float | None,
    Field(None, description="Percentage of carbohydrates"),
    AfterValidator(_validate_percentage_range),
]

MealProteinPercentageOptional = Annotated[
    float | None,
    Field(None, description="Percentage of proteins"),
    AfterValidator(_validate_percentage_range),
]

MealTotalFatPercentageOptional = Annotated[
    float | None,
    Field(None, description="Percentage of total fat"),
    AfterValidator(_validate_percentage_range),
]

# Optional boolean fields
MealLikeOptional = Annotated[
    bool | None,
    Field(None, description="Whether the meal is liked"),
]

# Collection fields
MealRecipesOptionalList = Annotated[
    list[ApiRecipe] | None,
    Field(default_factory=list, description="List of recipes in the meal"),
]

MealTagsOptionalFrozenset = Annotated[
    frozenset[ApiTag] | None,
    Field(default_factory=frozenset, description="Frozenset of tags associated with the meal"),
] 
