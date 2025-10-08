"""Business rules used across the recipes catalog domain."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.seedwork.domain.rules import BusinessRule

if TYPE_CHECKING:
    from src.contexts.shopping_list.core.domain.root_aggregate.client import Client

class MaxNumberOfShoppingLists(BusinessRule):
    """Validate that a client has a maximum number of shopping lists.

    Args:
        client: Client to validate shopping lists for.
    """
    __message = "Client has a maximum number of shopping lists"

    def __init__(self, client: Client):
        self.client = client

    def is_broken(self) -> bool:
        if len(self.client.shopping_list) > 10:
            return True
        return False

    def get_message(self) -> str:
        return self.__message