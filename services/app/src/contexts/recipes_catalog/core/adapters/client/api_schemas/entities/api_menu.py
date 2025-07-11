from datetime import datetime
from typing import Any, Dict

from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import MenuSaModel
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu_fields import MenuDescriptionOptional, MenuMealsOptional, MenuTagsOptional
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.value_objects.api_menu_meal import ApiMenuMeal
from src.contexts.recipes_catalog.core.domain.client.entities.menu import Menu
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiEntity
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag

class ApiMenu(BaseApiEntity[Menu, MenuSaModel]):
    """
    A Pydantic model representing and validating a menu encompassing
    details about the menu, its meals, and additional metadata.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the menu.
        author_id (str): Unique identifier of the user who created the menu.
        client_id (str): Unique identifier of the client the menu is associated with.
        meals (frozenset[ApiMenuMeal]): Frozenset of meals on a menu with week, weekday and meal_id.
        tags (frozenset[ApiTag]): Frozenset of tags associated with the menu.
        description (str | None): Description of the menu.
        created_at (datetime): Timestamp of when the menu was created.
        updated_at (datetime): Timestamp of when the menu was last updated.
        discarded (bool): Flag indicating if the menu is discarded.
        version (int): Version of the menu.
    """

    author_id: UUIDIdRequired
    client_id: UUIDIdRequired
    meals: MenuMealsOptional
    tags: MenuTagsOptional
    description: MenuDescriptionOptional

    @classmethod
    def from_domain(cls, domain_obj: Menu) -> "ApiMenu":
        """Convert a domain object to an API schema instance."""
        return cls(
            id=domain_obj.id,
            author_id=domain_obj.author_id,
            client_id=domain_obj.client_id,
            meals=frozenset(ApiMenuMeal.from_domain(i) for i in domain_obj.meals),
            tags=frozenset(ApiTag.from_domain(tag) for tag in domain_obj.tags),
            description=domain_obj.description,
            created_at=domain_obj.created_at or datetime.now(),
            updated_at=domain_obj.updated_at or datetime.now(),
            discarded=domain_obj.discarded,
            version=domain_obj.version,
        )

    def to_domain(self) -> Menu:
        """Convert the API schema instance to a domain object."""
        return Menu(
            id=self.id,
            author_id=self.author_id,
            client_id=self.client_id,
            meals=set(meal.to_domain() for meal in self.meals) if self.meals else None,
            tags=set(tag.to_domain() for tag in self.tags) if self.tags else None,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
            discarded=self.discarded,
            version=self.version,
        )

    @classmethod
    def from_orm_model(cls, orm_model: MenuSaModel) -> "ApiMenu":
        """Convert an ORM model to an API schema instance."""
        return cls(
            id=orm_model.id,
            author_id=orm_model.author_id,
            client_id=orm_model.client_id,
            meals=frozenset(ApiMenuMeal.from_orm_model(i) for i in orm_model.meals),
            tags=frozenset(ApiTag.from_orm_model(tag) for tag in orm_model.tags),
            description=orm_model.description,
            created_at=orm_model.created_at or datetime.now(),
            updated_at=orm_model.updated_at or datetime.now(),
            discarded=orm_model.discarded,
            version=orm_model.version,
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the API schema instance to ORM model kwargs."""
        return {
            "id": self.id,
            "author_id": self.author_id,
            "client_id": self.client_id,
            "meals": [meal.to_orm_kwargs() for meal in self.meals] if self.meals else [],
            "tags": [tag.to_orm_kwargs() for tag in self.tags] if self.tags else [],
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "discarded": self.discarded,
            "version": self.version,
        }
