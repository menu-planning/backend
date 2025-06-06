from typing import Optional, Dict, Any
from typing_extensions import Annotated

from pydantic import TypeAdapter

from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseValueObject
from src.contexts.recipes_catalog.core.domain.value_objects.ingredient import Ingredient
from src.contexts.seedwork.shared.adapters.api_schemas.fields import UUIDIdOptional
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.recipes_catalog.core.adapters.ORM.sa_models.recipe.ingredient import IngredientSaModel
from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.fields import (
    IngredientName,
    IngredientQuantity,
    IngredientPosition,
)


class ApiIngredient(BaseValueObject[Ingredient, IngredientSaModel]):
    """
    A Pydantic model representing and validating a recipe ingredient.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): The name of the ingredient.
        quantity (float): The quantity of the ingredient.
        position (int): The position of the ingredient in the recipe.
        unit (MeasureUnit): The unit of measurement for the quantity of the ingredient.
        full_text (str, optional): The full textual description of the ingredient, if available.
        product_id (str, optional): The identifier of the food item associated with the ingredient, if applicable.
    """

    name: IngredientName
    quantity: IngredientQuantity
    unit: MeasureUnit
    position: IngredientPosition
    full_text: Optional[str] = None
    product_id: UUIDIdOptional

    @classmethod
    def from_domain(cls, domain_obj: Ingredient) -> "ApiIngredient":
        """Creates an instance of `ApiIngredient` from a domain model object."""
        if domain_obj is None:
            return None
        return cls(
            name=domain_obj.name,
            quantity=domain_obj.quantity,
            unit=domain_obj.unit,
            full_text=domain_obj.full_text,
            product_id=domain_obj.product_id,
            position=domain_obj.position,
        )

    def to_domain(self) -> Ingredient:
        """Converts the instance to a domain model object."""
        return Ingredient(
            name=self.name,
            quantity=self.quantity,
            unit=MeasureUnit(self.unit),
            full_text=self.full_text,
            product_id=self.product_id,
            position=self.position,
        )

    @classmethod
    def from_orm_model(cls, orm_model: IngredientSaModel) -> "ApiIngredient":
        """Creates an instance of `ApiIngredient` from an ORM model."""
        return cls(
            name=orm_model.name,
            quantity=orm_model.quantity,
            unit=MeasureUnit(orm_model.unit),
            full_text=orm_model.full_text,
            product_id=orm_model.product_id,
            position=orm_model.position,
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Converts the instance to ORM model kwargs."""
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "full_text": self.full_text,
            "product_id": self.product_id,
            "position": self.position,
        }

IngredientListAdapter = TypeAdapter(list[ApiIngredient])