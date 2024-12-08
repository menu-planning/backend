from pydantic import BaseModel, Field
from src.contexts.recipes_catalog.shared.adapters.api_schemas.pydantic_validators import (
    MonthValue,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.ingredient import (
    ApiIngredient,
)
from src.contexts.recipes_catalog.shared.domain.commands import CreateRecipe
from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.allergen import (
    ApiAllergen,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.cuisine import (
    ApiCuisine,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.flavor import (
    ApiFlavor,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.texture import (
    ApiTexture,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)


class ApiCreateRecipe(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a new recipe via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the recipe.
        description (str): Detailed description of the recipe.
        ingredients (str): (list[ApiIngredient], optional): Detailed list of
            ingredients.
        instructions (str):Detailed instructions.
        author (ApiAuthor): The recipe's author.
        utensils (str, optional): Comma-separated list of utensils.
        total_time (int, optional): Total preparation and cooking time in
            minutes.
        servings (int, optional): Number of servings the recipe yields.
        notes (str, optional): Additional notes about the recipe.
        diet_types_ids (set[str], optional): Set of applicable diet types ids
        categoryies_ids (set[str], optional): Set of recipe categories ids
        cuisine (str, optional): The cuisine of the recipe
        flavor (str, optional): Description of the recipe's
            flavor profile.
        texture (str, optional): Description of the recipe's
            texture profile.
        meal_planning_ids (str, optional): Suitable for meal planning purposes.
        privacy (Privacy): Privacy setting of the recipe.
        nutri_facts (ApiNutriFacts, optional): Nutritional facts of the
            recipe.
        season (set[MonthValue], optional): Applicable seasons for the
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
    author_id: str | None = None
    meal_id: str | None = None
    ingredients: list[ApiIngredient] = Field(default_factory=list)
    description: str | None = None
    utensils: str | None = None
    total_time: int | None = None
    servings: int | None = None
    notes: str | None = None
    diet_types_ids: set[str] = Field(default_factory=set)
    categories_ids: set[str] = Field(default_factory=set)
    cuisine: str | None = None
    flavor: str | None = None
    texture: str | None = None
    allergens: set[str] = Field(default_factory=set)
    meal_planning_ids: set[str] = Field(default_factory=set)
    privacy: Privacy = Privacy.PRIVATE
    nutri_facts: ApiNutriFacts | None = None
    weight_in_grams: int | None = None
    season: set[MonthValue] = Field(default_factory=set)
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
                servings=self.servings,
                notes=self.notes,
                diet_types_ids=self.diet_types_ids,
                categories_ids=self.categories_ids,
                cuisine=(
                    ApiCuisine(name=self.cuisine).to_domain() if self.cuisine else None
                ),
                flavor=ApiFlavor(name=self.flavor).to_domain() if self.flavor else None,
                texture=(
                    ApiTexture(name=self.texture).to_domain() if self.texture else None
                ),
                allergens={ApiAllergen(name=a).to_domain() for a in self.allergens},
                meal_planning_ids=self.meal_planning_ids,
                privacy=self.privacy,
                nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
                weight_in_grams=self.weight_in_grams,
                season=self.season,
                image_url=self.image_url,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateRecipeto domain model: {e}")

    @classmethod
    def from_recipe(cls, recipe: Recipe) -> "ApiCreateRecipe":
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
            servings=recipe.servings,
            notes=recipe.notes,
            diet_types_ids=recipe.diet_types_ids,
            categories_ids=recipe.categories_ids,
            cuisine=recipe.cuisine.name if recipe.cuisine else None,
            flavor=recipe.flavor.name if recipe.flavor else None,
            texture=recipe.texture.name if recipe.texture else None,
            allergens={a.name for a in recipe.allergens},
            meal_planning_ids=recipe.meal_planning_ids,
            privacy=recipe.privacy,
            nutri_facts=(
                ApiNutriFacts.from_domain(recipe.nutri_facts)
                if recipe.nutri_facts
                else None
            ),
            weight_in_grams=recipe.weight_in_grams,
            season=set([i.value for i in recipe.season]),
            image_url=recipe.image_url,
        )
