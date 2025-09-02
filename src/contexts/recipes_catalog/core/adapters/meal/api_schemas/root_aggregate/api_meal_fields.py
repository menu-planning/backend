from typing import Annotated

from pydantic import AfterValidator, Field
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
)
from src.contexts.seedwork.adapters.api_schemas import validators
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedText,
    SanitizedTextOptional,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import (
    ApiNutriFacts,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)

MealNameRequired = Annotated[
    SanitizedText,
    Field(
        ...,
        max_length=255,
        description="Name of the meal",
    ),
]

MealNutriFactsOptional = Annotated[
    ApiNutriFacts | None,
    Field(None, description="Nutritional facts"),
]

MealDescriptionOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Description of the meal"),
    AfterValidator(
        lambda v: validators.validate_optional_text_length(
            v, 1000, "Description must be less than 1000 characters"
        )
    ),
]

MealNotesOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Notes of the meal"),
    AfterValidator(
        lambda v: validators.validate_optional_text_length(
            v, 1000, "Notes must be less than 1000 characters"
        )
    ),
]

MealWeightInGramsOptional = Annotated[
    int | None,
    Field(None, description="Weight in grams"),
    AfterValidator(validators.validate_non_negative_int),
]

MealCalorieDensityOptional = Annotated[
    float | None,
    Field(None, description="Calorie density"),
    AfterValidator(validators.validate_non_negative_float),
]

MealCarboPercentageOptional = Annotated[
    float | None,
    Field(None, description="Percentage of carbohydrates"),
    AfterValidator(validators.validate_percentage_range),
]

MealProteinPercentageOptional = Annotated[
    float | None,
    Field(None, description="Percentage of proteins"),
    AfterValidator(validators.validate_percentage_range),
]

MealTotalFatPercentageOptional = Annotated[
    float | None,
    Field(None, description="Percentage of total fat"),
    AfterValidator(validators.validate_percentage_range),
]

MealLikeOptional = Annotated[
    bool | None,
    Field(None, description="Whether the meal is liked"),
]

MealRecipesOptionalList = Annotated[
    list[ApiRecipe] | None,
    Field(default_factory=list, description="List of recipes in the meal"),
]

MealTagsOptionalFrozenset = Annotated[
    frozenset[ApiTag] | None,
    Field(
        default_factory=frozenset,
        description="Frozenset of tags associated with the meal",
    ),
]
