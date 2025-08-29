from src.contexts.products_catalog.core.domain.events.classification import (
    ClassificationCreated,
)
from src.contexts.products_catalog.core.domain.events.food_product_created import (
    FoodProductCreated,
)
from src.contexts.products_catalog.core.domain.events.updated_attr_that_reflect_on_recipes import (
    UpdatedAttrOnProductThatReflectOnRecipeShoppingList,
)

__all__ = [
    "ClassificationCreated",
    "FoodProductCreated",
    "UpdatedAttrOnProductThatReflectOnRecipeShoppingList",
]
