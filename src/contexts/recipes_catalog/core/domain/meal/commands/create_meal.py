from attrs import field, frozen
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


@frozen(kw_only=True)
class CreateMeal(Command):
    name: str
    author_id: str
    menu_id: str
    recipes: list[_Recipe] | None = None
    tags: frozenset[Tag] | None = None
    description: str | None = None
    notes: str | None = None
    image_url: str | None = None
    meal_id: str = field(factory=Command.generate_uuid)  # Default to a new UUID if not provided
