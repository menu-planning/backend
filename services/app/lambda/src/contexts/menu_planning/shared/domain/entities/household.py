from datetime import datetime

from src.contexts.menu_planning.shared.domain.entities.client import _Client
from src.contexts.menu_planning.shared.domain.events.household_created import (
    HouseholdCreated,
)
from src.contexts.menu_planning.shared.domain.value_objects.address import Address
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event


class Household(Entity):
    def __init__(
        self,
        *,
        id: str,
        owner_id: str,
        name: str,
        address: Address | None = None,
        clients: list[_Client] | None = None,
        nutritionists_ids: list[str] | None = None,
        chefs_ids: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ):
        """Do not call directly to create a new Household."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._owner_id = owner_id
        self._name = name
        self._address = address
        self._clients = clients
        self._nutritionists_ids = nutritionists_ids
        self._chefs_ids = chefs_ids
        self._created_at = created_at
        self._updated_at = updated_at
        self.events: list[Event] = []

    @classmethod
    def create_house(
        cls,
        *,
        owner_id: str,
        name: str,
        address: Address | None = None,
    ) -> "Household":
        event = HouseholdCreated(
            owner_id=owner_id,
            name=name,
        )
        house = cls(
            id=event.house_id,
            owner_id=owner_id,
            name=event.name,
            address=address,
        )
        house.events.append(event)
        return house
