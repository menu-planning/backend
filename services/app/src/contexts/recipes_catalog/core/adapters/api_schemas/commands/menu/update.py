# from typing import Any

# from pydantic import BaseModel, Field, field_serializer

# from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.menu.menu import \
#     ApiMenu
# from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.menu_meal import \
#     ApiMenuMeal
# from src.contexts.recipes_catalog.shared.domain.commands import UpdateMenu
# from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import \
#     ApiTag


# class ApiAttributesToUpdateOnMenu(BaseModel):
#     """
#     A pydantic model representing and validating the data required to update
#     a Menu via the API.

#     This model is used for input validation and serialization of domain
#     objects in API requests and responses.

#     Attributes:
#         meals (set[ApiMenuMeal]): The meals to update.
#         description (str): The description to update.
#         tags (set[ApiTag]): The tags to update.

#     Methods:
#         to_domain() -> dict:
#             Converts the instance to a dictionary of attributes to update.

#     Raises:
#         ValueError: If the instance cannot be converted to a domain model.
#         ValidationError: If the instance is invalid.
#     """

#     meals: set[ApiMenuMeal] | None = None
#     description: str | None = None
#     tags: set[ApiTag] | None = Field(default_factory=set)

#     @field_serializer("tags")
#     def serialize_tags(self, tags: list[ApiTag] | None, _info):
#         """Serializes the tag list to a list of domain models."""
#         return {i.to_domain() for i in tags} if tags else set()

#     @field_serializer("meals")
#     def serialize_meals(self, meals: set[ApiMenuMeal] | None, _info):
#         """Serializes the meals dictionary to a dictionary of domain models."""
#         return (
#             {
#                 meal.to_domain()
#                 for meal in meals
#             }
#             if meals
#             else set()
#         )

#     def to_domain(self) -> dict[str, Any]:
#         """Converts the instance to a dictionary of attributes to update."""
#         try:
#             return self.model_dump(exclude_unset=True)
#         except Exception as e:
#             raise ValueError(
#                 f"Failed to convert ApiAttributesToUpdateOnMenu to domain model: {e}"
#             )


# class ApiUpdateMenu(BaseModel):
#     """
#     A Pydantic model representing and validating the the data required
#     to update a Menu via the API.

#     This model is used for input validation and serialization of domain
#     objects in API requests and responses.

#     Attributes:
#         menu_id (str): Identifier of the Menu to update.
#         updates (ApiAttributesToUpdateOnMenu): Attributes to update.

#     Methods:
#         to_domain() -> UpdateMenu:
#             Converts the instance to a domain model object for updating a Menu.

#     Raises:
#         ValueError: If the instance cannot be converted to a domain model.
#         ValidationError: If the instance is invalid.

#     """

#     menu_id: str
#     updates: ApiAttributesToUpdateOnMenu

#     def to_domain(self) -> UpdateMenu:
#         """Converts the instance to a domain model object for updating a menu."""
#         try:
#             return UpdateMenu(menu_id=self.menu_id, updates=self.updates.to_domain())
#         except Exception as e:
#             raise ValueError(f"Failed to convert ApiUpdateMenu to domain model: {e}")

#     @classmethod
#     def from_api_menu(cls, api_menu: ApiMenu) -> "ApiUpdateMenu":
#         """Creates an instance from an existing menu."""
#         attributes_to_update = {
#             key: getattr(api_menu, key) for key in api_menu.model_fields.keys()
#         }
#         attributes_to_update["meals"] = set(api_menu.meals.values()) if api_menu.meals else None
#         return cls(
#             menu_id=api_menu.id,
#             updates=ApiAttributesToUpdateOnMenu(**attributes_to_update),
#         )
