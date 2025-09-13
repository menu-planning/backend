from typing import Any

import src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_fields as fields
from pydantic import ValidationInfo, field_validator
from src.contexts.recipes_catalog.core.domain.meal.commands.create_recipe import (
    CreateRecipe,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UrlOptional,
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiCreateRecipe(BaseApiCommand[CreateRecipe]):
    """
    A Pydantic model representing and validating the data required
    to add a new recipe via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the recipe.
        description (str): Detailed description of the recipe.
        ingredients (list[ApiIngredient], optional): Detailed list of
            ingredients.
        instructions (str):Detailed instructions.
        author_id (str): The recipe's author id.
        utensils (str, optional): Comma-separated list of utensils.
        total_time (int, optional): Total preparation and cooking time in
            minutes.
        notes (str, optional): Additional notes about the recipe.
        tags (frozenset[ApiTag], optional): Detailed frozenset of tags.
        privacy (Privacy): Privacy setting of the recipe.
        nutri_facts (ApiNutriFacts, optional): Nutritional facts of the
            recipe.
        image_url (str, optional): URL of an image of the recipe.

    Methods:
        to_domain() -> CreateRecipe:
            Converts the instance to a domain model object for adding a recipe.

    Raises:
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    name: fields.RecipeNameRequired
    instructions: fields.RecipeInstructionsRequired
    author_id: UUIDIdRequired
    meal_id: UUIDIdRequired
    ingredients: fields.RecipeIngredientsOptionalFrozenset
    description: fields.RecipeDescriptionOptional
    utensils: fields.RecipeUtensilsOptional
    total_time: fields.RecipeTotalTimeOptional
    notes: fields.RecipeNotesOptional
    tags: fields.RecipeTagsOptionalFrozenset
    privacy: fields.RecipePrivacyOptional
    nutri_facts: fields.RecipeNutriFactsOptional
    weight_in_grams: fields.RecipeWeightInGramsOptional
    image_url: UrlOptional

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(
        cls, v: list[dict[str, Any]], info: ValidationInfo
    ) -> frozenset[ApiTag]:
        return frozenset(
            [
                ApiTag(
                    key=tag.get("key", ""),
                    value=tag.get("value", ""),
                    author_id=info.data["author_id"],
                    type="recipe",
                )
                for tag in v
            ]
            if v
            else []
        )

    # @field_validator("tags", mode="before")
    # @classmethod
    # def validate_tags_have_correct_author_id_and_type(
    #     cls, v: Any, info: ValidationInfo
    # ) -> Any:
    #     """
    #     Validate tags field. If a dict is provided without 'type' and 'author_id',
    #     add them with default values and convert to ApiTag.
    #     """
    #     # for tag in v:
    #     #     if tag.author_id is None:
    #     #         tag.author_id = info.data["author_id"]

    #     # First apply the existing validation
    #     validated_tags = validate_tags(v, "recipe", info)

    #     # Check for duplicate tags based on value
    #     if validated_tags:
    #         tag_values = []
    #         for tag in validated_tags:
    #             if hasattr(tag, "value"):
    #                 tag_values.append(tag.value)
    #             elif isinstance(tag, dict) and "value" in tag:
    #                 tag_values.append(tag["value"])

    #         # Check for duplicates
    #         seen_values = set()
    #         duplicates = []
    #         for value in tag_values:
    #             if value in seen_values:
    #                 duplicates.append(value)
    #             else:
    #                 seen_values.add(value)

    #         if duplicates:
    #             raise DuplicateItemError.create_pydantic_error(
    #                 item_type="tag",
    #                 field="tags",
    #                 duplicate_key="value",
    #                 duplicate_value=duplicates[0],
    #                 duplicate_items=[
    #                     tag
    #                     for tag in validated_tags
    #                     if hasattr(tag, "value") and tag.value == duplicates[0]
    #                 ],
    #             )

    #     return validated_tags

    def to_domain(self) -> CreateRecipe:
        """Converts the instance to a domain model object for adding a recipe."""
        try:
            return CreateRecipe(
                name=self.name,
                instructions=self.instructions,
                author_id=self.author_id,
                meal_id=self.meal_id,
                ingredients=(
                    [i.to_domain() for i in self.ingredients]
                    if self.ingredients
                    else None
                ),
                description=self.description,
                utensils=self.utensils,
                total_time=self.total_time,
                notes=self.notes,
                tags=(
                    frozenset([t.to_domain() for t in self.tags]) if self.tags else None
                ),
                privacy=self.privacy if self.privacy else Privacy.PRIVATE,
                nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
                weight_in_grams=self.weight_in_grams,
                image_url=str(self.image_url) if self.image_url else None,
            )
        except Exception as e:
            raise ValidationConversionError(
                f"Failed to convert ApiCreateRecipe to domain model: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
