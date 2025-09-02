"""Domain command to create a meal aggregate."""
from attrs import field, frozen
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.seedwork.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


@frozen(kw_only=True)
class CreateMeal(Command):
    """Command to create a new meal.

    Args:
        name: Name of the meal
        author_id: ID of the user creating the meal
        menu_id: ID of the menu to add the meal to
        recipes: Optional list of recipes for the meal
        tags: Optional set of tags to associate with the meal
        description: Optional description of the meal
        notes: Optional notes about the meal
        image_url: Optional URL to meal image
        meal_id: Unique identifier for the meal (auto-generated if not provided)
    """
    name: str
    author_id: str
    menu_id: str
    recipes: list[_Recipe] | None = None
    tags: frozenset[Tag] | None = None
    description: str | None = None
    notes: str | None = None
    image_url: str | None = None
    meal_id: str = field(factory=Command.generate_uuid)
