from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_fields import MealDescriptionOptional, MealImageUrlOptional, MealNameRequired, MealNotesOptional, MealRecipesOptionalList, MealTagsOptionalFrozenset
from src.contexts.recipes_catalog.core.domain.meal.commands.create_meal import CreateMeal
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired

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
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    name: MealNameRequired
    author_id: UUIDIdRequired
    menu_id: UUIDIdRequired
    recipes: MealRecipesOptionalList
    tags: MealTagsOptionalFrozenset
    description: MealDescriptionOptional
    notes: MealNotesOptional
    image_url: MealImageUrlOptional

    def to_domain(self) -> CreateMeal:
        """Converts the instance to a domain model object for creating a meal."""
        try:
            return CreateMeal(
                name=self.name,
                author_id=self.author_id,
                menu_id=self.menu_id,
                recipes=[recipe.to_domain() for recipe in self.recipes] if self.recipes else None,
                tags=set([tag.to_domain() for tag in self.tags]) if self.tags else None,
                description=self.description,
                notes=self.notes,
                image_url=self.image_url,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateMeal to domain model: {e}")
