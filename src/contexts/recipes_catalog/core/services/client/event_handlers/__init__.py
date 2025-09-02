from src.contexts.recipes_catalog.core.services.client.event_handlers.menu_deleted_handler import (
    delete_related_meals,
)
from src.contexts.recipes_catalog.core.services.client.event_handlers.menu_meals_changed_handler import (
    update_menu_id_on_meals,
)

__all__ = [
    "delete_related_meals",
    "update_menu_id_on_meals",
]
