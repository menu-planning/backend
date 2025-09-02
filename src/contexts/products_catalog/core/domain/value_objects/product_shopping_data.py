"""Value objects for shopping-related product data and items."""
from attrs import frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True, hash=True)
class ProductShoppingData(ValueObject):
    """Immutable data used to inform shopping list generation.
    
    Invariants:
        - edible_yield must be > 0 if provided
        - kg_per_unit must be > 0 if provided
        - liters_per_kg must be > 0 if provided
        - cooking_factor must be > 0 if provided
        - conservation_days must be >= 0 if provided
    
    Attributes:
        product_id: Unique identifier of the product.
        shopping_name: Name to display on shopping lists.
        store_department_name: Store department where product is found.
        recommended_brands_and_products: Recommended alternatives.
        edible_yield: Percentage of product that is edible.
        kg_per_unit: Weight conversion factor.
        liters_per_kg: Volume conversion factor.
        nutrition_group: Nutritional classification group.
        cooking_factor: Factor for cooking calculations.
        conservation_days: Days the product can be stored.
        substitutes: Alternative products.
    
    Notes:
        Immutable. Equality by value (all attributes).
        Used for generating shopping lists and recipe calculations.
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
    """A shopping list item with quantity, unit, and product data.
    
    Invariants:
        - quantity must be > 0
        - unit must be non-empty
        - product_data must be valid ProductShoppingData
    
    Attributes:
        quantity: Amount to purchase.
        unit: Unit of measurement for the quantity.
        product_data: Product information for shopping.
    
    Notes:
        Immutable. Equality by value (quantity, unit, product_data).
        Represents a single item on a shopping list.
    """

    quantity: float
    unit: str
    product_data: ProductShoppingData
