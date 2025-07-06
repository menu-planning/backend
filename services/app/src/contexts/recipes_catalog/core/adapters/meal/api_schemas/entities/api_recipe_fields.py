from __future__ import annotations

from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text
from src.contexts.shared_kernel.domain.enums import Privacy

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


def _validate_privacy_enum(v: str | None) -> str | None:
    """Validates that a privacy value is a valid Privacy enum value."""
    if v is not None:
        try:
            Privacy(v)
            return v
        except ValueError:
            return None
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
    BeforeValidator(validate_optional_text),
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
    Privacy | None,
    Field(default=Privacy.PRIVATE, description="Privacy setting"),
    AfterValidator(_validate_privacy_enum),
]

# Optional object fields
RecipeNutriFacts = Annotated[
    'ApiNutriFacts | None',  # type: ignore # Forward reference to avoid circular import
    Field(None, description="Nutritional facts"),
]

# Collection fields
RecipeIngredients = Annotated[
    'frozenset[ApiIngredient]',  # type: ignore # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="List of ingredients"),
]

RecipeTags = Annotated[
    'frozenset[ApiTag]',  # type: ignore # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="frozenset of tags"),
]

RecipeRatings = Annotated[
    'frozenset[ApiRating]',  # type: ignore # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="List of user ratings"),
]

# Optional collection fields
OptionalRecipeTags = Annotated[
    'frozenset[ApiTag] | None',  # type: ignore # Forward reference to avoid circular import
    Field(None, description="Frozenset of tags"),
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