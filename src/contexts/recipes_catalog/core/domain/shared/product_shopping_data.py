"""Product shopping data value objects for recipes catalog domain."""
from attrs import frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True, hash=True)
class ProductShoppingData(ValueObject):
    """Value object representing shopping information for a product.

    Invariants:
        - All numeric values must be non-negative when present
        - Conservation days must be positive when present

    Notes:
        Immutable. Equality by value (all fields).
    """

    product_id: str | None = None
    shopping_name: str | None = None
    store_department_name: str | None = None
    recommended_brands_and_products: str | None = None
    edible_yield: float | None = None
    kg_per_unit: float | None = None
    liters_per_kg: float | None = None
    nutrition_group: str | None = None
    cooking_factor: float | None = None
    conservation_days: int | None = None
    substitutes: str | None = None


@frozen(kw_only=True, hash=True)
class ShoppingItem(ValueObject):
    """Value object representing a shopping list item.

    Invariants:
        - Quantity must be positive
        - Unit must be non-empty

    Notes:
        Immutable. Equality by value (quantity, unit, product_data).
    """

    quantity: float
    unit: str
    product_data: ProductShoppingData
