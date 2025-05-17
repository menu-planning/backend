from attrs import frozen

from src.contexts.recipes_catalog.core.domain.entities.recipe import _Recipe
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


@frozen(kw_only=True)
class CreateMeal(Command):
    name: str
    author_id: str
    menu_id: str | None
    recipes: list[_Recipe]
    tags: set[Tag]
    description: str | None
    notes: str | None
    image_url: str | None
