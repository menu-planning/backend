from attrs import frozen, field

from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject

@frozen(kw_only=True, hash=True)
class ShoppingItem(ValueObject):
    """
    ShoppingItem is a value object that represents an shopping item in a shopping list.

    """

    quantity: float = field(eq=False, hash=False)

    shopping_name: str
    unit: str
    store_department: str | None = None
    recommended_brands_and_products: str | None = None
    storable: bool | None = None
    edible_yield: float| None = None
    
    def __add__(self, other: "ShoppingItem") -> "ShoppingItem":
        if self == other:
            return self.replace(
                quantity=self.quantity + other.quantity,
            )
        return NotImplemented
