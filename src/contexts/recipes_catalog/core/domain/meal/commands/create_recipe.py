"""Domain command to create a recipe within a meal aggregate."""
from attrs import field, frozen
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.seedwork.domain.commands.command import Command
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


@frozen(kw_only=True)
class CreateRecipe(Command):
    """Command to create a new recipe.

    Args:
        name: Name of the recipe
        instructions: Cooking instructions for the recipe
        author_id: ID of the user creating the recipe
        meal_id: ID of the meal the recipe belongs to
        ingredients: Optional list of ingredients for the recipe
        description: Optional description of the recipe
        utensils: Optional list of required utensils
        total_time: Optional cooking time in minutes
        notes: Optional additional notes about the recipe
        tags: Optional set of tags to associate with the recipe
        privacy: Privacy level of the recipe (defaults to PRIVATE)
        nutri_facts: Optional nutritional information
        weight_in_grams: Optional weight of the final dish
        image_url: Optional URL to recipe image
        recipe_id: Unique identifier for the recipe (auto-generated if not provided)
    """
    name: str
    instructions: str
    author_id: str
    meal_id: str
    ingredients: list[Ingredient] | None = None
    description: str | None = None
    utensils: str | None = None
    total_time: int | None = None
    notes: str | None = None
    tags: frozenset[Tag] | None = None
    privacy: Privacy = Privacy.PRIVATE
    nutri_facts: NutriFacts | None = None
    weight_in_grams: int | None = None
    image_url: str | None = None
    recipe_id: str = field(factory=Command.generate_uuid)
