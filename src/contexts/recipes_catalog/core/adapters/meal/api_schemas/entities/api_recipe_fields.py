from typing import Annotated

from pydantic import AfterValidator, Field

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import (
    ApiIngredient,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import (
    ApiRating,
)
from src.contexts.seedwork.shared.adapters.api_schemas import validators
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    SanitizedText,
    SanitizedTextOptional,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import (
    ApiNutriFacts,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)
from src.contexts.shared_kernel.domain.enums import Privacy

# Required string fields with validation
RecipeNameRequired = Annotated[
    SanitizedText,
    Field(
        ...,
        max_length=500,
        description="Name of the recipe",
    ),
]

RecipeInstructionsRequired = Annotated[
    SanitizedText,
    Field(
        ...,
        max_length=15000,
        description="Detailed instructions",
    ),
]

# Optional string fields
RecipeDescriptionOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Description of the recipe"),
    AfterValidator(
        lambda v: validators.validate_optional_text_length(
            v, 1000, "Description must be less than 1000 characters"
        )
    ),
]

RecipeUtensilsOptional = Annotated[
    SanitizedTextOptional,
    AfterValidator(
        lambda v: validators.validate_optional_text_length(
            v, 500, "Utensils must be less than 500 characters"
        )
    ),
    Field(None, description="Comma-separated list of utensils"),
]

RecipeNotesOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Notes of the recipe"),
    AfterValidator(
        lambda v: validators.validate_optional_text_length(
            v, 1000, "Notes must be less than 1000 characters"
        )
    ),
]

# Optional numeric fields
RecipeTotalTimeOptional = Annotated[
    int | None,
    Field(None, description="Total preparation time in minutes"),
    AfterValidator(validators.validate_non_negative_int),
]

RecipeWeightInGramsOptional = Annotated[
    int | None,
    Field(None, description="Weight in grams"),
    AfterValidator(validators.validate_non_negative_int),
]

# Optional enum fields
RecipePrivacyOptional = Annotated[
    Privacy | None,
    Field(default=Privacy.PRIVATE, description="Privacy setting"),
    AfterValidator(validators.convert_none_to_private_enum),
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
    AfterValidator(validators.validate_rating_range),
]

RecipeAverageConvenienceRatingOptional = Annotated[
    float | None,
    Field(None, description="Average convenience rating"),
    AfterValidator(validators.validate_rating_range),
]
