from attrs import frozen

from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject

@frozen(kw_only=True, hash=True)
class ProductShoppingData(ValueObject):

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

    quantity: float
    unit: str
    product_data: ProductShoppingData