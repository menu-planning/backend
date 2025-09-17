import uuid
from typing import Annotated, Any

import src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_fields as fields
from pydantic import Field, ValidationInfo, field_validator
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu_fields import (
    MenuMealsOptional,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.value_objects.api_menu_meal import (
    ApiMenuMeal,
)
from src.contexts.recipes_catalog.core.domain.meal.commands.create_meal import (
    CreateMeal,
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


class ApiCreateMeal(BaseApiCommand[CreateMeal]):
    """
    A Pydantic model representing and validating the data required
    to add a new meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the meal.
        author_id (str): ID of the user who created the meal.
        menu_id (str): ID of the menu to add the meal to.
        recipes (list[ApiRecipe], optional): Recipes that make up the meal.
        tags (frozenset[ApiTag], optional): Tags associated with the meal.
        description (str, optional): Description of the meal.
        notes (str, optional): Additional notes about the meal.
        image_url (str, optional): URL of an image of the meal.

    Methods:
        to_domain() -> CreateMeal:
            Converts the instance to a domain model object for creating a meal.

    Raises:
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    name: fields.MealNameRequired
    author_id: UUIDIdRequired
    menu_id: UUIDIdRequired
    menu_meal: Annotated[
        ApiMenuMeal | None, Field(default=None, description="Meal on the menu")
    ]
    recipes: fields.MealRecipesOptionalList
    tags: fields.MealTagsOptionalFrozenset
    description: fields.MealDescriptionOptional
    notes: fields.MealNotesOptional
    image_url: UrlOptional

    # This is a hack since menu_meal.meal_is is generated after the meal is created
    @field_validator("menu_meal", mode="before")
    @classmethod
    def validate_menu_meal(cls, v: Any, info: ValidationInfo) -> Any:
        if v is None:
            return v
        dummy_meal_id = uuid.uuid4().hex
        if isinstance(v, ApiMenuMeal):
            v.meal_id = dummy_meal_id
        elif isinstance(v, dict):
            v["meal_id"] = dummy_meal_id
        return v

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
                    type="meal",
                )
                for tag in v
            ]
            if v
            else []
        )

    def to_domain(self) -> CreateMeal:
        """Converts the instance to a domain model object for creating a meal."""
        try:
            return CreateMeal(
                name=self.name,
                author_id=self.author_id,
                menu_id=self.menu_id,
                menu_meal=self.menu_meal.to_domain() if self.menu_meal else None,
                recipes=(
                    [recipe.to_domain() for recipe in self.recipes]
                    if self.recipes
                    else None
                ),
                tags=(
                    frozenset([tag.to_domain() for tag in self.tags])
                    if self.tags
                    else None
                ),
                description=self.description,
                notes=self.notes,
                image_url=str(self.image_url) if self.image_url else None,
            )
        except Exception as e:
            raise ValidationConversionError(
                f"Failed to convert ApiCreateMeal to domain model: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
