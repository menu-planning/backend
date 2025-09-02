"""Value object representing an ingredient in a recipe."""
from attrs import frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.enums import MeasureUnit


@frozen(kw_only=True)
class Ingredient(ValueObject):
    """Value object representing an ingredient in a recipe.

    Invariants:
        - Position must be non-negative
        - Quantity must be positive
        - Name must be non-empty

    Notes:
        Immutable. Equality by value (name, unit, quantity, position, full_text, product_id).
    """
    name: str
    unit: MeasureUnit
    quantity: float
    position: int
    full_text: str | None = None
    product_id: str | None = None

    def __mul__(self, other: float) -> "Ingredient":
        """Scale ingredient quantity by a multiplier.

        Args:
            other: Multiplier to apply to quantity.

        Returns:
            New ingredient with scaled quantity.

        Raises:
            TypeError: When other is not a float.
        """
        if isinstance(other, float):
            return self.replace(
                quantity=self.quantity * other,
            )
        return NotImplemented

    def __add__(self, other: "Ingredient") -> "Ingredient":
        """Sum ingredient quantities when same unit and product ID.

        Args:
            other: Ingredient to add to this one.

        Returns:
            New ingredient with summed quantities.

        Raises:
            TypeError: When ingredients have different units or product IDs.
        """
        if isinstance(other, Ingredient) and self.unit == other.unit and self.product_id != None and self.product_id == other.product_id:
            return self.replace(
                quantity=self.quantity + other.quantity,
            )
        return NotImplemented
