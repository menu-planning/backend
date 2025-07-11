from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, Field

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import SanitizedText, SanitizedTextOptional, remove_whitespace_and_empty_str
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.shared_kernel.domain.enums import Privacy

def raise_validation_error(message: str) -> None:
    raise ValueError(f"Validation error: {message}")

def _validate_non_negative_int(v: int | None) -> int | None:
        """Validates that a value is non-negative."""
        if v is not None and (v < 0):
            raise ValueError(f"Validation error: Value must be non-negative: {v}")
        return v


def _validate_rating_range(v: float | None) -> float | None:
        """Validates that a rating value is between 0 and 5."""
        if v is not None and (v < 0 or v > 5):
            raise ValueError(f"Validation error: Rating must be between 0 and 5: {v}")
        return v


def _convert_none_to_private_enum(v: str | None) -> str | None:
    """Validates that a privacy value is a valid Privacy enum value."""
    if v is None:
        return Privacy.PRIVATE
    else:
        return v

# Required string fields with validation
RecipeNameRequired = Annotated[
    SanitizedText,
    Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Name of the recipe",
    ),
]

RecipeInstructionsRequired = Annotated[
    SanitizedText,
    Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Detailed instructions",
    ),
]

# Optional string fields
RecipeDescriptionOptional = Annotated[
    SanitizedTextOptional,
    AfterValidator(
         lambda v: raise_validation_error('Description must be less than 1000 characters') 
         if (v is not None and len(v)>10000) 
         else v),
]

RecipeUtensilsOptional = Annotated[
    str | None,
    BeforeValidator(remove_whitespace_and_empty_str),
    Field(None, description="Comma-separated list of utensils"),
    AfterValidator(
         lambda v: raise_validation_error('Utensils must be less than 1000 characters') 
         if (v is not None and len(v)>1000) 
         else v),
]

RecipeNotesOptional = Annotated[
    str | None,
    BeforeValidator(remove_whitespace_and_empty_str),
    Field(None, description="Additional notes"),
    AfterValidator(
         lambda v: raise_validation_error('Notes must be less than 10000 characters') 
         if (v is not None and len(v)>10000) 
         else v),
]

RecipeImageUrlOptional = Annotated[
    str | None,
    BeforeValidator(remove_whitespace_and_empty_str),
    Field(None, description="URL of the recipe image"),
]

# Optional numeric fields
RecipeTotalTimeOptional = Annotated[
    int | None,
    Field(None, description="Total preparation time in minutes"),
    AfterValidator(_validate_non_negative_int),
]

RecipeWeightInGramsOptional = Annotated[
    int | None,
    Field(None, description="Weight in grams"),
    AfterValidator(_validate_non_negative_int),
]

# Optional enum fields
RecipePrivacyOptional = Annotated[
    Privacy | None,
    Field(default=Privacy.PRIVATE, description="Privacy setting"),
    AfterValidator(_convert_none_to_private_enum),
]

# Optional object fields
RecipeNutriFactsOptional = Annotated[
    ApiNutriFacts | None,
    Field(None, description="Nutritional facts"),
]

# Collection fields
RecipeIngredientsOptionalFrozenset = Annotated[
    frozenset[ApiIngredient] | None,
    Field(default_factory=frozenset, description="frozenset of ingredients"),
]

RecipeTagsOptionalFrozenset = Annotated[
    frozenset[ApiTag] | None,
    Field(default_factory=frozenset, description="frozenset of tags"),
]

RecipeRatingsOptionalFrozenset = Annotated[
    frozenset[ApiRating] | None,
    Field(default_factory=frozenset, description="frozenset of user ratings"),
]

# Optional collection fields
RecipeTagsOptional = Annotated[
    frozenset[ApiTag] | None,
    Field(None, description="Frozenset of tags"),
]

# Optional numeric fields with range validation
RecipeAverageTasteRatingOptional = Annotated[
    float | None,
    Field(None, description="Average taste rating"),
    AfterValidator(
         lambda v: raise_validation_error('Average taste rating must be between 0 and 5') 
         if (v is not None and (v < 0 or v > 5)) 
         else v),
]

RecipeAverageConvenienceRatingOptional = Annotated[
    float | None,
    Field(None, description="Average convenience rating"),
    AfterValidator(_validate_rating_range),
]