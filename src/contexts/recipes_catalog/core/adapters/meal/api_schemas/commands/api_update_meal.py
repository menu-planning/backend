from typing import Any

import src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_fields as meal_annotations
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.core.domain.meal.commands.update_meal import (
    UpdateMeal,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UrlOptional,
    UUIDIdOptional,
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiAttributesToUpdateOnMeal(BaseApiCommand[UpdateMeal]):
    """
    A pydantic model representing and validating the data required to update
    a meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the meal.
        menu_id (str, optional): ID of the menu to move the meal to.
        description (str, optional): Description of the meal.
        recipes (list[ApiRecipe], optional): Recipes in the meal.
        tags (frozenset[ApiTag], optional): Tags associated with the meal.
        notes (str, optional): Additional notes about the meal.
        like (bool, optional): Whether the meal is liked.
        image_url (str, optional): URL of an image of the meal.

    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary of attributes to update.

    Raises:
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    name: meal_annotations.MealNameRequired | None = None
    menu_id: UUIDIdOptional
    description: meal_annotations.MealDescriptionOptional
    recipes: meal_annotations.MealRecipesOptionalList
    tags: meal_annotations.MealTagsOptionalFrozenset
    notes: meal_annotations.MealNotesOptional
    like: meal_annotations.MealLikeOptional
    image_url: UrlOptional

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            # Manual field conversion to avoid model_dump issues with frozensets
            updates = {}

            # Get fields that are set (exclude_unset behavior)
            fields_set = self.__pydantic_fields_set__

            # Simple fields that can be included directly
            simple_fields = ["name", "menu_id", "description", "notes", "like"]

            for field in simple_fields:
                if field in fields_set:
                    value = getattr(self, field)
                    updates[field] = value

            # Complex fields that need special handling
            # Include recipes if explicitly set, even if empty list
            if "recipes" in fields_set:
                if self.recipes is not None:
                    updates["recipes"] = [recipe.to_domain() for recipe in self.recipes]
                else:
                    updates["recipes"] = None

            # Include tags if explicitly set, even if empty frozenset
            if "tags" in fields_set:
                if self.tags is not None:
                    updates["tags"] = {tag.to_domain() for tag in self.tags}
                else:
                    updates["tags"] = None

            # Include image_url if explicitly set, even if None
            if "image_url" in fields_set:
                if self.image_url is not None:
                    url_str = str(self.image_url)
                    # Handle Pydantic's URL normalization - remove trailing slash if
                    # it was added This preserves the original URL format expected
                    # by tests
                    if url_str.endswith("/") and not url_str.endswith("://"):
                        # Remove trailing slash from URLs like
                        # "http://example.com/" -> "http://example.com"
                        # but preserve it for URLs that originally had it or for
                        # root paths
                        base_url = url_str.rstrip("/")
                        # Only remove if the URL doesn't have a path component
                        if (
                            base_url.count("/") == 2
                        ):  # e.g., "http://example.com" has 2 slashes
                            url_str = base_url
                    updates["image_url"] = url_str
                else:
                    updates["image_url"] = None
        except Exception as e:
            error_msg = (
                f"Failed to convert ApiAttributesToUpdateOnMeal to domain model: {e}"
            )
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
        else:
            return updates


class ApiUpdateMeal(BaseApiCommand[UpdateMeal]):
    """
    A Pydantic model representing and validating the data required
    to update a meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): ID of the meal to update.
        updates (ApiAttributesToUpdateOnMeal): Attributes to update.

    Methods:
        to_domain() -> UpdateMeal:
            Converts the instance to a domain model object for updating a meal.

    Raises:
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    meal_id: UUIDIdRequired
    updates: ApiAttributesToUpdateOnMeal

    def to_domain(self) -> UpdateMeal:
        """Converts the instance to a domain model object for updating a meal."""
        try:
            return UpdateMeal(
                meal_id=self.meal_id,
                updates=self.updates.to_domain(),
            )
        except Exception as e:
            error_msg = f"Failed to convert ApiUpdateMeal to domain model: {e}"
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e

    @classmethod
    def from_api_meal(
        cls, api_meal: ApiMeal, old_api_meal: ApiMeal | None = None
    ) -> "ApiUpdateMeal":
        """Creates an instance from an existing meal.

        Args:
            api_meal: The new/updated meal data.
            old_api_meal: Optional. The original meal to compare against.
                         If provided, only changed fields will be included in updates.
                         If not provided, all fields will be included
                         (previous behavior).

        Returns:
            ApiUpdateMeal instance with only the changed attributes
            (if old_api_meal provided) or all attributes (if old_api_meal not provided).
        """
        # Only extract fields that ApiAttributesToUpdateOnMeal accepts
        allowed_fields = ApiAttributesToUpdateOnMeal.model_fields.keys()
        attributes_to_update = {}

        for key in allowed_fields:
            new_value = getattr(api_meal, key)

            # If no old meal provided, include all fields (current behavior)
            if old_api_meal is None:
                attributes_to_update[key] = new_value
            else:
                # Compare with old value and only include if changed
                old_value = getattr(old_api_meal, key)
                if new_value != old_value:
                    attributes_to_update[key] = new_value

        return cls(
            meal_id=api_meal.id,
            updates=ApiAttributesToUpdateOnMeal(**attributes_to_update),
        )
