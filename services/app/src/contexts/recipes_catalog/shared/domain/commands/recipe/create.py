from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


@frozen(kw_only=True)
class CreateRecipe(Command):
    name: str
    ingredients: list[Ingredient]
    instructions: str
    author_id: str
    meal_id: str
    description: str | None = None
    utensils: str | None = None
    total_time: int | None = None
    notes: str | None = None
    tags: set[Tag] | None = None
    privacy: Privacy = Privacy.PRIVATE
    nutri_facts: NutriFacts | None = None
    weight_in_grams: int | None = None
    image_url: str | None = None
