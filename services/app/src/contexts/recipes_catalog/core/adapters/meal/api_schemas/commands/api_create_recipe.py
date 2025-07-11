from typing import Any
from pydantic import HttpUrl, ValidationInfo, field_validator
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_fields import RecipeDescriptionOptional, RecipeImageUrlOptional, RecipeIngredientsOptionalFrozenset, RecipeInstructionsRequired, RecipeNameRequired, RecipeNotesOptional, RecipeNutriFactsOptional, RecipePrivacyOptional, RecipeTagsOptionalFrozenset, RecipeTotalTimeOptional, RecipeUtensilsOptional, RecipeWeightInGramsOptional
from src.contexts.recipes_catalog.core.domain.meal.commands.create_recipe import CreateRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.pydantic_validators import validate_tags_have_correct_author_id_and_type as validate_tags

class ApiCreateRecipe(BaseApiCommand[CreateRecipe]):
    """
    A Pydantic model representing and validating the data required
    to add a new recipe via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the recipe.
        description (str): Detailed description of the recipe.
        ingredients (list[ApiIngredient], optional): Detailed list of
            ingredients.
        instructions (str):Detailed instructions.
        author_id (str): The recipe's author id.
        utensils (str, optional): Comma-separated list of utensils.
        total_time (int, optional): Total preparation and cooking time in
            minutes.
        notes (str, optional): Additional notes about the recipe.
        tags (frozenset[ApiTag], optional): Detailed frozenset of tags.
        privacy (Privacy): Privacy setting of the recipe.
        nutri_facts (ApiNutriFacts, optional): Nutritional facts of the
            recipe.
        image_url (str, optional): URL of an image of the recipe.

    Methods:
        to_domain() -> CreateRecipe:
            Converts the instance to a domain model object for adding a recipe.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    name: RecipeNameRequired
    instructions: RecipeInstructionsRequired
    author_id: UUIDIdRequired
    meal_id: UUIDIdRequired
    ingredients: RecipeIngredientsOptionalFrozenset
    description: RecipeDescriptionOptional
    utensils: RecipeUtensilsOptional
    total_time: RecipeTotalTimeOptional
    notes: RecipeNotesOptional
    tags: RecipeTagsOptionalFrozenset
    privacy: RecipePrivacyOptional
    nutri_facts: RecipeNutriFactsOptional
    weight_in_grams: RecipeWeightInGramsOptional
    image_url: HttpUrl | None = None

    @field_validator('tags', mode='before')
    @classmethod
    def validate_tags_have_correct_author_id_and_type(cls, v: Any, info: ValidationInfo) -> Any:
        """
        Validate tags field. If a dict is provided without 'type' and 'author_id',
        add them with default values and convert to ApiTag.
        """
        return validate_tags(v, 'recipe', info)

    def to_domain(self) -> CreateRecipe:
        """Converts the instance to a domain model object for adding a recipe."""
        try:
            return CreateRecipe(
                name=self.name,
                instructions=self.instructions,
                author_id=self.author_id,
                meal_id=self.meal_id,
                ingredients=[i.to_domain() for i in self.ingredients] if self.ingredients else None,
                description=self.description,
                utensils=self.utensils,
                total_time=self.total_time,
                notes=self.notes,
                tags=set([t.to_domain() for t in self.tags]) if self.tags else None,
                privacy=Privacy(self.privacy) if self.privacy else Privacy.PRIVATE,
                nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
                weight_in_grams=self.weight_in_grams,
                image_url=str(self.image_url) if self.image_url else None,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateRecipe to domain model: {e}")