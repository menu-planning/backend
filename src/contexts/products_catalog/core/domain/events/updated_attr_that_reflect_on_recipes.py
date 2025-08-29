from attrs import field, frozen

from src.contexts.seedwork.shared.domain.event import Event


@frozen(kw_only=True)
class UpdatedAttrOnProductThatReflectOnRecipeShoppingList(Event):
    product_id: str
    message: str = field(hash=False, default="")
