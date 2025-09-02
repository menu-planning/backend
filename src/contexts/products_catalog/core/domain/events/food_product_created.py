import uuid

from attrs import field, frozen
from src.contexts.seedwork.domain.event import Event


@frozen
class FoodProductCreated(Event):
    """Event emitted when a new food product is created in the catalog.
    
    Attributes:
        data_source: Source system that provided the product data.
        barcode: Product barcode if available.
        product_id: Unique identifier for the product (UUID v4 hex).
    
    Notes:
        Emitted by: Product aggregate creation methods. Ordering: none.
        Triggers downstream processes: image scraping and admin notifications.
    """
    data_source: str
    barcode: str | None = None
    product_id: str = field(factory=lambda: uuid.uuid4().hex)
