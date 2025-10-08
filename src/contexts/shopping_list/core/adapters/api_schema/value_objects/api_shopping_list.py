import operator
from typing import Any
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import DatetimeOptional
from pydantic import BaseModel

class ApiShoppingItem(BaseModel):
    shopping_name: str
    unit: str
    quantity: float
    meals_names: list[str] | None = None
    store_departament_name: str | None = None
    recommended_brands_and_products: str | None = None
    substitutes: str | None = None

class ApiShoppingList(BaseModel):
    shopping_items: list[ApiShoppingItem]
    order_by: str | None = None
    created_at: DatetimeOptional

    def model_post_init(self, __context: Any) -> None:
        self.order_by = self.order_by or 'store_departament_name'
        self.shopping_items = sorted(
            self.shopping_items,
            key=operator.attrgetter(
                self.order_by,
            ),
        )
