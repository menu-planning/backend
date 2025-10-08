from datetime import datetime
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject
from attrs import frozen

@frozen(kw_only=True, hash=True)
class _ShoppingItem(ValueObject):
    product_id: str
    shopping_name: str
    unit: str
    total_quantity: float
    meal_names: list[str]
    store_department_name: str | None = None
    recommended_brands_and_products: str | None = None
    substitutes: str | None = None

@frozen(kw_only=True, hash=True)
class ShoppingList(ValueObject):
    shopping_items: list[_ShoppingItem]
    created_at: datetime

