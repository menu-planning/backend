from pydantic import BaseModel, Field, field_serializer

from src.contexts.food_tracker.shared.adapters.api_schemas.value_objects.receipt import (
    ApiReceipt,
)
from src.contexts.food_tracker.shared.domain.entities.house import House


class ApiHouse(BaseModel):
    id: str
    owner_id: str
    name: str
    members_ids: set[str]
    nutritionists_ids: set[str]
    pending_receipts: set[ApiReceipt] = Field(default_factory=set)
    added_receipts: set[ApiReceipt] = Field(default_factory=set)
    discarded: bool = False
    version: int = 1

    @field_serializer("pending_receipts")
    def serialize_pending_receipts(self, pending_receipts: set[str], _info):
        return list(pending_receipts)

    @field_serializer("added_receipts")
    def serialize_added_receipts(self, added_receipts: set[str], _info):
        return list(added_receipts)

    @classmethod
    def from_domain(cls, house: House) -> "ApiHouse":
        return cls(
            id=house.id,
            owner_id=house.owner_id,
            name=house.name,
            members_ids=house.members_ids,
            nutritionists_ids=house.nutritionists_ids,
            pending_receipts=(
                set([ApiReceipt.from_domain(r) for r in house.pending_receipts])
                if house.pending_receipts
                else set()
            ),
            added_receipts=(
                set([ApiReceipt.from_domain(r) for r in house.added_receipts])
                if house.added_receipts
                else set()
            ),
            discarded=house.discarded,
            version=house.version,
        )

    def to_domain(self) -> House:
        return House(
            id=self.id,
            owner_id=self.owner_id,
            name=self.name,
            members_ids=self.members_ids,
            nutritionists_ids=self.nutritionists_ids,
            pending_receipts=(
                set([r.to_domain() for r in self.pending_receipts])
                if self.pending_receipts
                else None
            ),
            added_receipts=(
                set([r.to_domain() for r in self.added_receipts])
                if self.added_receipts
                else None
            ),
            discarded=self.discarded,
            version=self.version,
        )
