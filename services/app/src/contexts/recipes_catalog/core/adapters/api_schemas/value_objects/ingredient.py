from pydantic import BaseModel, field_serializer
from src.contexts.recipes_catalog.core.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit


class ApiIngredient(BaseModel):
    """
    A Pydantic model representing and validating a recipe ingredient.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): The unique identifier of the ingredient.
        name (str): The name of the ingredient.
        quantity (float): The quantity of the ingredient.
        position (int): The position of the ingredient in the recipe.
        unit (Unit): The unit of measurement for the quantity of the ingredient.
        full_text (str, optional): The full textual description of the ingredient, if available.
        product_id (str, optional): The identifier of the food item associated with the ingredient, if applicable.

    Methods:
        from_domain(domain_obj: Ingredient) -> "ApiIngredient":
            Creates an instance of `ApiIngredient` from a domain model object.
            Returns `None` if `domain_obj` is `None`.
        to_domain() -> Ingredient:
            Converts the instance to a domain model object.

    Raises:
        ValueError: If the instance cannot be converted to a domain model or
            if it this class cannot be instantiated from a domain model.
        ValidationError: If the instance is invalid.

    Example:
        ApiIngredient can be used to serialize ingredient data for API responses or to parse
        ingredient data received from API requests.
    """

    name: str
    quantity: float
    unit: MeasureUnit
    position: int
    full_text: str | None = None
    product_id: str | None = None

    @field_serializer("unit")
    def serialize_unit(self, unit: MeasureUnit, _info):
        """Serializes the unit to a string."""
        return unit.value
    
    @classmethod
    def from_domain(cls, domain_obj: Ingredient) -> "ApiIngredient":
        """Creates an instance of `ApiIngredient` from a domain model object."""
        try:
            return cls(
                name=domain_obj.name,
                quantity=domain_obj.quantity,
                unit=domain_obj.unit,
                full_text=domain_obj.full_text,
                product_id=domain_obj.product_id,
                position=domain_obj.position,
            )
        except Exception as e:
            raise ValueError(f"Failed to build ApiIngredient from domain instance: {e}")

    def to_domain(self) -> Ingredient:
        """Converts the instance to a domain model object."""
        try:
            return Ingredient(
                name=self.name,
                quantity=self.quantity,
                unit=self.unit,
                full_text=self.full_text,
                product_id=self.product_id,
                position=self.position,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiIngredient to domain model: {e}")
