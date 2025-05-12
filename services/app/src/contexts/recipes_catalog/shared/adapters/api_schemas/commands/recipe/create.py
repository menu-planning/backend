from pydantic import BaseModel, Field
from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.ingredient import (
    ApiIngredient,
)
from src.contexts.recipes_catalog.shared.domain.commands import CreateRecipe
from src.contexts.recipes_catalog.shared.domain.entities.recipe import _Recipe
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiCreateRecipe(BaseModel):
    """
    A Pydantic model representing and validating the the data required
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
        tags (set[ApiTag], optional): Detailed set of tags.
        privacy (Privacy): Privacy setting of the recipe.
        nutri_facts (ApiNutriFacts, optional): Nutritional facts of the
            recipe.
        image_url (str, optional): URL of an image of the recipe.

    Methods:
        to_domain() -> AddRecipe:
            Converts the instance to a domain model object for adding a recipe.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    name: str
    instructions: str
    author_id: str
    meal_id: str
    ingredients: list[ApiIngredient] = Field(default_factory=list)
    description: str | None = None
    utensils: str | None = None
    total_time: int | None = None
    notes: str | None = None
    tags: set[ApiTag] = Field(default_factory=set)
    privacy: Privacy = Privacy.PRIVATE
    nutri_facts: ApiNutriFacts | None = None
    weight_in_grams: int | None = None
    image_url: str | None = None

    # TODO: check if has tests
    def to_domain(self) -> CreateRecipe:
        """Converts the instance to a domain model object for adding a recipe."""
        try:
            return CreateRecipe(
                name=self.name,
                instructions=self.instructions,
                author_id=self.author_id,
                meal_id=self.meal_id,
                ingredients=[i.to_domain() for i in self.ingredients],
                description=self.description,
                utensils=self.utensils,
                total_time=self.total_time,
                notes=self.notes,
                tags=set([t.to_domain() for t in self.tags]),
                privacy=self.privacy,
                nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
                weight_in_grams=self.weight_in_grams,
                image_url=self.image_url,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateRecipeto domain model: {e}")

    @classmethod
    def from_recipe(cls, recipe: _Recipe) -> "ApiCreateRecipe":
        """Converts a domain recipe object to an instance of this class."""
        return cls(
            name=recipe.name,
            instructions=recipe.instructions,
            author_id=recipe.author_id,
            meal_id=recipe.meal_id,
            ingredients=[ApiIngredient.from_domain(i) for i in recipe.ingredients],
            description=recipe.description,
            utensils=recipe.utensils,
            total_time=recipe.total_time,
            notes=recipe.notes,
            tags=set([ApiTag.from_domain(i) for i in recipe.tags]),
            privacy=recipe.privacy,
            nutri_facts=(
                ApiNutriFacts.from_domain(recipe.nutri_facts)
                if recipe.nutri_facts
                else None
            ),
            weight_in_grams=recipe.weight_in_grams,
            image_url=recipe.image_url,
        )
