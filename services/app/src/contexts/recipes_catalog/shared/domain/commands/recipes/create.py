from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.enums import Month, Privacy
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


@frozen(kw_only=True)
class CreateRecipe(Command):
    name: str
    ingredients: list[Ingredient]
    instructions: str
    author_id: str
    description: str | None = None
    utensils: str | None = None
    total_time: int | None = None
    servings: int | None = None
    notes: str | None = None
    diet_types_ids: set[str] | None = None
    categories_ids: set[str] | None = None
    cuisine: Cuisine | None = None
    flavor: Flavor | None = None
    texture: Texture | None = None
    meal_planning_ids: set[str] | None = None
    privacy: Privacy = Privacy.PRIVATE
    nutri_facts: NutriFacts | None = None
    weight_in_grams: int | None = None
    season: set[Month] | None = None
    image_url: str | None = None
