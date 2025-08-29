from typing import Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient_fields import (
    IngredientFullTextOptional,
    IngredientNameRequired,
    IngredientPositionRequired,
    IngredientQuantityRequired,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    UUIDIdOptional,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit


class ApiIngredient(BaseApiValueObject[Ingredient, IngredientSaModel]):
    """
    A Pydantic model representing and validating a recipe ingredient.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): The name of the ingredient.
        quantity (float): The quantity of the ingredient.
        position (int): The position of the ingredient in the recipe.
        unit (MeasureUnit): The unit of measurement for the quantity of the ingredient.
        full_text (str, optional): The full textual description of the ingredient,
                                   if available.
        product_id (str, optional): The identifier of the food item associated with
            the ingredient, if applicable.
    """

    name: IngredientNameRequired
    quantity: IngredientQuantityRequired
    unit: MeasureUnit
    position: IngredientPositionRequired
    full_text: IngredientFullTextOptional
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

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Converts the instance to ORM model kwargs."""
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "full_text": self.full_text,
            "product_id": self.product_id,
            "position": self.position,
        }
