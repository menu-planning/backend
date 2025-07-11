from typing import Any

from pydantic import HttpUrl

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_fields import MealDescriptionOptional, MealImageUrlOptional, MealLikeOptional, MealNameRequired, MealNotesOptional, MealRecipesOptionalList, MealTagsOptionalFrozenset
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.domain.meal.commands.update_meal import UpdateMeal
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired, UUIDIdOptional

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
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    name: MealNameRequired | None = None
    menu_id: UUIDIdOptional
    description: MealDescriptionOptional
    recipes: MealRecipesOptionalList
    tags: MealTagsOptionalFrozenset
    notes: MealNotesOptional
    like: MealLikeOptional
    image_url: HttpUrl | None = None

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
            if "recipes" in fields_set and self.recipes is not None:
                updates["recipes"] = [recipe.to_domain() for recipe in self.recipes]
            
            if "tags" in fields_set and self.tags is not None:
                updates["tags"] = set([tag.to_domain() for tag in self.tags])

            if "image_url" in fields_set and self.image_url is not None:
                updates["image_url"] = str(self.image_url)
            
            return updates
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnMeal to domain model: {e}"
            )


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
        ValueError: If the instance cannot be converted to a domain model.
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
            raise ValueError(f"Failed to convert ApiUpdateMeal to domain model: {e}")

    @classmethod
    def from_api_meal(cls, api_meal: ApiMeal) -> "ApiUpdateMeal":
        """Creates an instance from an existing meal."""
        # Only extract fields that ApiAttributesToUpdateOnMeal accepts
        allowed_fields = ApiAttributesToUpdateOnMeal.model_fields.keys()
        attributes_to_update = {}
        
        for key in allowed_fields:
            value = getattr(api_meal, key)
            # Convert HttpUrl to string for image_url field
            if key == "image_url" and value is not None:
                value = str(value)
            attributes_to_update[key] = value
        
        return cls(
            meal_id=api_meal.id,
            updates=ApiAttributesToUpdateOnMeal(**attributes_to_update),
        )
