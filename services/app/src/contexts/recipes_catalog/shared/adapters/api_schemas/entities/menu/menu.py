from pydantic import BaseModel, Field

from src.contexts.recipes_catalog.shared.adapters.api_schemas.pydantic_validators import (
    CreatedAtValue,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.menu_meal import (
    ApiMenuMeal,
)
from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
from src.contexts.recipes_catalog.shared.domain.enums import MealType
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import MenuMeal
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.contexts.shared_kernel.domain.enums import Weekday
from src.logging.logger import logger


class ApiMenu(BaseModel):

    id: str
    author_id: str
    client_id: str | None = None
    meals: dict[tuple[int, Weekday, MealType], ApiMenuMeal] | None = None
    tags: set[ApiTag] = Field(default_factory=set)
    description: str | None = None
    created_at: CreatedAtValue | None = None
    updated_at: CreatedAtValue | None = None
    discarded: bool = False
    version: int = 1

    @classmethod
    def from_domain(cls, domain_obj: Menu) -> "ApiMenu":
        """
        A Pydantic model representing and validating a menu encompassing
        details about the menu, its ingredients, preparation, and
        additional metadata.

        This model is used for input validation and serialization of domain
        objects in API requests and responses.

        Attributes:
            id (str): Unique identifier of the menu.
            author_id (str): Unique identifier of the user who created the menu.
            client_id (str): Unique identifier of the client the menu is associated with.
            meals (dict[tuple[int, Weekday, MealType], ApiMenuMeal]): Dictionary of menu items
                with keys representing the order, weekday, and meal type of the item.
            tags (set[ApiTag]): Set of tags associated with the menu.
            description (str): Description of the menu.
            created_at (CreatedAtValue): Timestamp of when the menu was created.
            updated_at (CreatedAtValue): Timestamp of when the menu was last updated.
            discarded (bool): Flag indicating if the menu is discarded.
            version (int): Version of the menu.

        Args:
            domain_obj (Menu): Domain object to convert to API schema.

        Returns:
            ApiMenu: API schema object representing the domain
                object.

        Raises:
            ValueError: If an error occurs while converting the domain object
                to an API schema.
        """
        try:
            return cls(
                id=domain_obj.id,
                author_id=domain_obj.author_id,
                client_id=domain_obj.client_id,
                meals={
                    (
                        meal.week,
                        meal.weekday,
                        meal.meal_type,
                    ): ApiMenuMeal.from_domain(meal)
                    for meal in domain_obj.meals.values()
                },
                tags=set([ApiTag.from_domain(tag) for tag in domain_obj.tags]),
                description=domain_obj.description,
                created_at=domain_obj.created_at,
                updated_at=domain_obj.updated_at,
                discarded=domain_obj.discarded,
                version=domain_obj.version,
            )
        except Exception as e:
            logger.error(f"Error converting domain object to API schema: {e}")
            raise ValueError("Error converting domain object to API schema") from e

    def to_domain(self) -> Menu:
        """
        Converts the instance to a domain model object.

        Returns:
            Menu: Converted domain model object.
        """
        try:
            return Menu(
                id=self.id,
                author_id=self.author_id,
                client_id=self.client_id,
                meals={
                    (
                        meal.week,
                        meal.weekday,
                        meal.meal_type,
                    ): meal.to_domain()
                    for meal in self.meals.values()
                },
                tags=set([tag.to_domain() for tag in self.tags]),
                description=self.description,
                created_at=self.created_at,
                updated_at=self.updated_at,
                discarded=self.discarded,
                version=self.version,
            )
        except Exception as e:
            logger.error(f"Error converting API schema to domain object: {e}")
            raise ValueError("Error converting API schema to domain object") from e
