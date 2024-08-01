from pydantic import UUID4, BaseModel
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
    pending_receipts: set[ApiReceipt]
    added_receipts: set[ApiReceipt]
    discarded: bool = False
    version: int = 1

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
