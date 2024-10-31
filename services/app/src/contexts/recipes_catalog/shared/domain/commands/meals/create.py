from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class CreateMeal(Command):
    name: str
    author_id: str
    recipes: list[Recipe]
    menu_id: str | None
    description: str | None
    notes: str | None
    image_url: str | None
