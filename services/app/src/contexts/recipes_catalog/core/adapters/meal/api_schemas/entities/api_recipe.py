from datetime import datetime
from typing import Any, Dict
from pydantic import TypeAdapter, field_validator

from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_fields import RecipeAverageConvenienceRating, RecipeAverageTasteRating, RecipeDescription, RecipeImageUrl, RecipeIngredients, RecipeInstructions, RecipeName, RecipeNotes, RecipeNutriFacts, RecipePrivacy, RecipeRatings, RecipeTags, RecipeTotalTime, RecipeUtensils, RecipeWeightInGrams
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient, IngredientListAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating, RatingListAdapter
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseEntity
from src.contexts.seedwork.shared.adapters.api_schemas.fields import UUIDId
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag, TagSetAdapter
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts import NutriFactsSaModel


class ApiRecipe(BaseEntity[_Recipe, RecipeSaModel]):
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
    """

    id: UUIDId
    name: RecipeName
    instructions: RecipeInstructions
    author_id: UUIDId
    meal_id: UUIDId
    ingredients: RecipeIngredients
    description: RecipeDescription
    utensils: RecipeUtensils
    total_time: RecipeTotalTime
    notes: RecipeNotes
    tags: RecipeTags
    privacy: RecipePrivacy
    ratings: RecipeRatings
    nutri_facts: RecipeNutriFacts
    weight_in_grams: RecipeWeightInGrams
    image_url: RecipeImageUrl
    average_taste_rating: RecipeAverageTasteRating
    average_convenience_rating: RecipeAverageConvenienceRating

    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v: list[ApiIngredient]) -> list[ApiIngredient]:
        """Validate that ingredients are unique by name."""
        if not v:
            return v
        return IngredientListAdapter.validate_python(v)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: set[ApiTag]) -> set[ApiTag]:
        """Validate tags using TypeAdapter."""
        return TagSetAdapter.validate_python(v)

    @field_validator('ratings')
    @classmethod
    def validate_ratings(cls, v: list[ApiRating]) -> list[ApiRating]:
        """Validate ratings using TypeAdapter."""
        return RatingListAdapter.validate_python(v)
    
    @classmethod
    def from_domain(cls, domain_obj: _Recipe) -> "ApiRecipe":
        """Convert a domain object to an API schema instance."""
        return cls(
            id=domain_obj.id,
            name=domain_obj.name,
            meal_id=domain_obj.meal_id,
            description=domain_obj.description,
            ingredients=IngredientListAdapter.validate_python([ApiIngredient.from_domain(i) for i in domain_obj.ingredients]),
            instructions=domain_obj.instructions,
            author_id=domain_obj.author_id,
            utensils=domain_obj.utensils,
            total_time=domain_obj.total_time,
            notes=domain_obj.notes,
            tags=TagSetAdapter.validate_python(set(ApiTag.from_domain(i) for i in domain_obj.tags)),
            privacy=domain_obj.privacy,
            ratings=RatingListAdapter.validate_python([ApiRating.from_domain(r) for r in domain_obj.ratings] if domain_obj.ratings else []),
            nutri_facts=ApiNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
            weight_in_grams=domain_obj.weight_in_grams,
            image_url=domain_obj.image_url,
            created_at=domain_obj.created_at or datetime.now(),
            updated_at=domain_obj.updated_at or datetime.now(),
            discarded=domain_obj.discarded,
            version=domain_obj.version,
            average_taste_rating=domain_obj.average_taste_rating,
            average_convenience_rating=domain_obj.average_convenience_rating,
        )

    def to_domain(self) -> _Recipe:
        """Convert the API schema instance to a domain object."""
        return _Recipe(
            id=self.id,
            name=self.name,
            meal_id=self.meal_id,
            description=self.description,
            ingredients=[i.to_domain() for i in self.ingredients],
            instructions=self.instructions,
            author_id=self.author_id,
            utensils=self.utensils,
            total_time=self.total_time,
            notes=self.notes,
            tags=set(i.to_domain() for i in self.tags),
            privacy=self.privacy,
            ratings=[r.to_domain() for r in self.ratings],
            nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
            weight_in_grams=self.weight_in_grams,
            image_url=self.image_url,
            created_at=self.created_at,
            updated_at=self.updated_at,
            discarded=self.discarded,
            version=self.version,
        )

    @classmethod
    def from_orm_model(cls, orm_model: RecipeSaModel) -> "ApiRecipe":
        """Convert an ORM model to an API schema instance."""
        return cls(
            id=orm_model.id,
            name=orm_model.name,
            meal_id=orm_model.meal_id,
            description=orm_model.description,
            ingredients=IngredientListAdapter.validate_python([ApiIngredient.from_orm_model(i) for i in orm_model.ingredients]),
            instructions=orm_model.instructions,
            author_id=orm_model.author_id,
            utensils=orm_model.utensils,
            total_time=orm_model.total_time,
            notes=orm_model.notes,
            tags=TagSetAdapter.validate_python(set(ApiTag.from_orm_model(i) for i in orm_model.tags)),
            privacy=Privacy(orm_model.privacy) if orm_model.privacy else Privacy.PRIVATE,
            ratings=RatingListAdapter.validate_python([ApiRating.from_orm_model(r) for r in orm_model.ratings] if orm_model.ratings else []),
            nutri_facts=ApiNutriFacts(**orm_model.nutri_facts.__dict__) if orm_model.nutri_facts else None,
            weight_in_grams=orm_model.weight_in_grams,
            image_url=orm_model.image_url,
            created_at=orm_model.created_at or datetime.now(),
            updated_at=orm_model.updated_at or datetime.now(),
            discarded=orm_model.discarded,
            version=orm_model.version,
            average_taste_rating=orm_model.average_taste_rating,
            average_convenience_rating=orm_model.average_convenience_rating,
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the API schema instance to ORM model kwargs."""
        return {
            "id": self.id,
            "name": self.name,
            "meal_id": self.meal_id,
            "description": self.description,
            "ingredients": [i.to_orm_kwargs() for i in self.ingredients],
            "instructions": self.instructions,
            "author_id": self.author_id,
            "utensils": self.utensils,
            "total_time": self.total_time,
            "notes": self.notes,
            "tags": [i.to_orm_kwargs() for i in self.tags],
            "privacy": self.privacy.value,
            "ratings": [r.to_orm_kwargs() for r in self.ratings],
            "nutri_facts": NutriFactsSaModel(**self.nutri_facts.model_dump()) if self.nutri_facts else None,
            "weight_in_grams": self.weight_in_grams,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "discarded": self.discarded,
            "version": self.version,
            "average_taste_rating": self.average_taste_rating,
            "average_convenience_rating": self.average_convenience_rating,
        }

RecipeListAdapter = TypeAdapter(list[ApiRecipe])