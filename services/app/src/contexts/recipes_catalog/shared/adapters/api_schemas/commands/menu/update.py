from typing import Any

from pydantic import BaseModel, Field, field_serializer

from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.meal.meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands import UpdateMenu
from src.contexts.recipes_catalog.shared.domain.commands.meal.update_meal import (
    UpdateMeal,
)
from src.contexts.recipes_catalog.shared.domain.enums import MealType
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import MenuMeal
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.contexts.shared_kernel.domain.enums import Weekday
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class ApiAttributesToUpdateOnMenu(BaseModel):
    """
    A pydantic model representing and validating the data required to update
    a Menu via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the Menu.
        description (str, optional): Detailed description of the Menu.
        notes (str, optional): Additional notes about the Menu.
        like (bool, optional): Whether the user likes the Menu.
        image_url (str, optional): URL of the image of the Menu.


    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary of attributes to update.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    id: str
    author_id: str
    client_id: str | None = None
    meals: dict[tuple[int, Weekday, MealType], MenuMeal] | None = None
    description: str | None = None
    # recipe_id: str
    name: str | None = None
    description: str | None = None
    tags: set[ApiTag] | None = Field(default_factory=set)
    notes: str | None = None
    like: bool | None = None
    image_url: str | None = None

    @field_serializer("tags")
    def serialize_tags(self, tags: list[ApiTag] | None, _info):
        """Serializes the tag list to a list of domain models."""
        return set([i.to_domain() for i in tags]) if tags else None

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump(exclude_unset=True)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnMeal to domain model: {e}"
            )


class ApiUpdateMeal(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update a Meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): Identifier of the Meal to update.
        updates (ApiAttributesToUpdateOnMeal): Attributes to update.

    Methods:
        to_domain() -> UpdateMeal:
            Converts the instance to a domain model object for updating a Meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    meal_id: str
    updates: ApiAttributesToUpdateOnMenu

    def to_domain(self) -> UpdateMeal:
        """Converts the instance to a domain model object for updating a meal."""
        try:
            return UpdateMenu(id=self.meal_id, updates=self.updates.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateMeal to domain model: {e}")

    @classmethod
    def from_api_meal(cls, api_meal: ApiMeal) -> "ApiUpdateMeal":
        """Creates an instance from an existing meal."""
        attributes_to_update = {
            key: getattr(api_meal, key) for key in api_meal.model_fields.keys()
        }
        return cls(
            meal_id=api_meal.id,
            updates=ApiAttributesToUpdateOnMenu(**attributes_to_update),
        )
