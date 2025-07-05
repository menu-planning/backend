from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_fields import MealCalorieDensity, MealCarboPercentage, MealDescription, MealImageUrl, MealLike, MealName, MealNotes, MealNutriFacts, MealProteinPercentage, MealRecipes, MealTags, MealTotalFatPercentage, MealWeightInGrams
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiEntity
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId, UUIDIdOptional
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel


class ApiMeal(BaseApiEntity[Meal, MealSaModel]):
    """
    A Pydantic model representing and validating a meal encompassing
    details about the meal, its recipes, and additional metadata.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the meal.
        name (str): Name of the meal.
        author_id (str): Identifier of the meal's author.
        menu_id (str, optional): Identifier of the meal's menu.
        recipes (list[ApiRecipe], optional): Recipes in the meal.
        tags (set[ApiTag], optional): Tags associated with the meal.
        description (str, optional): Detailed description.
        notes (str, optional): Additional notes.
        like (bool, optional): Whether the meal is liked.
        image_url (str, optional): URL of an image.
        nutri_facts (ApiNutriFacts, optional): Nutritional facts.
        weight_in_grams (int, optional): Weight in grams.
        calorie_density (float, optional): Calorie density.
        carbo_percentage (float, optional): Percentage of carbohydrates.
        protein_percentage (float, optional): Percentage of proteins.
        total_fat_percentage (float, optional): Percentage of total fat.
    """

    name: MealName
    author_id: UUIDId
    menu_id: UUIDIdOptional
    recipes: MealRecipes
    tags: MealTags
    description: MealDescription
    notes: MealNotes
    like: MealLike
    image_url: MealImageUrl
    nutri_facts: MealNutriFacts
    weight_in_grams: MealWeightInGrams
    calorie_density: MealCalorieDensity
    carbo_percentage: MealCarboPercentage
    protein_percentage: MealProteinPercentage
    total_fat_percentage: MealTotalFatPercentage

    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        """Convert a domain object to an API schema instance."""
        return cls(
            id=domain_obj.id,
            name=domain_obj.name,
            author_id=domain_obj.author_id,
            menu_id=domain_obj.menu_id,
            recipes=[ApiRecipe.from_domain(r) for r in domain_obj.recipes],
            tags=frozenset(ApiTag.from_domain(t) for t in domain_obj.tags),
            description=domain_obj.description,
            notes=domain_obj.notes,
            like=domain_obj.like,
            image_url=domain_obj.image_url,
            nutri_facts=ApiNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
            weight_in_grams=domain_obj.weight_in_grams,
            calorie_density=domain_obj.calorie_density,
            carbo_percentage=domain_obj.carbo_percentage,
            protein_percentage=domain_obj.protein_percentage,
            total_fat_percentage=domain_obj.total_fat_percentage,
            created_at=domain_obj.created_at or datetime.now(),
            updated_at=domain_obj.updated_at or datetime.now(),
            discarded=domain_obj.discarded,
            version=domain_obj.version,
        )

    def to_domain(self) -> Meal:
        """Convert the API schema instance to a domain object."""
        return Meal(
            id=self.id,
            name=self.name,
            author_id=self.author_id,
            menu_id=self.menu_id,
            recipes=[r.to_domain() for r in self.recipes],
            tags=set(t.to_domain() for t in self.tags),
            description=self.description,
            notes=self.notes,
            like=self.like,
            image_url=self.image_url,
            created_at=self.created_at,
            updated_at=self.updated_at,
            discarded=self.discarded,
            version=self.version,
        )

    @classmethod
    def from_orm_model(cls, orm_model: MealSaModel) -> "ApiMeal":
        """Convert an ORM model to an API schema instance."""
        return cls(
            id=orm_model.id,
            name=orm_model.name,
            author_id=orm_model.author_id,
            menu_id=orm_model.menu_id,
            recipes=[ApiRecipe.from_orm_model(r) for r in orm_model.recipes],
            tags=frozenset(ApiTag.from_orm_model(t) for t in orm_model.tags),
            description=orm_model.description,
            notes=orm_model.notes,
            like=orm_model.like,
            image_url=orm_model.image_url,
            nutri_facts=ApiNutriFacts(**asdict(orm_model.nutri_facts)) if orm_model.nutri_facts else None,
            weight_in_grams=orm_model.weight_in_grams,
            calorie_density=orm_model.calorie_density,
            carbo_percentage=orm_model.carbo_percentage,
            protein_percentage=orm_model.protein_percentage,
            total_fat_percentage=orm_model.total_fat_percentage,
            created_at=orm_model.created_at or datetime.now(),
            updated_at=orm_model.updated_at or datetime.now(),
            discarded=orm_model.discarded,
            version=orm_model.version,
        )
    
    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the API schema instance to ORM model kwargs."""
        return {
            "id": self.id,
            "name": self.name,
            "author_id": self.author_id,
            "menu_id": self.menu_id,
            "recipes": [r.to_orm_kwargs() for r in self.recipes],
            "tags": [t.to_orm_kwargs() for t in self.tags],
            "description": self.description,
            "notes": self.notes,
            "like": self.like,
            "image_url": self.image_url,
            "nutri_facts": NutriFactsSaModel(**self.nutri_facts.to_orm_kwargs()) if self.nutri_facts else None,
            "weight_in_grams": self.weight_in_grams,
            "calorie_density": self.calorie_density,
            "carbo_percentage": self.carbo_percentage,
            "protein_percentage": self.protein_percentage,
            "total_fat_percentage": self.total_fat_percentage,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "discarded": self.discarded,
            "version": self.version,
        }
