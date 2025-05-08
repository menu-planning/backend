from attrs import frozen
from src.contexts.products_catalog.shared.domain.value_objects.yield_rate import YieldRate
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.enums import MeasureUnit


@frozen(kw_only=True)
class Ingredient(ValueObject):
    """
    Ingredient is a value object that represents an ingredient in a recipe.

    Attributes:
        name: The name of the ingredient.
        unit: The unit of the ingredient.
        quantity: The quantity of the ingredient.
        position: The position of the ingredient in the recipe
        full_text: The full text of the ingredient.
        product_id: The product id of the ingredient.

    """

    name: str
    unit: MeasureUnit
    quantity: float
    position: int
    full_text: str | None = None
    product_id: str | None = None

    def __mul__(self, other: float) -> "Ingredient":
        if isinstance(other, float):
            return self.replace(
                quantity=self.quantity * other,
            )
        return NotImplemented

    def __add__(self, other: "Ingredient") -> "Ingredient":
        if isinstance(other, Ingredient) and self.unit == other.unit and self.product_id != None and self.product_id == other.product_id:
            return self.replace(
                quantity=self.quantity + other.quantity,
            )
        return NotImplemented
