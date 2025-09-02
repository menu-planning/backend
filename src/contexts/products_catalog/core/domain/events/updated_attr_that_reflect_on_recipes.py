"""Event emitted when product attributes change that affect recipes.

This event is triggered when product properties that impact recipe
calculations or shopping lists are modified.
"""
from attrs import field, frozen
from src.contexts.seedwork.domain.event import Event


@frozen(kw_only=True)
class UpdatedAttrOnProductThatReflectOnRecipeShoppingList(Event):
    """Event emitted when product attributes change that affect recipes.
    
    Attributes:
        product_id: Unique identifier of the product that was modified.
        message: Description of the changes made to the product.
    
    Notes:
        Emitted by: Product aggregate when recipe-affecting properties change.
        Ordering: none. Triggers recipe recalculation and shopping list updates.
    """
    product_id: str
    message: str = field(hash=False, default="")
