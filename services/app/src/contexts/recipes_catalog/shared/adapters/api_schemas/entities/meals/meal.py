from pydantic import BaseModel, Field
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.pydantic_validators import (
    CreatedAtValue,
)
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.logging.logger import logger


class ApiMeal(BaseModel):
    """
    A Pydantic model representing and validating a meal encompassing
    details about the meal, its ingredients, preparation, and
    additional metadata.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the meal.
        name (str): Name of the meal.
        author_id (str): Identifier of the meal's author.
        recipes (list[ApiRecipe], optional): Recipes in the meal.
        tags (list[ApiTag], optional): Tags associated with the meal.
        menu_id (str, optional): Identifier of the meal's menu.
        description (str, optional): Detailed description.
        notes (str, optional): Additional notes.
        image_url (str, optional): URL of an image.
        created_at (datetime, optional): Creation timestamp.
        updated_at (datetime, optional): Last modification timestamp.
        discarded (bool): Whether the meal is discarded.
        version (int): Version number.

    Raises:
        ValueError: If the instance cannot be converted to a domain model or
            if it this class cannot be instantiated from a domain model.
        ValidationError: If the instance is invalid.

    Methods:
        from_domain(domain_obj: Meal) -> "ApiMeal":
            Creates an instance from a domain model object.
        to_domain() -> Meal:
            Converts the instance to a domain model object.
    """

    id: str
    name: str
    author_id: str
    recipes: list[ApiRecipe] = Field(default_factory=list)
    tags: set[ApiTag] = Field(default_factory=set)
    # menu_id: str | None = None
    description: str | None = None
    notes: str | None = None
    image_url: str | None = None
    created_at: CreatedAtValue | None = None
    updated_at: CreatedAtValue | None = None
    discarded: bool = False
    version: int = 1

    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        """
        Creates an instance from a domain model object.

        Returns:
            ApiMeal: Converted instance.
        """
        try:
            return cls(
                id=domain_obj.id,
                name=domain_obj.name,
                author_id=domain_obj.author_id,
                recipes=[ApiRecipe.from_domain(r) for r in domain_obj.recipes],
                tags=set([ApiTag.from_domain(t) for t in domain_obj.tags]),
                description=domain_obj.description,
                notes=domain_obj.notes,
                image_url=domain_obj.image_url,
                created_at=domain_obj.created_at,
                updated_at=domain_obj.updated_at,
                discarded=domain_obj.discarded,
                version=domain_obj.version,
            )
        except Exception as e:
            logger.error(f"Error converting domain object to API schema: {e}")
            raise ValueError("Error converting domain object to API schema") from e

    def to_domain(self) -> Meal:
        """
        Converts the instance to a domain model object.

        Returns:
            Meal: Converted domain model object.
        """
        try:
            return Meal(
                id=self.id,
                name=self.name,
                author_id=self.author_id,
                recipes=[r.to_domain() for r in self.recipes],
                tags=set([t.to_domain() for t in self.tags]),
                description=self.description,
                notes=self.notes,
                image_url=self.image_url,
                created_at=self.created_at,
                updated_at=self.updated_at,
                discarded=self.discarded,
                version=self.version,
            )
        except Exception as e:
            logger.error(f"Error converting API schema to domain object: {e}")
            raise ValueError("Error converting API schema to domain object") from e
