from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag

def _validate_non_negative_int(v: int | None) -> int | None:
        """Validates that a value is non-negative."""
        if v is not None and (v < 0):
            raise ValueError(f"Value must be non-negative: {v}")
        return v


def _validate_rating_range(v: float | None) -> float | None:
        """Validates that a rating value is between 0 and 5."""
        if v is not None and (v < 0 or v > 5):
            raise ValueError(f"Rating must be between 0 and 5: {v}")
        return v


# Required string fields with validation
RecipeName = Annotated[
    str,
    BeforeValidator(validate_optional_text),
    Field(
        ...,
        min_length=1,
        description="Name of the recipe",
    ),
]

RecipeInstructions = Annotated[
    str,
    BeforeValidator(validate_optional_text),
    Field(
        ...,
        min_length=1,
        description="Detailed instructions",
    ),
]

# Optional string fields
RecipeDescription = Annotated[
    str | None,
    Field(None, description="Detailed description"),
    
]

RecipeUtensils = Annotated[
    str | None,
    BeforeValidator(validate_optional_text),
    Field(None, description="Comma-separated list of utensils"),
]

RecipeNotes = Annotated[
    str | None,
    BeforeValidator(validate_optional_text),
    Field(None, description="Additional notes"),
]

RecipeImageUrl = Annotated[
    str | None,
    BeforeValidator(validate_optional_text),
    Field(None, description="URL of the recipe image"),
]

# Optional numeric fields
RecipeTotalTime = Annotated[
    int | None,
    Field(None, description="Total preparation time in minutes"),
    AfterValidator(_validate_non_negative_int),
]

RecipeWeightInGrams = Annotated[
    int | None,
    Field(None, description="Weight in grams"),
    AfterValidator(_validate_non_negative_int),
]

# Optional enum fields
RecipePrivacy = Annotated[
    str | None,
    Field(default=Privacy.PRIVATE, description="Privacy setting"),
    AfterValidator(lambda v: v if v in Privacy else None),
]

# Optional object fields
RecipeNutriFacts = Annotated[
    ApiNutriFacts | None,  # Forward reference to avoid circular import
    Field(None, description="Nutritional facts"),
]

# Collection fields
RecipeIngredients = Annotated[
    list[ApiIngredient],  # Forward reference to avoid circular import
    Field(default_factory=list, description="List of ingredients"),
]

RecipeTags = Annotated[
    frozenset[ApiTag],  # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="Frozenset of tags"),
]

RecipeRatings = Annotated[
    list[ApiRating],  # Forward reference to avoid circular import
    Field(default_factory=list, description="List of user ratings"),
]

# Optional collection fields
OptionalRecipeTags = Annotated[
    frozenset[ApiTag] | None,  # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="Frozenset of tags"),
]

# Optional numeric fields with range validation
RecipeAverageTasteRating = Annotated[
    float | None,
    Field(None, description="Average taste rating"),
    AfterValidator(_validate_rating_range),
]

RecipeAverageConvenienceRating = Annotated[
    float | None,
    Field(None, description="Average convenience rating"),
    AfterValidator(_validate_rating_range),
] 