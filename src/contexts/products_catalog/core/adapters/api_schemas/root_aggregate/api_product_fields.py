"""Field definitions for product API schemas.

Provides validated field types for product entities with proper
constraints and validation rules.
"""
from typing import Annotated

import src.contexts.seedwork.adapters.api_schemas.validators as validators
from pydantic import AfterValidator, Field
from src.contexts.products_catalog.core.adapters.api_schemas.value_objects.api_if_food_votes import (
    ApiIsFoodVotes,
)
from src.contexts.products_catalog.core.adapters.api_schemas.value_objects.api_score import (
    ApiScore,
)
from src.contexts.products_catalog.core.domain.enums import Unit
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedText,
    SanitizedTextOptional,
    UrlOptional,
    UUIDIdRequired,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import (
    ApiNutriFacts,
)

# Required string fields with validation
ProductSourceIdRequired = Annotated[
    str,
    Field(..., description="Source identifier for the product"),
    AfterValidator(validators.validate_uuid_format),
]

ProductNameRequired = Annotated[
    SanitizedText,
    Field(..., max_length=500, description="Name of the product"),
]

# Optional string fields
ProductShoppingNameOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Shopping name of the product"),
    AfterValidator(lambda v: validators.validate_optional_text_length(v, 500, "Shopping name must be less than 500 characters")),
]

ProductStoreDepartmentNameOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Store department name"),
    AfterValidator(lambda v: validators.validate_optional_text_length(v, 200, "Store department name must be less than 200 characters")),
]

ProductRecommendedBrandsOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Recommended brands and products"),
    AfterValidator(lambda v: validators.validate_optional_text_length(v, 1000, "Recommended brands must be less than 1000 characters")),
]

ProductNutritionGroupOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Nutrition group"),
    AfterValidator(lambda v: validators.validate_optional_text_length(v, 200, "Nutrition group must be less than 200 characters")),
]

ProductSubstitutesOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Product substitutes"),
    AfterValidator(lambda v: validators.validate_optional_text_length(v, 1000, "Substitutes must be less than 1000 characters")),
]

ProductBarcodeOptional = Annotated[
    str | None,
    Field(default=None, description="Product barcode"),
    AfterValidator(lambda v: validators.validate_optional_text_length(v, 50, "Barcode must be less than 50 characters")),
]

ProductIngredientsOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Product ingredients"),
    AfterValidator(lambda v: validators.validate_optional_text_length(v, 5000, "Ingredients must be less than 5000 characters")),
]

ProductJsonDataOptional = Annotated[
    str | None,
    Field(default=None, description="Additional JSON data"),
]

# Optional UUID fields
ProductBrandIdOptional = Annotated[
    str | None,
    Field(default=None, description="Brand identifier"),
    AfterValidator(validators.validate_optional_uuid_format),
]

ProductCategoryIdOptional = Annotated[
    str | None,
    Field(default=None, description="Category identifier"),
    AfterValidator(validators.validate_optional_uuid_format),
]

ProductParentCategoryIdOptional = Annotated[
    str | None,
    Field(default=None, description="Parent category identifier"),
    AfterValidator(validators.validate_optional_uuid_format),
]

ProductFoodGroupIdOptional = Annotated[
    str | None,
    Field(default=None, description="Food group identifier"),
    AfterValidator(validators.validate_optional_uuid_format),
]

ProductProcessTypeIdOptional = Annotated[
    str | None,
    Field(default=None, description="Process type identifier"),
    AfterValidator(validators.validate_optional_uuid_format),
]

# Optional numeric fields
ProductEdibleYieldOptional = Annotated[
    float | None,
    Field(default=None, description="Edible yield ratio (0 < value <= 1)"),
    AfterValidator(validators.validate_non_negative_float),
]

ProductKgPerUnitOptional = Annotated[
    float | None,
    Field(default=None, description="Kilograms per unit"),
    AfterValidator(validators.validate_non_negative_float),
]

ProductLitersPerKgOptional = Annotated[
    float | None,
    Field(default=None, description="Liters per kilogram"),
    AfterValidator(validators.validate_non_negative_float),
]

ProductCookingFactorOptional = Annotated[
    float | None,
    Field(default=None, description="Cooking factor"),
    AfterValidator(validators.validate_non_negative_float),
]

ProductPackageSizeOptional = Annotated[
    float | None,
    Field(default=None, description="Package size"),
    AfterValidator(validators.validate_non_negative_float),
]

ProductConservationDaysOptional = Annotated[
    int | None,
    Field(default=None, description="Conservation days"),
    AfterValidator(validators.validate_non_negative_int),
]

# Optional boolean fields
ProductIsFoodOptional = Annotated[
    bool | None,
    Field(default=None, description="Whether the product is food"),
]

ProductIsFoodHousesChoiceOptional = Annotated[
    bool | None,
    Field(default=None, description="Houses choice for is_food"),
]

# Optional enum fields
ProductPackageSizeUnitOptional = Annotated[
    Unit | None,
    Field(default=None, description="Package size unit"),
]

# Optional object fields
ProductScoreOptional = Annotated[
    ApiScore | None,
    Field(default=None, description="Product score"),
]

ProductNutriFactsOptional = Annotated[
    ApiNutriFacts | None,
    Field(default=None, description="Nutritional facts"),
]

ProductIsFoodVotesOptional = Annotated[
    ApiIsFoodVotes | None,
    Field(default=None, description="Is food votes"),
]
