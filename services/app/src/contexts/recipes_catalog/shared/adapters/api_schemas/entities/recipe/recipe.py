from pydantic import BaseModel, Field, field_serializer

from src.contexts.recipes_catalog.shared.adapters.api_schemas.pydantic_validators import (
    AverageRatingValue,
    CreatedAtValue,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.ingredient import (
    ApiIngredient,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.rating import (
    ApiRating,
)
from src.contexts.recipes_catalog.shared.domain.entities import _Recipe
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiRecipe(BaseModel):
    """
    A Pydantic model representing and validating a recipe encompassing
    details about the recipe, its ingredients, preparation, and
    additional metadata.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the recipe.
        name (str): Name of the recipe.
        description (str): Detailed description.
        ingredients (list[ApiIngredient], optional): Detailed list of
            ingredients.
        instructions (str): Detailed instructions.
        author_id (str): Identifier of the recipe's author.
        utensils (str, optional): Comma-separated list of utensils.
        notes (str, optional): Additional notes.
        ... (additional common attributes for recipe details) ...
        nutri_facts (ApiNutriFacts, optional): Nutritional facts of the recipe.
        ratings (list[ApiRating]): User ratings of the recipe.
        ... (other metadata attributes) ...

    Raises:
        ValueError: If the instance cannot be converted to a domain model or
            if it this class cannot be instantiated from a domain model.
        ValidationError: If the instance is invalid.

    Methods:
        from_domain(domain_obj: Recipe) -> "ApiRecipe":
            Creates an instance from a domain model object.
        to_domain() -> Recipe:
            Converts the instance to a domain model object.
    """

    id: str
    name: str
    ingredients: list[ApiIngredient] = Field(default_factory=list)
    instructions: str
    author_id: str
    meal_id: str | None = None
    description: str | None = None
    utensils: str | None = None
    total_time: int | None = None
    notes: str | None = None
    tags: set[ApiTag] = Field(default_factory=set)
    privacy: Privacy = Privacy.PRIVATE
    ratings: list[ApiRating] | None = Field(default_factory=list)
    nutri_facts: ApiNutriFacts | None = None
    weight_in_grams: int | None = None
    image_url: str | None = None
    created_at: CreatedAtValue | None = None
    updated_at: CreatedAtValue | None = None
    discarded: bool = False
    version: int = 1
    average_taste_rating: AverageRatingValue | None = None
    average_convenience_rating: AverageRatingValue | None = None

    @field_serializer("tags")
    def serialize_tags(self, tags: set[str], _info):
        return list(tags)

    @field_serializer("privacy")
    def serialize_privacy(self, privacy: Privacy, _info):
        return privacy.value

    # def model_dump(self, *args, **kwargs):
    #     data = super().model_dump(*args, **kwargs)
    #     # Convert sets to lists in the output
    #     for key, value in data.items():
    #         if isinstance(value, set):
    #             data[key] = list(value)
    #     return data

    @classmethod
    def from_domain(cls, domain_obj: _Recipe) -> "ApiRecipe":
        """Creates an instance of `ApiRecipe` from a domain model object."""
        try:
            return cls(
                id=domain_obj.id,
                name=domain_obj.name,
                meal_id=domain_obj.meal_id,
                description=domain_obj.description,
                ingredients=[
                    ApiIngredient.from_domain(i) for i in domain_obj.ingredients
                ],
                instructions=domain_obj.instructions,
                author_id=domain_obj.author_id,
                utensils=domain_obj.utensils,
                total_time=domain_obj.total_time,
                notes=domain_obj.notes,
                tags=set([ApiTag.from_domain(i) for i in domain_obj.tags]),
                privacy=domain_obj.privacy,
                ratings=(
                    [ApiRating.from_domain(r) for r in domain_obj.ratings]
                    if domain_obj.ratings
                    else []
                ),
                nutri_facts=(
                    ApiNutriFacts.from_domain(domain_obj.nutri_facts)
                    if domain_obj.nutri_facts
                    else None
                ),
                weight_in_grams=domain_obj.weight_in_grams,
                image_url=domain_obj.image_url,
                created_at=domain_obj.created_at,
                updated_at=domain_obj.updated_at,
                discarded=domain_obj.discarded,
                version=domain_obj.version,
                average_taste_rating=domain_obj.average_taste_rating,
                average_convenience_rating=domain_obj.average_convenience_rating,
            )
        except Exception as e:
            raise ValueError(f"Failed to build ApiRecipe from domain instance: {e}")

    def to_domain(self) -> _Recipe:
        """Converts the instance to a domain model object."""
        try:
            return _Recipe(
                id=self.id,
                name=self.name,
                meal_id=self.meal_id,
                description=self.description,
                ingredients=(
                    [i.to_domain() for i in self.ingredients]
                    if self.ingredients
                    else []
                ),
                instructions=self.instructions,
                author_id=self.author_id,
                utensils=self.utensils,
                total_time=self.total_time,
                notes=self.notes,
                tags=(set([i.to_domain() for i in self.tags]) if self.tags else set()),
                privacy=self.privacy,
                ratings=[r.to_domain() for r in self.ratings] if self.ratings else [],
                nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
                weight_in_grams=self.weight_in_grams,
                image_url=self.image_url,
                created_at=self.created_at,
                updated_at=self.updated_at,
                discarded=self.discarded,
                version=self.version,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiRecipe to domain model: {e}")
